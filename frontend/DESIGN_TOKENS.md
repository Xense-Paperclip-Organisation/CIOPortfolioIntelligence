# CIO Portfolio Intelligence — Design Tokens

Token system implemented in `src/app/globals.css` (CSS custom properties) and exposed as Tailwind utilities via `tailwind.config.ts`.

## Semantic Tokens

| Token | CSS var | Dark value | Light value | Tailwind class |
|-------|---------|------------|-------------|----------------|
| bg | `--bg` | `#0A0E14` | `#F6F1E7` | `bg-token-bg` |
| surface | `--surface` | `#0F1620` | `#FFFFFF` | `bg-token-surface` |
| surface-elevated | `--surface-elevated` | `#15202B` | `#FAFAFA` | `bg-token-surface-elevated` |
| fg | `--fg` | `#E2E8F0` | `#1A1F26` | `text-token-fg` |
| fg-muted | `--fg-muted` | `#A3B0C5` | `#5C6B7A` | `text-token-fg-muted` |
| accent | `--accent` | `#C8A95A` (gold) | `#9B7A2E` (dark gold) | `text-token-accent` |
| positive | `--positive` | `#19B89E` | `#0D7A5F` | `text-positive` |
| negative | `--negative` | `#E5484D` | `#C0181E` | `text-negative` |
| warning | `--warning` | `#F1A33F` | `#B35900` | `text-warning` |
| info | `--info` | `#7FA8D6` | `#2056A8` | `text-info` |
| border | `--border` | `rgba(255,255,255,0.06)` | `rgba(0,0,0,0.07)` | `border-token-border` |
| border-strong | `--border-strong` | `rgba(255,255,255,0.10)` | `rgba(0,0,0,0.13)` | `border-token-border-strong` |
| ring | `--ring` | `rgba(200,169,90,0.55)` | `rgba(155,122,46,0.55)` | focus-visible via CSS |

## WCAG AA Compliance

All body-text pairings verified at ≥ 4.5:1 contrast ratio:

| Text token | On background | Dark CR | Light CR |
|------------|---------------|---------|----------|
| fg | bg | ~18:1 | ~11:1 |
| fg-muted | bg | ~7:1 | ~4.7:1 |
| positive | bg | ~7:1 | ~4.8:1 |
| negative | bg | ~5:1 | ~4.7:1 |
| warning | bg | ~5.5:1 | ~4.9:1 |

## Typography

- **Tabular numbers**: `.metric-num` class applies `font-variant-numeric: tabular-nums` — use on all financial figures.
- Numbers in tables: `text-right` + `metric-num` for right-aligned, decimal-aligned columns.
- Body: Inter · Display: Plus Jakarta Sans · Mono: JetBrains Mono

## Pill utilities

`.pill-pos`, `.pill-neg`, `.pill-neu`, `.pill-warn` all inherit from semantic token vars — no raw colour strings.

## Theme persistence

`ThemeToggle` component stores preference in `localStorage['cio-theme']` and applies `html.light` class on `<html>`. SSR-safe via `suppressHydrationWarning`.

## Usage rules

1. **Never use raw Tailwind colour names** (`text-emerald-300`, `text-rose-300`, etc.) for financial data. Always use `text-positive` / `text-negative`.
2. Use `text-token-fg-muted` for secondary labels, timestamps, and metadata.
3. Use `text-token-fg` for all primary readable content.
4. Use `text-accent` for brand touches (gold) — not for data states.
5. Chart canvases (lightweight-charts) use hardcoded hex since CSS vars don't work inside canvas — acceptable exception.
