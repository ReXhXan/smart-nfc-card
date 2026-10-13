import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import Store
from app.llm import MockLLM
from app.main import create_app

SAMPLE = {
    "slug": "rehan", "full_name": "Rehan Khan", "title": "AI/ML Engineer", "company": "Acme Labs",
    "email": "rehan@example.com", "phone": "+91 90000 00000", "location": "Bengaluru",
    "skills": ["Python", "LangChain", "FastAPI"],
    "highlights": ["Built a production-style RAG system for chatting with documents"],
    "links": {"github": "https://github.com/ReXhXan"},
}


@pytest.fixture
def sample():
    return dict(SAMPLE)


@pytest.fixture
def client():
    s = Settings(llm_provider="mock", database_path=":memory:", public_base_url="https://cards.test")
    app = create_app(s, llm=MockLLM(), store=Store(":memory:"))
    return TestClient(app)
