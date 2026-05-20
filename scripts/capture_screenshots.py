"""Headless screenshot capture for the CIO Portfolio Intelligence POC.

Usage:
    python scripts/capture_screenshots.py --base http://localhost:8080 --out docs/screenshots/

Requires Playwright in the local environment (`pip install playwright && playwright install
chromium`).  If Playwright is not available the script prints a fallback instruction.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path


SHOTS = [
    ("01-dark-home-fold", "dark", "fullPage", 0),
    ("02-light-home-fold", "light", "fullPage", 0),
]


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8080")
    parser.add_argument("--out", default="docs/screenshots")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.async_api import async_playwright  # type: ignore
    except ImportError:
        print("Playwright is not installed in this environment.\n"
              "Install with `pip install playwright && playwright install chromium`, then re-run.")
        print(f"As a fallback, capture the screenshots manually from a browser at {args.base}.")
        return 1

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for name, theme, mode, _ in SHOTS:
            ctx = await browser.new_context(viewport={"width": 1440, "height": 2200},
                                            color_scheme="dark" if theme == "dark" else "light")
            page = await ctx.new_page()
            await page.goto(args.base, wait_until="networkidle")
            if theme == "light":
                await page.evaluate("document.documentElement.classList.add('light')")
                await page.wait_for_timeout(300)
            out = out_dir / f"{name}.png"
            await page.screenshot(path=str(out), full_page=(mode == "fullPage"))
            print(f"captured {out}")
            await ctx.close()
        await browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
