"""FastAPI app: card CRUD, public card page, AI bio/chat, vCard and tap analytics."""
import html
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response

from .config import Settings, get_settings
from .db import Store
from .llm import LLM, get_llm
from .logging_config import setup_logging
from .models import AskRequest, AskResponse, BioRequest, BioResponse, Card, CardIn
from .services import analytics, bio, chat, vcard

STATIC = Path(__file__).parent / "static"
VALID_SOURCES = {"nfc", "qr", "link"}


def create_app(settings: Settings | None = None, llm: LLM | None = None, store: Store | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)
    app = FastAPI(title="Smart NFC Card", version="1.0.0")
    app.state.settings = settings
    app.state.llm = llm or get_llm(settings)
    app.state.store = store or Store(settings.database_path)

    def S() -> Store:
        return app.state.store

    def card_or_404(slug: str, store: Store = Depends(S)) -> Card:
        card = store.get(slug.lower())
        if not card:
            raise HTTPException(404, "card not found")
        return card

    def card_url(slug: str) -> str:
        return f"{settings.public_base_url.rstrip('/')}/c/{slug}"

    @app.get("/health")
    def health():
        return {"status": "ok", "llm": settings.llm_provider}

    @app.get("/", response_class=HTMLResponse)
    def editor():
        return FileResponse(STATIC / "editor.html")

    @app.post("/api/cards", status_code=201)
    def create(card: CardIn, store: Store = Depends(S)):
        store.upsert(card)
        return {"slug": card.slug, "url": card_url(card.slug)}

    @app.get("/api/cards/{slug}", response_model=Card)
    def read(card: Card = Depends(card_or_404)):
        return card

    @app.delete("/api/cards/{slug}", status_code=204)
    def delete(slug: str, store: Store = Depends(S)):
        if not store.delete(slug.lower()):
            raise HTTPException(404, "card not found")
        return Response(status_code=204)

    @app.post("/api/cards/{slug}/bio", response_model=BioResponse)
    def make_bio(req: BioRequest, card: Card = Depends(card_or_404), store: Store = Depends(S)):
        new_bio = bio.generate_bio(app.state.llm, card, req.tone, req.max_words)
        pitch = bio.generate_pitch(app.state.llm, card)
        if req.save:
            store.upsert(CardIn(**card.model_dump(exclude={"taps"}) | {"bio": new_bio}))
        return BioResponse(bio=new_bio, pitch=pitch)

    @app.post("/api/cards/{slug}/ask", response_model=AskResponse)
    def ask(req: AskRequest, card: Card = Depends(card_or_404)):
        return AskResponse(answer=chat.answer(app.state.llm, card, req.question))

    @app.get("/api/cards/{slug}/vcard")
    def download_vcard(card: Card = Depends(card_or_404)):
        return Response(
            vcard.to_vcard(card, card_url(card.slug)), media_type="text/vcard",
            headers={"Content-Disposition": f'attachment; filename="{card.slug}.vcf"'},
        )

    @app.get("/api/cards/{slug}/analytics")
    def stats(card: Card = Depends(card_or_404), store: Store = Depends(S)):
        return analytics.summarize(store.tap_rows(card.slug))

    @app.get("/c/{slug}", response_class=HTMLResponse)
    def public_card(request: Request, src: str = "link", card: Card = Depends(card_or_404),
                    store: Store = Depends(S)):
        """The URL written to the NFC tag. Every visit is logged as a tap."""
        store.record_tap(card.slug, src if src in VALID_SOURCES else "link",
                         request.headers.get("user-agent", ""), request.headers.get("referer", ""))
        page = (STATIC / "card.html").read_text(encoding="utf-8")
        return page.replace("{{SLUG}}", html.escape(card.slug)).replace("{{NAME}}", html.escape(card.full_name))

    return app


app = create_app()
