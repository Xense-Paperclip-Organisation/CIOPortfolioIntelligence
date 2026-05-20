// Server-side fetch helper.  Uses BACKEND_URL when set so server components
// can talk to the FastAPI service directly inside the docker network.
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000';
const PUBLIC_BASE = process.env.NEXT_PUBLIC_API_BASE || '/api';

export function isServer() {
  return typeof window === 'undefined';
}

export function apiUrl(path: string): string {
  if (isServer()) {
    return `${BACKEND_URL}${path.startsWith('/api') ? path : `/api${path}`}`;
  }
  // Browser-side — always go through Next.js rewrite so nginx can proxy.
  return `${PUBLIC_BASE}${path.startsWith('/') ? path : `/${path}`}`.replace('/api/api', '/api');
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = apiUrl(path);
  const res = await fetch(url, {
    ...init,
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) }
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${body.slice(0, 200)}`);
  }
  return (await res.json()) as T;
}

export function fmtUsd(value: number | null | undefined, opts: { compact?: boolean } = {}): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: opts.compact ? 'compact' : 'standard',
    maximumFractionDigits: opts.compact ? 1 : 0
  }).format(value);
}

export function fmtAed(value: number | null | undefined, opts: { compact?: boolean } = {}): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return new Intl.NumberFormat('en-AE', {
    style: 'currency',
    currency: 'AED',
    notation: opts.compact ? 'compact' : 'standard',
    maximumFractionDigits: opts.compact ? 1 : 0
  }).format(value);
}

export function fmtPct(value: number | null | undefined, digits: number = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(digits)}%`;
}

export function fmtNum(value: number | null | undefined, digits: number = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: digits }).format(value);
}
