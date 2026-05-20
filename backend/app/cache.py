"""Lightweight cache with Redis backend and in-process fallback."""
from __future__ import annotations

import json
import time
from threading import Lock
from typing import Any

import redis

from .config import get_settings


_local_store: dict[str, tuple[float, str]] = {}
_local_lock = Lock()
_redis: redis.Redis | None = None
_redis_dead_until: float = 0.0


def _client() -> redis.Redis | None:
    global _redis, _redis_dead_until
    if _redis is not None and time.time() > _redis_dead_until:
        return _redis
    if time.time() < _redis_dead_until:
        return None
    try:
        _redis = redis.from_url(get_settings().redis_url, socket_connect_timeout=1, socket_timeout=1)
        _redis.ping()
        return _redis
    except Exception:
        _redis = None
        _redis_dead_until = time.time() + 30
        return None


def cache_get(key: str) -> Any | None:
    client = _client()
    if client is not None:
        try:
            raw = client.get(key)
            if raw is not None:
                return json.loads(raw)
        except Exception:
            pass
    with _local_lock:
        item = _local_store.get(key)
        if item is None:
            return None
        expires_at, raw = item
        if expires_at < time.time():
            _local_store.pop(key, None)
            return None
        return json.loads(raw)


def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    payload = json.dumps(value, default=str)
    client = _client()
    if client is not None:
        try:
            client.set(key, payload, ex=ttl_seconds)
        except Exception:
            pass
    with _local_lock:
        _local_store[key] = (time.time() + ttl_seconds, payload)


def cache_clear() -> None:
    client = _client()
    if client is not None:
        try:
            client.flushdb()
        except Exception:
            pass
    with _local_lock:
        _local_store.clear()
