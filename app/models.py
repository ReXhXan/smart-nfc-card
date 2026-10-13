"""Pydantic schemas for cards and API payloads."""
import re

from pydantic import BaseModel, Field, field_validator

SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{1,38}[a-z0-9])$")


class CardIn(BaseModel):
    slug: str = Field(..., description="Public handle, used in the card URL")
    full_name: str = Field(..., min_length=1, max_length=120)
    title: str = ""
    company: str = ""
    email: str = ""
    phone: str = ""
    website: str = ""
    location: str = ""
    skills: list[str] = []
    highlights: list[str] = Field(default_factory=list, description="Projects, achievements, experience")
    bio: str = ""
    links: dict[str, str] = {}

    @field_validator("slug")
    @classmethod
    def _slug(cls, v: str) -> str:
        v = v.strip().lower()
        if not SLUG_RE.match(v):
            raise ValueError("slug must be 3-40 chars of a-z, 0-9 and '-'")
        return v


class Card(CardIn):
    taps: int = 0


class BioRequest(BaseModel):
    tone: str = "professional"
    max_words: int = Field(60, ge=15, le=200)
    save: bool = True


class BioResponse(BaseModel):
    bio: str
    pitch: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class AskResponse(BaseModel):
    answer: str
