"""News service: public RSS feeds via feedparser.

Per the BRD (§5) we deliberately use *only* free, open RSS — no paywall content.
The feed list mixes global financial media with MENA outlets so we have
relevant material for both Ahmed's US-tech-heavy book and his MENA names.
"""
from __future__ import annotations

import hashlib
import logging
import re
import time
from datetime import datetime
from typing import Any

import feedparser

from ..cache import cache_get, cache_set
from ..config import get_settings

log = logging.getLogger("services.news")


RSS_FEEDS: list[dict[str, str]] = [
    {"source": "Reuters Business", "url": "https://www.reutersagency.com/feed/?best-topics=business-finance&post_type=best"},
    {"source": "Reuters Markets", "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"source": "FT Markets", "url": "https://www.ft.com/markets?format=rss"},
    {"source": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss"},
    {"source": "Investing.com Stock Market", "url": "https://www.investing.com/rss/news_25.rss"},
    {"source": "Investing.com Forex", "url": "https://www.investing.com/rss/news_1.rss"},
    {"source": "Investing.com Commodities", "url": "https://www.investing.com/rss/news_11.rss"},
    {"source": "Khaleej Times Business", "url": "https://www.khaleejtimes.com/rss/business"},
    {"source": "Arabian Business", "url": "https://www.arabianbusiness.com/rss/articles"},
    {"source": "Gulf News Business", "url": "https://gulfnews.com/rss?xml=business"},
    {"source": "CNBC Top News", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    {"source": "MarketWatch Top", "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories"},
]


_KEYWORD_BOOST = {
    "AAPL": ["apple", "iphone", "tim cook"],
    "NVDA": ["nvidia", "jensen", "ai chip", "gpu"],
    "TSLA": ["tesla", "musk", "ev", "cybertruck"],
    "MSFT": ["microsoft", "azure", "satya", "copilot"],
    "META": ["meta", "facebook", "instagram", "zuckerberg"],
    "EMAAR.DU": ["emaar", "dubai property", "uae real estate", "dfm"],
    "2222.SR": ["aramco", "saudi oil", "tadawul", "opec"],
    "GLD": ["gold", "bullion", "safe haven", "precious metals"],
    "KSA-SUKUK-5.6-2030": ["sukuk", "saudi bond", "gcc yields", "sovereign debt"],
}


def _normalize_entry(entry: Any, source: str) -> dict[str, Any] | None:
    title = (entry.get("title") or "").strip()
    link = (entry.get("link") or "").strip()
    if not title or not link:
        return None
    summary = re.sub(r"<[^>]+>", "", entry.get("summary") or "").strip()
    published = entry.get("published") or entry.get("updated") or ""
    try:
        ts = feedparser._parse_date(published) if published else None
        published_iso = datetime(*ts[:6]).isoformat() if ts else None
    except Exception:
        published_iso = None
    article_id = hashlib.sha1(link.encode("utf-8")).hexdigest()[:16]
    return {
        "id": article_id,
        "title": title,
        "summary": summary[:600],
        "link": link,
        "published": published_iso,
        "source": source,
    }


def _score(article: dict[str, Any], holdings: list[dict[str, Any]]) -> tuple[float, list[str]]:
    """Score article relevance to the user's holdings. Returns (score, matched_tickers)."""
    text = f"{article.get('title','')} {article.get('summary','')}".lower()
    score = 0.0
    matched: list[str] = []
    for h in holdings:
        ticker = h["ticker"]
        kws = _KEYWORD_BOOST.get(ticker, [])
        name = h.get("name", "").lower()
        if ticker.lower() in text or any(k in text for k in kws) or (name and name in text):
            score += 3.0 + h.get("weight_target_pct", 0) / 5.0
            matched.append(ticker)
    if "market" in text or "stocks" in text:
        score += 0.5
    if "uae" in text or "saudi" in text or "gulf" in text:
        score += 0.3
    return score, matched


def fetch_articles(holdings: list[dict[str, Any]], limit: int = 18) -> list[dict[str, Any]]:
    """Pull and rank live articles for the supplied holdings book.

    Ranks by holding-overlap score so the top articles will name actual
    securities. Cached for the configured TTL.
    """
    cache_key = "news:articles:v3"
    cached = cache_get(cache_key)
    if cached is not None:
        articles = cached
    else:
        articles = []
        for feed in RSS_FEEDS:
            try:
                parsed = feedparser.parse(feed["url"])
                for entry in parsed.entries[:25]:
                    norm = _normalize_entry(entry, feed["source"])
                    if norm:
                        articles.append(norm)
            except Exception as exc:
                log.warning("RSS feed failed %s: %s", feed.get("url"), exc)
        # Dedupe by id
        seen = set()
        unique: list[dict[str, Any]] = []
        for a in articles:
            if a["id"] in seen:
                continue
            seen.add(a["id"])
            unique.append(a)
        articles = unique
        cache_set(cache_key, articles, ttl_seconds=get_settings().news_cache_ttl_seconds)

    ranked: list[tuple[float, dict[str, Any]]] = []
    for art in articles:
        score, matched = _score(art, holdings)
        art2 = {**art, "matched_tickers": matched, "score": score}
        ranked.append((score, art2))
    ranked.sort(key=lambda x: (x[0], x[1].get("published") or ""), reverse=True)

    top = [a for _, a in ranked if a["score"] > 0]
    if len(top) < limit:
        # Backfill with high-quality general articles so the feed isn't empty
        # when feeds are quiet on a holding-specific day.
        backfill = [a for _, a in ranked if a["score"] == 0][: limit - len(top)]
        top.extend(backfill)
    return top[:limit]


def fetch_for_ticker(ticker: str, limit: int = 6) -> list[dict[str, Any]]:
    """Filter the live article pool to a single ticker, with at least
    `limit` items by falling back to keyword matches."""
    pseudo_holdings = [{"ticker": ticker, "name": ticker, "weight_target_pct": 10}]
    return fetch_articles(pseudo_holdings, limit=limit * 2)[:limit]


def freshness() -> dict[str, Any]:
    return {"feeds": RSS_FEEDS, "fetched_at": int(time.time())}
