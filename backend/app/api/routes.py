"""FastAPI routes — single source of truth for the dashboard data contract."""
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response
from pydantic import BaseModel

from .. import profile as profile_mod
from ..agents import advisory as advisory_agent
from ..agents import chart as chart_agent
from ..agents import chat as chat_agent
from ..agents import client as ai_client
from ..agents import personalization as personalization_agent
from ..agents import pulse as pulse_agent
from ..agents import scenario as scenario_agent
from ..services import macro as macro_svc
from ..services import news as news_svc
from ..services import pdf as pdf_svc
from ..services import portfolio as portfolio_svc
from ..services import prices as prices_svc
from ..services import risk as risk_svc

router = APIRouter(prefix="/api")


# Profile ----------------------------------------------------------------
@router.get("/profile")
async def get_profile() -> dict[str, Any]:
    return profile_mod.get_profile()


# Portfolio --------------------------------------------------------------
async def _portfolio_bundle() -> dict[str, Any]:
    revalued = await run_in_threadpool(portfolio_svc.revalue_holdings)
    positions = revalued["positions"]
    allocation = portfolio_svc.allocation_breakdown(positions)
    target = profile_mod.BALANCED_TARGET
    alerts = portfolio_svc.alignment_alerts(positions, allocation, target)
    return {
        "revalued": revalued,
        "positions": positions,
        "allocation": allocation,
        "target": target,
        "alerts": alerts,
        "portfolio_hash": portfolio_svc.portfolio_hash(positions),
    }


@router.get("/portfolio")
async def portfolio() -> dict[str, Any]:
    return await _portfolio_bundle()


@router.get("/portfolio/pulse")
async def portfolio_pulse() -> dict[str, Any]:
    bundle = await _portfolio_bundle()
    risk = await run_in_threadpool(risk_svc.portfolio_risk, bundle["positions"])
    pulse = await run_in_threadpool(
        pulse_agent.narrative,
        bundle["positions"], bundle["allocation"], risk, bundle["target"],
        bundle["revalued"]["day_pnl_pct"],
    )
    return {**bundle, "risk": risk, "pulse": pulse}


# Per-holding ------------------------------------------------------------
@router.get("/holdings/{ticker}/candles")
async def holding_candles(ticker: str, timeframe: str = Query("1d")) -> dict[str, Any]:
    profile = profile_mod.get_profile()
    holding = next((h for h in profile["holdings"] if h["ticker"].upper() == ticker.upper()), None)
    if holding is None:
        raise HTTPException(404, f"unknown ticker {ticker}")
    if holding["asset_class"] == "Cash":
        return {"symbol": ticker, "timeframe": timeframe, "candles": [], "source": "cash", "synthesized": False}
    if holding["asset_class"] == "Fixed Income":
        # Synthesize a price walk for the sukuk from yield curve
        candles = prices_svc._synth_candles(seed=f"{ticker}:{timeframe}", count=60)
        return {"symbol": ticker, "timeframe": timeframe, "candles": candles,
                "source": "yield-curve+duration", "synthesized": True}
    candles = await run_in_threadpool(prices_svc.get_candles, holding["yahoo_symbol"], timeframe)
    return candles


@router.get("/holdings/{ticker}/chart-explanation")
async def holding_chart_explanation(ticker: str, timeframe: str = Query("1d")) -> dict[str, Any]:
    candles_data = await holding_candles(ticker, timeframe)
    candles = candles_data.get("candles", [])
    explanation = await run_in_threadpool(chart_agent.explain, candles, ticker, timeframe)
    return {"ticker": ticker, "timeframe": timeframe, "explanation": explanation,
            "source": candles_data.get("source"), "synthesized": candles_data.get("synthesized", False)}


@router.get("/holdings/{ticker}/news")
async def holding_news(ticker: str, limit: int = Query(6, ge=1, le=20)) -> dict[str, Any]:
    items = await run_in_threadpool(news_svc.fetch_for_ticker, ticker, limit)
    return {"ticker": ticker, "items": items}


