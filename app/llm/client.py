from __future__ import annotations

from abc import ABC, abstractmethod
import logging

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    """Raised when the configured local LLM cannot serve a request."""


class LLMClient(ABC):
    @abstractmethod
    def generate_structured_query(self, system_prompt: str, question: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        raise NotImplementedError


class OllamaClient(LLMClient):
    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url
        self._model = settings.ollama_model
        self._timeout = settings.llm_timeout_seconds

    def is_available(self) -> bool:
        try:
            with httpx.Client(timeout=min(self._timeout, 2.0)) as client:
                response = client.get(f"{self._base_url}/api/tags")
                return response.is_success
        except httpx.HTTPError:
            return False

    def generate_structured_query(self, system_prompt: str, question: str) -> dict:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(f"{self._base_url}/api/generate", json={
                    "model": self._model,
                    "system": system_prompt,
                    "prompt": question,
                    # JSON mode keeps small local models reliable; Pydantic and allowlists
                    # remain the security boundary before any deterministic data operation.
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0},
                })
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("llm_request_failed provider=ollama error_type=%s", type(exc).__name__)
            raise LLMUnavailableError("Configured Ollama service is unavailable") from exc
        import json
        try:
            return json.loads(body["response"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise LLMUnavailableError("Ollama returned malformed structured output") from exc


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "ollama":
        return OllamaClient(settings)
    raise ValueError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
