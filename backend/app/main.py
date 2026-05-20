"""FastAPI entry point."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
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

app.include_router(router)


@app.get("/healthz")
def healthz() -> dict[str, bool]:
    return {"ok": True}


@app.on_event("startup")
async def on_startup() -> None:
    log.info("backend ready — POC FastAPI service started")