@router.get("/holdings/{ticker}")
async def holding_detail(ticker: str) -> dict[str, Any]:
    profile = profile_mod.get_profile()
    holding = next((h for h in profile["holdings"] if h["ticker"].upper() == ticker.upper()), None)
    if holding is None:
        raise HTTPException(404, f"unknown ticker {ticker}")
    risk_metrics: dict[str, Any] = {}
    if holding.get("yahoo_symbol"):
        sym = holding["yahoo_symbol"]
        risk_metrics = {
            "beta": await run_in_threadpool(risk_svc.beta, sym),
            "volatility_annualised_pct": await run_in_threadpool(risk_svc.volatility_annualised, sym, 30),
            "max_drawdown_1y_pct": await run_in_threadpool(risk_svc.max_drawdown, sym, 365),
            "sharpe_1y": await run_in_threadpool(risk_svc.sharpe, sym, 365),
        }
    return {"holding": holding, "risk_metrics": risk_metrics}


# News + personalization -------------------------------------------------
@router.get("/news")
async def list_news(limit: int = Query(12, ge=1, le=30)) -> dict[str, Any]:
    bundle = await _portfolio_bundle()
    raw_articles = await run_in_threadpool(news_svc.fetch_articles, bundle["positions"], limit)
    portfolio_hash = bundle["portfolio_hash"]
    personalized = await asyncio.gather(*[
        run_in_threadpool(personalization_agent.personalize, art, bundle["positions"], portfolio_hash)
        for art in raw_articles
    ])
    enriched: list[dict[str, Any]] = []
    for art, pers in zip(raw_articles, personalized):
        enriched.append({**art, "personalization": pers})
    return {"articles": enriched, "portfolio_hash": portfolio_hash}


# Risk ------------------------------------------------------------------
@router.get("/risk")
async def risk_endpoint() -> dict[str, Any]:
    bundle = await _portfolio_bundle()
    risk = await run_in_threadpool(risk_svc.portfolio_risk, bundle["positions"])
    return {"risk": risk, "positions_summary": [
        {"ticker": p["ticker"], "weight_pct": round(p["weight_pct"], 2)} for p in bundle["positions"]
    ]}


# Advisory --------------------------------------------------------------
@router.get("/advisory")
async def advisory_endpoint() -> dict[str, Any]:
    bundle = await _portfolio_bundle()
    risk = await run_in_threadpool(risk_svc.portfolio_risk, bundle["positions"])
    advisory = await run_in_threadpool(
        advisory_agent.advise,
        bundle["positions"], bundle["allocation"], risk, bundle["target"], profile_mod.get_profile(),
    )
    return {"advisory": advisory, "risk": risk}


# Scenario --------------------------------------------------------------
@router.get("/scenarios")
async def list_scenarios() -> dict[str, Any]:
    return {"scenarios": scenario_agent.list_scenarios()}


class ScenarioRunRequest(BaseModel):
    scenario_id: str


# GET variant so the xense.dev GET-only reverse-proxy can reach it from the browser.
@router.get("/scenarios/run")
async def scenario_run_get(scenario_id: str = Query("us-tech-drawdown")) -> dict[str, Any]:
    bundle = await _portfolio_bundle()
    return await run_in_threadpool(scenario_agent.run, scenario_id, bundle["positions"])


@router.post("/scenarios/run")
async def scenario_run(body: ScenarioRunRequest) -> dict[str, Any]:
    bundle = await _portfolio_bundle()
    return await run_in_threadpool(scenario_agent.run, body.scenario_id, bundle["positions"])


# Catalysts -------------------------------------------------------------
@router.get("/catalysts")
async def catalysts() -> dict[str, Any]:
    """Return a compact catalyst calendar from FRED + per-holding earnings.

    Earnings dates come from yfinance.Ticker.calendar when available; macro
    catalysts come from FRED meeting series. Where free intraday feeds don't
    exist, we return a clearly-labelled empty list rather than synthesise.
    """
    profile = profile_mod.get_profile()
    items: list[dict[str, Any]] = []
    import yfinance as yf  # lazy
    import datetime as _dt
    def _to_iso(v: Any) -> str | None:
        """Coerce a yfinance date value to an ISO-8601 string, never repr()."""
        if isinstance(v, list):
            v = v[0] if v else None
        if v is None:
            return None
        if hasattr(v, "isoformat"):
            return v.isoformat()
        s = str(v)
        # Guard: reject any string that looks like a Python repr
        if s.startswith("datetime.") or s.startswith("[datetime."):
            return None
        return s

    for h in profile["holdings"]:
        if not h.get("yahoo_symbol"):
            continue
        try:
            tkr = yf.Ticker(h["yahoo_symbol"])
            cal = tkr.calendar
            if hasattr(cal, "to_dict"):
                cal = cal.to_dict()
            if isinstance(cal, dict):
                for key, value in cal.items():
                    if "earnings" in key.lower() and value:
                        iso = _to_iso(value)
                        if iso is None:
                            continue
                        items.append({
                            "ticker": h["ticker"], "name": h["name"],
                            "kind": "earnings", "label": key,
                            "value": iso, "source": "yfinance",
                        })
        except Exception:
            continue
    macro_calendar = [
        {"ticker": None, "kind": "macro", "label": "FOMC decision",
         "source": "FRED publication schedule",
         "note": "See FOMC scheduled meeting dates"},
        {"ticker": None, "kind": "macro", "label": "ECB meeting",
         "source": "ECB published calendar"},
        {"ticker": None, "kind": "macro", "label": "OPEC+ ministerial",
         "source": "OPEC public schedule"},
    ]
    return {"items": items, "macro": macro_calendar,
            "note": "Earnings dates from yfinance; macro tags reference public central-bank calendars."}


