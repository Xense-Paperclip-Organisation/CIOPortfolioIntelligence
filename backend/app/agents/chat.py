"""Ask-the-CIO chat (BRD §4.12).

The full portfolio context is preloaded into a cached system prompt so each
follow-up question only sends the latest user turn — keeps cost down and
latency stable.
"""
from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic

from . import client as ai
from ..config import get_settings


SYSTEM_TEMPLATE = (
    "You are the Chief Investment Officer of Emirates NBD Wealth, speaking with one client.\n"
    "You know this client's portfolio in detail (provided below).\n"
    "Voice: advisory-grade, concrete, calm. Cite holdings by ticker when relevant.\n"
    "Hard rules:\n"
    "  * Only reference securities that actually exist in the supplied holdings.\n"
    "  * Never cite a number you can't justify from the supplied state.\n"
    "  * If a question is outside your remit (execution, taxes, legal), redirect.\n"
    "  * Be concise. 3-5 sentences unless the client asks for depth.\n"
    "Client portfolio state:\n"
    "{portfolio_context}\n"
)


def respond(history: list[dict[str, str]], portfolio_context: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    system_text = SYSTEM_TEMPLATE.format(portfolio_context=json.dumps(portfolio_context, default=str))

    if not settings.anthropic_api_key:
        # Deterministic offline response so the chat surface is testable in demos
        last = history[-1]["content"] if history else ""
        keywords = last.lower()
        if "risk" in keywords or "drawdown" in keywords:
            answer = (
                "Your current portfolio beta is elevated relative to a Balanced profile, primarily "
                "driven by NVDA, TSLA and the broader US-tech cluster. A 20% drawdown in that sleeve "
                "would draw the book down materially. Our advisory card recommends trimming NVDA and "
                "TSLA and building the GCC sukuk sleeve."
            )
        elif "rebalance" in keywords or "trim" in keywords:
            answer = (
                "Three immediate moves: trim NVDA from ~16% to 8%, trim TSLA from ~12% to 5%, and "
                "deploy excess cash into a laddered GCC sukuk + short-duration USD treasury sleeve. "
                "That brings you closer to the 50/30/5 Balanced model."
            )
        else:
            answer = (
                "Chat is running in offline mode (ANTHROPIC_API_KEY not set). Live prices and risk "
                "metrics in the dashboard are still current; for AI-generated advisory voice, configure "
                "the key and reload."
            )
        return {"role": "assistant", "content": answer, "degraded": True}

    client: Anthropic = ai._client()
    try:
        message = client.messages.create(
            model=settings.claude_chat_model,
            max_tokens=900,
            temperature=0.3,
            system=[{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": m["role"], "content": m["content"]} for m in history],
        )
    except Exception as exc:
        return {"role": "assistant", "content": f"Chat error: {exc}", "degraded": True}
    text = "".join(b.text for b in message.content if getattr(b, "type", "") == "text").strip()
    return {"role": "assistant", "content": text}
