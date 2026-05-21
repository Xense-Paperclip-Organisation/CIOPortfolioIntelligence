// Cross-component event bus for the dashboard. We use the global `window` as a
// pub-sub so unrelated components (e.g. Catalysts → Holdings) can coordinate
// without prop drilling or a top-level store.

export const FOCUS_HOLDING_EVENT = 'dashboard:focus-holding';

export interface FocusHoldingDetail {
  ticker: string;
}

export function focusHolding(ticker: string): void {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(new CustomEvent<FocusHoldingDetail>(FOCUS_HOLDING_EVENT, { detail: { ticker } }));
}

export function onFocusHolding(cb: (ticker: string) => void): () => void {
  if (typeof window === 'undefined') return () => {};
  const handler = (e: Event) => {
    const detail = (e as CustomEvent<FocusHoldingDetail>).detail;
    if (detail?.ticker) cb(detail.ticker);
  };
  window.addEventListener(FOCUS_HOLDING_EVENT, handler);
  return () => window.removeEventListener(FOCUS_HOLDING_EVENT, handler);
}
