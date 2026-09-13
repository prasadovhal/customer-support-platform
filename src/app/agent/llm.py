from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

import httpx
from loguru import logger

from app.core.config import get_settings


@runtime_checkable
class LLMClient(Protocol):
    """Protocol for LLM clients — sync or async chat completion."""

    async def chat(
        self,
        messages: list[dict[str, str]],
        system: Optional[str] = None,
    ) -> str: ...


class OllamaClient:
    """Async Ollama client using direct HTTP (avoids SDK version variance).

    Calls POST /api/chat on the Ollama server and returns the assistant text.
    Raises httpx.HTTPError on network failure; caller should handle gracefully.
    """

    def __init__(self) -> None:
        self._cfg = get_settings()

    async def chat(
        self,
        messages: list[dict[str, str]],
        system: Optional[str] = None,
    ) -> str:
        all_messages: list[dict[str, str]] = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        payload = {
            "model": self._cfg.OLLAMA_MODEL,
            "messages": all_messages,
            "stream": False,
        }

        async with httpx.AsyncClient(
            base_url=self._cfg.OLLAMA_BASE_URL,
            timeout=float(self._cfg.OLLAMA_TIMEOUT),
        ) as client:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
            content: str = data["message"]["content"]
            logger.debug(f"Ollama response ({len(content)} chars)")
            return content
