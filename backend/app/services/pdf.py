"""Generate a CIO briefing PDF using reportlab (no headless browser required)."""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_GOLD = colors.HexColor("#C9A85C")
_DARK = colors.HexColor("#0D1117")
_STEEL = colors.HexColor("#8B9BB4")
_WHITE = colors.white
_LIGHT_BG = colors.HexColor("#161B22")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=_GOLD,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Helvetica",
            fontSize=10,
            textColor=_STEEL,
            spaceAfter=12,
        ),
        "section": ParagraphStyle(
            "section",
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=_GOLD,
            spaceBefore=14,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#C9D1D9"),
            spaceAfter=4,
            leading=14,
        ),
        "alert": ParagraphStyle(
            "alert",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=colors.HexColor("#F0A020"),
            spaceAfter=3,
            leftIndent=8,
        ),
    }


def _position_table(positions: list[dict[str, Any]]) -> Table:
    header = ["Holding", "Asset Class", "Geography", "Value (AED)", "Weight %"]
    rows = [header]
    for p in positions:
        rows.append([
            p.get("ticker", ""),
            p.get("asset_class", ""),
            p.get("geography", ""),
            f"{p.get('value_aed', 0):,.0f}",
            f"{p.get('weight_pct', 0):.1f}%",
        ])
    col_widths = [35 * mm, 35 * mm, 35 * mm, 35 * mm, 25 * mm]
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0D1117"), colors.HexColor("#161B22")]),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#C9D1D9")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#30363D")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _risk_table(risk: dict[str, Any]) -> Table:
    port = risk.get("portfolio", {})
    rows = [
        ["Metric", "Value"],
        ["Volatility (ann.)", f"{port.get('volatility_annualised_pct', 'N/A')}"],
        ["Max Drawdown (1Y)", f"{port.get('max_drawdown_1y_pct', 'N/A')}"],
        ["Beta", f"{port.get('beta', 'N/A')}"],
        ["Sharpe (1Y)", f"{port.get('sharpe_1y', 'N/A')}"],
    ]
    col_widths = [80 * mm, 80 * mm]
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0D1117"), colors.HexColor("#161B22")]),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#C9D1D9")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#30363D")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def generate(
    profile: dict[str, Any],
    positions: list[dict[str, Any]],
    allocation: dict[str, Any],
    alerts: list[dict[str, Any]],
    risk: dict[str, Any],
    advisory: str | None = None,
    pulse: str | None = None,
) -> bytes:
    """Return PDF bytes for the CIO briefing."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="CIO Portfolio Briefing",
        author="Wealth Tribe Nexus — EmiratesNBD",
    )

    s = _styles()
    story: list[Any] = []

    # Header
    ts = datetime.utcnow().strftime("%d %b %Y, %H:%M UTC")
    story.append(Paragraph("CIO Portfolio Intelligence Briefing", s["title"]))
    story.append(Paragraph(f"Emirates NBD Wealth — {ts}", s["subtitle"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_GOLD))
    story.append(Spacer(1, 8 * mm))

    # Client profile
    story.append(Paragraph("Client Profile", s["section"]))
    client_name = profile.get("client_name", "—")
    rm = profile.get("relationship_manager", "—")
    risk_profile = profile.get("risk_profile", "—")
    story.append(Paragraph(
        f"<b>Client:</b> {client_name} &nbsp;&nbsp; <b>RM:</b> {rm} &nbsp;&nbsp; <b>Risk Profile:</b> {risk_profile}",
        s["body"],
    ))
    story.append(Spacer(1, 4 * mm))

    # Portfolio summary
    story.append(Paragraph("Portfolio Holdings", s["section"]))
    if positions:
        story.append(_position_table(positions))
    else:
        story.append(Paragraph("No positions data available.", s["body"]))
    story.append(Spacer(1, 4 * mm))

    # Allocation
    story.append(Paragraph("Asset Allocation", s["section"]))
    if allocation:
        alloc_rows = [["Asset Class", "Weight %"]] + [
            [k, f"{v:.1f}%"] for k, v in allocation.items() if isinstance(v, (int, float))
        ]
        if len(alloc_rows) > 1:
            at = Table(alloc_rows, colWidths=[90 * mm, 70 * mm], repeatRows=1)
            at.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _GOLD),
                ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#0D1117"), colors.HexColor("#161B22")]),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#C9D1D9")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#30363D")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(at)
    story.append(Spacer(1, 4 * mm))

    # Alerts
    if alerts:
        story.append(Paragraph("Alignment Alerts", s["section"]))
        for alert in alerts[:10]:
            msg = alert.get("message") or str(alert)
            story.append(Paragraph(f"⚠ {msg}", s["alert"]))
        story.append(Spacer(1, 4 * mm))

    # Risk
    story.append(Paragraph("Risk Metrics", s["section"]))
    story.append(_risk_table(risk))
    story.append(Spacer(1, 4 * mm))

    # Pulse narrative
    if pulse:
        story.append(Paragraph("Portfolio Pulse (AI Narrative)", s["section"]))
        story.append(Paragraph(pulse.replace("<", "&lt;").replace(">", "&gt;"), s["body"]))
        story.append(Spacer(1, 4 * mm))

    # Advisory recommendation
    if advisory:
        story.append(Paragraph("Advisory Recommendation (AI)", s["section"]))
        for line in advisory.splitlines():
            if line.strip():
                story.append(Paragraph(line.replace("<", "&lt;").replace(">", "&gt;"), s["body"]))
        story.append(Spacer(1, 4 * mm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.3, color=_STEEL))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        "CONFIDENTIAL — For internal use only. Not for distribution. "
        "This document is generated automatically and does not constitute investment advice.",
        ParagraphStyle("footer", fontName="Helvetica-Oblique", fontSize=7, textColor=_STEEL),
    ))

    doc.build(story)
    return buf.getvalue()
