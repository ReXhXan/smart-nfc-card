"""Pluggable LLM clients. OpenAI and Groq share the OpenAI-compatible API; Ollama runs locally."""
import httpx


class LLM:
    def generate(self, system: str, prompt: str) -> str:
        raise NotImplementedError


class OpenAICompatibleLLM(LLM):
    def __init__(self, model: str, api_key: str, base_url: str | None = None):
        from openai import OpenAI
        self.client, self.model = OpenAI(api_key=api_key, base_url=base_url), model

    def generate(self, system, prompt):
        r = self.client.chat.completions.create(
            model=self.model, temperature=0.4,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        )
        return (r.choices[0].message.content or "").strip()


class OllamaLLM(LLM):
    def __init__(self, model: str, base_url: str):
        self.model, self.url = model, base_url.rstrip("/") + "/api/chat"

    def generate(self, system, prompt):
        r = httpx.post(self.url, timeout=120, json={
            "model": self.model, "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        })
        r.raise_for_status()
        return r.json()["message"]["content"].strip()


class MockLLM(LLM):
    """Deterministic offline stand-in: returns the first line of the CONTEXT/PROFILE block."""

    def generate(self, system, prompt):
        for marker in ("CONTEXT:\n", "PROFILE:\n"):
            if marker in prompt:
                body = prompt.split(marker, 1)[1].strip().splitlines()
                return body[0].lstrip("- ").strip() if body else "I don't know."
        return "I don't know."


def get_llm(settings) -> LLM:
    p = settings.llm_provider.lower()
    if p == "openai":
        return OpenAICompatibleLLM(settings.llm_model, settings.openai_api_key)
    if p == "groq":
        return OpenAICompatibleLLM(settings.llm_model, settings.groq_api_key,
                                   base_url="https://api.groq.com/openai/v1")
    if p == "ollama":
        return OllamaLLM(settings.llm_model, settings.ollama_base_url)
    return MockLLM()
