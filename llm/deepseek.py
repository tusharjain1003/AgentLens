"""
DeepSeek V3 via OpenAI-compatible API.
Model: deepseek-chat (= DeepSeek V3) — no daily quota, excellent reasoning.
"""
from __future__ import annotations

import logging
from typing import AsyncIterator
from openai import AsyncOpenAI
from config import settings
from .base import BaseLLMClient
from pipeline.token_tracker import get_tracker

logger = logging.getLogger(__name__)

_MODEL = "deepseek-chat"
_BASE_URL = "https://api.deepseek.com"


def _estimate_tokens(messages: list[dict], completion: str = "") -> tuple[int, int]:
    prompt_chars = sum(len(m.get("content") or "") for m in messages)
    return max(1, prompt_chars // 4), max(1, len(completion) // 4)


def _record_usage(model: str, prompt_tokens: int, completion_tokens: int) -> None:
    try:
        from pipeline.runtime import get_runtime

        tracker = get_runtime().token_tracker
    except Exception:
        tracker = get_tracker()
    tracker.record(model, int(prompt_tokens or 0), int(completion_tokens or 0))


def _usage_tokens(usage) -> tuple[int, int] | None:
    if not usage:
        return None
    prompt = getattr(usage, "prompt_tokens", None)
    completion = getattr(usage, "completion_tokens", None)
    if prompt is None and isinstance(usage, dict):
        prompt = usage.get("prompt_tokens")
        completion = usage.get("completion_tokens")
    if prompt is None or completion is None:
        return None
    return int(prompt), int(completion)


class DeepSeekClient(BaseLLMClient):
    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=_BASE_URL,
        )

    async def astream(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        stream = await self._client.chat.completions.create(
            model=_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            stream=True,
            stream_options={"include_usage": True},
        )
        collected: list[str] = []
        usage = None
        async for chunk in stream:
            usage = getattr(chunk, "usage", None) or usage
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                collected.append(delta.content)
                yield delta.content
        tokens = _usage_tokens(usage)
        if tokens is None:
            tokens = _estimate_tokens(messages, "".join(collected))
        _record_usage(_MODEL, tokens[0], tokens[1])

    async def acomplete(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 2048,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = await self._client.chat.completions.create(
            model=_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            stream=False,
        )
        text = resp.choices[0].message.content or ""
        tokens = _usage_tokens(getattr(resp, "usage", None))
        if tokens is None:
            tokens = _estimate_tokens(messages, text)
        _record_usage(_MODEL, tokens[0], tokens[1])
        return text
