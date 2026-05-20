export type AssetClass = 'Equity' | 'Fixed Income' | 'Cash' | 'Commodity' | 'Alternatives';
export type Geography = 'USA' | 'Europe' | 'Japan' | 'EM Asia' | 'MENA' | 'Global' | 'UAE';

export interface Quote {
  symbol?: string;
  price: number;
  open?: number;
  high?: number;
  low?: number;
  previous_close?: number;
  day_change_abs?: number;
  day_change_pct?: number;
  week_change_pct?: number;
  volume?: number;
  as_of?: string;
  source: string;
  synthesized: boolean;
  yield_pct?: number;
  duration_years?: number;
}

export interface Position {
  ticker: string;
  name: string;
  asset_class: AssetClass;
  geography: Geography;
  sector?: string;
  currency: string;
  quote: Quote;
  shares?: number;
  cost_basis_per_share?: number;
  value_usd: number;
  value_native: number;
  day_pnl_usd: number;
  weight_pct: number;
  unrealized_pnl_native?: number;
  quantity?: number;
}

export interface AllocationBuckets {
  asset_class: Record<string, number>;
  geography: Record<string, number>;
  sector: Record<string, number>;
  currency: Record<string, number>;
}

export interface AlignmentAlert {
  severity: 'high' | 'medium' | 'low';
  category: string;
  headline: string;
  body: string;
  metric?: Record<string, any>;
}

export interface PortfolioBundle {
  revalued: {
    positions: Position[];
    total_value_usd: number;
    total_value_aed: number;
    day_pnl_usd: number;
    day_pnl_pct: number;
    fx_usd_aed: number;
    as_of: string;
  };
  positions: Position[];
  allocation: AllocationBuckets;
  target: any;
  alerts: AlignmentAlert[];
  portfolio_hash: string;
}

export interface Pulse {
  narrative: string;
  health_score: number;
  headline_metric: string;
  degraded?: boolean;
}

export interface RiskMetrics {
  portfolio: {
    beta?: number | null;
    vol_annualised_pct?: number;
    expected_return_annualised_pct?: number;
    sharpe_1y?: number | null;
    max_drawdown_1y_pct?: number;
  };
  per_symbol: Record<string, {
    beta?: number | null;
    vol_30d_annualised?: number | null;
    max_drawdown_1y_pct?: number | null;
    sharpe_1y?: number | null;
  }>;
  correlation: {
    symbols: string[];
    matrix: number[][];
  };
}

export interface ImpactTile {
  ticker: string;
  name: string;
  direction: 'positive' | 'negative' | 'neutral';
  confidence: number;
  rationale?: string;
  logo_url?: string;
}

export interface Personalization {
  summary_paragraph: string;
  impact_tiles: ImpactTile[];
  transmission_paragraph: string;
  named_securities: string[];
  qa?: { ok: boolean; issues?: string[]; fallback_used?: string[] };
  degraded?: boolean;
}

export interface Article {
  id: string;
  title: string;
  summary: string;
  link: string;
  published?: string | null;
  source: string;
  matched_tickers: string[];
  score: number;
  personalization?: Personalization;
}

export interface AdvisoryRec {
  action: 'Rebalance' | 'Diversify' | 'Hold' | 'Trim' | 'Add';
  target_holding: string;
  reasoning: string;
  suggested_size_change?: number | null;
  suggested_replacement?: string | null;
}

export interface AdvisoryOutput {
  headline?: string;
  recommendations: AdvisoryRec[];
  diversification_gap_analysis: string;
  currency_commentary: string;
  education_funding_stress: string;
  qa?: any;
  degraded?: boolean;
}

export interface Candle { t: string; o: number; h: number; l: number; c: number; v: number }

export interface ChartExplanation {
  direction: { pct: number; tag: string };
  range: { high: number; low: number };
  volume_tag: string;
  pattern: { name: string; explanation: string };
  key_moment: string;
  support: number;
  resistance: number;
  next_target: number;
  last_candle: string;
  degraded?: boolean;
}

export interface ScenarioPerHolding {
  ticker: string;
  impact_pct: number;
  comment?: string;
}

export interface ScenarioResult {
  scenario: { id: string; label: string; description: string };
  rationale: string;
  per_holding: ScenarioPerHolding[];
  total_portfolio_impact_pct: number;
  degraded?: boolean;
}

export interface MacroSnapshot {
  us_treasury_yield_curve: Record<string, number>;
  us_cpi_yoy_pct?: number | null;
  fx_usd_aed?: number;
  fx_usd_sar?: number;
  fx_eur_usd?: number;
  as_of: number;
  sources: string[];
}
