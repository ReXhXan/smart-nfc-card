"""vCard 3.0 export (RFC 2426) so visitors can save the contact in one tap."""
from ..models import CardIn


def _esc(v: str) -> str:
    return v.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def to_vcard(card: CardIn, card_url: str) -> str:
    parts = card.full_name.rsplit(" ", 1)
    last, first = (parts[1], parts[0]) if len(parts) == 2 else (parts[0], "")
    lines = ["BEGIN:VCARD", "VERSION:3.0", f"N:{_esc(last)};{_esc(first)};;;", f"FN:{_esc(card.full_name)}"]
    if card.title:
        lines.append(f"TITLE:{_esc(card.title)}")
    if card.company:
        lines.append(f"ORG:{_esc(card.company)}")
    if card.email:
        lines.append(f"EMAIL;TYPE=INTERNET:{card.email}")
    if card.phone:
        lines.append(f"TEL;TYPE=CELL:{card.phone}")
    if card.website:
        lines.append(f"URL:{card.website}")
    for url in card.links.values():
        lines.append(f"URL:{url}")
    if card.bio:
        lines.append(f"NOTE:{_esc(card.bio)}")
    lines += [f"SOURCE:{card_url}", "END:VCARD"]
    return "\r\n".join(lines) + "\r\n"
