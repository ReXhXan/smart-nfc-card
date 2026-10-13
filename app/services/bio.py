"""LLM-generated bio and 1-line elevator pitch from the card owner's details."""
from ..llm import LLM
from ..models import CardIn
from .profile import facts

BIO_SYSTEM = (
    "You write concise, first-person professional bios for digital business cards. "
    "Use ONLY facts from the PROFILE. Never invent employers, numbers or awards."
)
PITCH_SYSTEM = "Write a single-sentence elevator pitch (max 25 words) using ONLY the PROFILE facts."


def _profile_block(card: CardIn) -> str:
    return "PROFILE:\n" + "\n".join(f"- {f}" for f in facts(card))


def generate_bio(llm: LLM, card: CardIn, tone: str = "professional", max_words: int = 60) -> str:
    prompt = f"Tone: {tone}. Max {max_words} words.\n\n{_profile_block(card)}"
    words = llm.generate(BIO_SYSTEM, prompt).split()
    return " ".join(words[:max_words])


def generate_pitch(llm: LLM, card: CardIn) -> str:
    return llm.generate(PITCH_SYSTEM, _profile_block(card))
