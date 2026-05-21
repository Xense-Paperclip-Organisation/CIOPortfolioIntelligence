"""Structured JSON logging + request-ID contextvar."""
from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ctx: dict[str, Any] = getattr(record, "ctx", {})
        payload = {
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)
            ),
            "level": record.levelname,
            "request_id": request_id_var.get("-"),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if ctx:
            payload["context"] = ctx
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_ctx(logger: logging.Logger, level: int, msg: str, **ctx: Any) -> None:
    """Emit a structured log record with extra context dict."""
    logger.log(level, msg, extra={"ctx": ctx})