# Macro -----------------------------------------------------------------
@router.get("/macro")
async def macro_endpoint() -> dict[str, Any]:
    return await run_in_threadpool(macro_svc.macro_snapshot)


# Chat ------------------------------------------------------------------
class ChatRequest(BaseModel):
    messages: list[dict[str, str]]


@router.post("/chat")
async def chat(body: ChatRequest) -> dict[str, Any]:
    bundle = await _portfolio_bundle()
    risk = await run_in_threadpool(risk_svc.portfolio_risk, bundle["positions"])
    ctx = {
        "positions": [
            {"ticker": p["ticker"], "weight_pct": round(p["weight_pct"], 2),
             "asset_class": p["asset_class"], "geography": p["geography"]}
            for p in bundle["positions"]
        ],
        "allocation": bundle["allocation"],
        "alerts": bundle["alerts"],
        "risk": risk.get("portfolio", {}),
        "stated_risk_profile": "Balanced (Moderate Growth)",
    }
    reply = await run_in_threadpool(chat_agent.respond, body.messages, ctx)
    return {"reply": reply, "context_keys": list(ctx.keys())}


# RM Routing (stub) -----------------------------------------------------
class RmRouteRequest(BaseModel):
    holding: str
    action: str
    reasoning: str
    note: str = ""


import datetime as _rm_dt, uuid as _uuid

_rm_log: list[dict[str, Any]] = []


@router.post("/rm-route")
async def rm_route(body: RmRouteRequest) -> dict[str, Any]:
    entry = {
        "id": str(_uuid.uuid4()),
        "timestamp": _rm_dt.datetime.utcnow().isoformat() + "Z",
        "holding": body.holding,
        "action": body.action,
        "reasoning": body.reasoning,
        "note": body.note,
        "status": "routed_to_rm",
    }
    _rm_log.append(entry)
    return {"ok": True, "entry": entry}


@router.get("/rm-route/log")
async def rm_route_log() -> dict[str, Any]:
    return {"entries": _rm_log}


# PDF export ------------------------------------------------------------
@router.get("/export/pdf")
async def export_pdf() -> Response:
    """Generate and return a CIO briefing PDF using reportlab (no headless browser needed)."""
    try:
        bundle = await _portfolio_bundle()
        risk = await run_in_threadpool(risk_svc.portfolio_risk, bundle["positions"])
        advisory_result = await run_in_threadpool(
            advisory_agent.advise,
            bundle["positions"], bundle["allocation"], risk, bundle["target"], profile_mod.get_profile(),
        )
        advisory_text: str | None = None
        if isinstance(advisory_result, dict):
            advisory_text = advisory_result.get("recommendation") or advisory_result.get("narrative")
        elif isinstance(advisory_result, str):
            advisory_text = advisory_result

        pulse_text: str | None = None
        try:
            pulse_result = await run_in_threadpool(
                pulse_agent.narrative,
                bundle["positions"], bundle["allocation"], risk, bundle["target"],
                bundle["revalued"]["day_pnl_pct"],
            )
            if isinstance(pulse_result, dict):
                pulse_text = pulse_result.get("narrative") or pulse_result.get("pulse")
            elif isinstance(pulse_result, str):
                pulse_text = pulse_result
        except Exception:
            pass

        pdf_bytes = await run_in_threadpool(
            pdf_svc.generate,
            profile_mod.get_profile(),
            bundle["positions"],
            bundle["allocation"],
            bundle["alerts"],
            risk,
            advisory_text,
            pulse_text,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}") from e

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="cio-briefing.pdf"'},
    )


# Healthcheck -----------------------------------------------------------
@router.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "ok": True,
        "ai_live": ai_client.is_live(),
    }
