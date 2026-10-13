"""Turn a card into plain-text facts that prompts and retrieval can use."""
import re

from ..models import CardIn

_WORD = re.compile(r"[a-z0-9+#.]+")
_STOP = {"the", "a", "an", "is", "are", "what", "does", "do", "of", "to", "in", "and", "or",
         "he", "she", "they", "his", "her", "their", "you", "your", "me", "about", "for", "with", "on"}


def facts(card: CardIn) -> list[str]:
    out = [f"{card.full_name} is {card.title or 'a professional'}"
           + (f" at {card.company}" if card.company else "") + "."]
    if card.location:
        out.append(f"{card.full_name} is based in {card.location}.")
    if card.skills:
        out.append(f"Skills: {', '.join(card.skills)}.")
    out += [f"Highlight: {h}" for h in card.highlights]
    if card.bio:
        out.append(f"Bio: {card.bio}")
    contact = [f"email {card.email}" if card.email else "", f"phone {card.phone}" if card.phone else "",
               f"website {card.website}" if card.website else ""]
    contact += [f"{k} {v}" for k, v in card.links.items()]
    contact = [c for c in contact if c]
    if contact:
        out.append(f"Contact: {', '.join(contact)}.")
    return out


def tokens(text: str) -> set[str]:
    return {t.strip(".") for t in _WORD.findall(text.lower())} - _STOP - {""}


def rank_facts(question: str, items: list[str], k: int = 4) -> list[str]:
    """Lightweight IDF-weighted lexical retrieval: profiles are tiny, so no vector DB is needed.

    Terms that occur in many facts (like the owner's name) count for less than rare ones.
    """
    import math

    q = tokens(question)
    toks = [tokens(f) for f in items]
    df = {t: sum(t in ft for ft in toks) for t in q}
    score = lambda ft: sum(math.log(1 + len(items) / df[t]) for t in q & ft)
    scored = sorted(((score(ft), i, f) for i, (ft, f) in enumerate(zip(toks, items))), key=lambda x: (-x[0], x[1]))
    hits = [f for s, _, f in scored if s > 0][:k]
    return hits or items[:k]
