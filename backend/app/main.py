"""FastAPI entry point."""
from __future__ import annotations

import uuid

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .logging_config import configure_logging, log_ctx, request_id_var

configure_logging()

import logging
log = logging.getLogger("cio.backend")

app = FastAPI(
    title="CIO Portfolio Intelligence — POC",
    description="Portfolio-aware advisory dashboard backend (BRD: WEALTH-POC-CIO-001).",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next) -> Response:
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_var.set(rid)
    try:
        response = await call_next(request)
    finally:
        request_id_var.reset(token)
    response.headers["X-Request-ID"] = rid
    return response


app.include_router(router)


@app.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}


@app.on_event("startup")
async def on_startup() -> None:
    log_ctx(log, logging.INFO, "backend ready — POC FastAPI service started")
