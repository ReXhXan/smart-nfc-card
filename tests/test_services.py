from app.llm import LLM, MockLLM
from app.models import CardIn
from app.services import analytics, bio, chat, vcard
from app.services.profile import facts, rank_facts


class SpyLLM(LLM):
    def __init__(self, reply="ok"):
        self.reply, self.calls = reply, []

    def generate(self, system, prompt):
        self.calls.append((system, prompt))
        return self.reply


def test_facts_cover_profile(sample):
    f = "\n".join(facts(CardIn(**sample)))
    assert "AI/ML Engineer at Acme Labs" in f and "LangChain" in f and "rehan@example.com" in f


def test_rank_facts_prefers_overlap(sample):
    top = rank_facts("Which skills does Rehan have?", facts(CardIn(**sample)), k=1)
    assert top[0].startswith("Skills:")


def test_bio_prompt_grounded_and_truncated(sample):
    spy = SpyLLM("word " * 500)
    out = bio.generate_bio(spy, CardIn(**sample), max_words=20)
    assert len(out.split()) == 20
    system, prompt = spy.calls[0]
    assert "ONLY" in system and "PROFILE:" in prompt and "Acme Labs" in prompt


def test_chat_uses_relevant_context(sample):
    spy = SpyLLM("answer")
    chat.answer(spy, CardIn(**sample), "Where is he based?")
    prompt = spy.calls[0][1]
    assert "Bengaluru" in prompt.split("QUESTION:")[0]


def test_mock_llm_is_deterministic(sample):
    assert chat.answer(MockLLM(), CardIn(**sample), "location?") == chat.answer(
        MockLLM(), CardIn(**sample), "location?")


def test_vcard_format(sample):
    v = vcard.to_vcard(CardIn(**sample | {"bio": "Hi; I build, things"}), "https://cards.test/c/rehan")
    assert v.startswith("BEGIN:VCARD\r\nVERSION:3.0\r\n") and v.endswith("END:VCARD\r\n")
    assert "N:Khan;Rehan;;;" in v and "TEL;TYPE=CELL:+91 90000 00000" in v
    assert "NOTE:Hi\\; I build\\, things" in v


def test_analytics_summary():
    rows = [{"ts": "2026-10-12T10:00:00+00:00", "source": "nfc", "user_agent": "Mozilla (iPhone)"},
            {"ts": "2026-10-13T09:00:00+00:00", "source": "qr", "user_agent": "Android 14"},
            {"ts": "2026-10-13T11:00:00+00:00", "source": "nfc", "user_agent": ""}]
    s = analytics.summarize(rows)
    assert s["total"] == 3 and s["by_source"] == {"nfc": 2, "qr": 1}
    assert s["by_device"] == {"ios": 1, "android": 1, "unknown": 1}
    assert s["by_day"] == {"2026-10-12": 1, "2026-10-13": 2}
