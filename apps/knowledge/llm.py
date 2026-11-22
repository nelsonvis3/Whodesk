"""Proveedores de LLM. El resto del sistema solo conoce `generate(system, user) -> str`."""

import logging

import httpx
from django.conf import settings

log = logging.getLogger(__name__)


class ProviderError(Exception):
    pass


class NoProvider:
    """Sin LLM: el asistente responde de forma extractiva (fragmentos de la base de conocimiento)."""

    name = "none"
    model = ""
    generative = False

    def generate(self, system: str, user: str) -> str:
        raise ProviderError("No hay proveedor de LLM configurado")


class AnthropicProvider:
    name = "anthropic"
    generative = True

    def __init__(self, api_key, model, timeout, max_tokens):
        self.api_key, self.model, self.timeout, self.max_tokens = api_key, model, timeout, max_tokens

    def generate(self, system: str, user: str) -> str:
        try:
            r = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": 0.2,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=self.timeout,
            )
            r.raise_for_status()
            blocks = r.json().get("content", [])
            text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise ProviderError(f"Fallo del proveedor anthropic: {exc.__class__.__name__}") from exc
        if not text:
            raise ProviderError("Respuesta vacía del proveedor")
        return text


class OpenAIProvider:
    """Cualquier API compatible con /chat/completions (OpenAI, Groq, OpenRouter, Gemini, etc.)."""

    name = "openai"
    generative = True

    def __init__(self, api_key, model, base_url, timeout, max_tokens):
        self.api_key, self.model, self.timeout, self.max_tokens = api_key, model, timeout, max_tokens
        self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")

    def generate(self, system: str, user: str) -> str:
        try:
            r = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": 0.2,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                },
                timeout=self.timeout,
            )
            r.raise_for_status()
            text = (r.json()["choices"][0]["message"]["content"] or "").strip()
        except (httpx.HTTPError, ValueError, KeyError, IndexError) as exc:
            raise ProviderError(f"Fallo del proveedor openai: {exc.__class__.__name__}") from exc
        if not text:
            raise ProviderError("Respuesta vacía del proveedor")
        return text


def get_provider():
    name = settings.LLM_PROVIDER
    if name == "none":
        return NoProvider()
    if not settings.LLM_API_KEY or not settings.LLM_MODEL:
        log.warning("LLM_PROVIDER=%s pero faltan LLM_API_KEY o LLM_MODEL: se usa modo extractivo", name)
        return NoProvider()
    if name == "anthropic":
        return AnthropicProvider(
            settings.LLM_API_KEY, settings.LLM_MODEL, settings.LLM_TIMEOUT, settings.LLM_MAX_TOKENS
        )
    return OpenAIProvider(
        settings.LLM_API_KEY,
        settings.LLM_MODEL,
        settings.LLM_BASE_URL,
        settings.LLM_TIMEOUT,
        settings.LLM_MAX_TOKENS,
    )
