"""Anthropic Claude client wrapper with prompt-caching + JSON-only output.

All in-app "agents" (Personalization, Advisory, Chart, Chat) share this entry
point so we can centralise: (1) prompt caching on the system block,
(2) JSON-mode coercion, (3) graceful degradation when ANTHROPIC_API_KEY is
absent so the dashboard still renders deterministic fallbacks for demos.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from anthropic import Anthropic

from ..config import get_settings

log = logging.getLogger("agents.client")

_CLIENT: Anthropic | None = None


def _client() -> Anthropic | None:
    global _CLIENT
    settings = get_settings()
    if not settings.anthropic_api_key:
        return None
    if _CLIENT is None:
        _CLIENT = Anthropic(api_key=settings.anthropic_api_key)
    return _CLIENT


def call_json(
    *,
    system: str,
    user: str,
    model: str | None = None,
    max_tokens: int = 1500,
    temperature: float = 0.2,
) -> dict[str, Any] | None:
    """Call Claude and return parsed JSON. Returns None on any failure so
    callers can fall back to deterministic stubs and the QA agent can mark
    the response degraded rather than silently fabricating data.

    Honours BRD §8 (structured JSON) and prompt-cache the system block.
    """
    settings = get_settings()
    client = _client()
    if client is None:
        return None
    try:
        message = client.messages.create(
            model=model or settings.claude_advisory_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=[
                {
                    "type": "text",
                    "text": system,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user}],
        )
    except Exception as exc:
        log.warning("Claude call failed (%s): %s", model, exc)
        return None

    raw = "".join(block.text for block in message.content if getattr(block, "type", "") == "text")
    raw = raw.strip()
    # Strip optional ```json fences
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
        if raw.endswith("```"):
            raw = raw[:-3].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Last-ditch: pull first {...} block out of the response
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass
    log.warning("Claude returned non-JSON: %.200s", raw)
    return None


def is_live() -> bool:
    return _client() is not None
