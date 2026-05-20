'use client';
import { useEffect, useRef, useState } from 'react';
import { createChart, ColorType, IChartApi, CandlestickSeriesPartialOptions } from 'lightweight-charts';
import { apiFetch, fmtPct } from '@/lib/api';
import type { Candle, ChartExplanation, Position } from '@/types/api';
import { Sparkles } from 'lucide-react';

const TIMEFRAMES = ['1m', '5m', '1h', '1d', '1mo', '1yr'] as const;
type TF = typeof TIMEFRAMES[number];

export function HoldingDetail({ ticker, position }: { ticker: string; position: Position }) {
  const [tf, setTf] = useState<TF>('1d');
  const [candles, setCandles] = useState<Candle[]>([]);
  const [explanation, setExplanation] = useState<ChartExplanation | null>(null);
  const [news, setNews] = useState<{ id: string; title: string; source: string; link: string; published?: string | null }[]>([]);
  const [loading, setLoading] = useState(true);
  const chartRef = useRef<IChartApi | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    Promise.all([
      apiFetch<{ candles: Candle[] }>(`/api/holdings/${encodeURIComponent(ticker)}/candles?timeframe=${tf}`),
      apiFetch<{ explanation: ChartExplanation }>(`/api/holdings/${encodeURIComponent(ticker)}/chart-explanation?timeframe=${tf}`),
      apiFetch<{ items: any[] }>(`/api/holdings/${encodeURIComponent(ticker)}/news?limit=4`).catch(() => ({ items: [] }))
    ]).then(([c, e, n]) => {
      if (cancelled) return;
      setCandles(c.candles || []);
      setExplanation(e.explanation);
      setNews(n.items || []);
      setLoading(false);
    }).catch(() => setLoading(false));
    return () => { cancelled = true; };
  }, [ticker, tf]);

  useEffect(() => {
    if (!containerRef.current || !candles.length) return;
    chartRef.current?.remove();
    const chart = createChart(containerRef.current, {
      layout: { background: { type: ColorType.Solid, color: 'transparent' }, textColor: '#A3B0C5' },
      grid: { horzLines: { color: 'rgba(255,255,255,0.04)' }, vertLines: { color: 'rgba(255,255,255,0.04)' } },
      timeScale: { borderColor: 'rgba(255,255,255,0.1)', timeVisible: true },
      rightPriceScale: { borderColor: 'rgba(255,255,255,0.1)' },
      height: 320
    });
    const series = chart.addCandlestickSeries({
      upColor: '#19B89E', downColor: '#E5484D',
      borderUpColor: '#19B89E', borderDownColor: '#E5484D',
      wickUpColor: '#19B89E', wickDownColor: '#E5484D'
    } as CandlestickSeriesPartialOptions);
    series.setData(candles.map((c) => ({
      time: Math.floor(new Date(c.t).getTime() / 1000) as any,
      open: c.o, high: c.h, low: c.l, close: c.c
    })));
    const volumeSeries = chart.addHistogramSeries({ priceFormat: { type: 'volume' }, priceScaleId: 'volume' });
    chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } });
    volumeSeries.setData(candles.map((c) => ({
      time: Math.floor(new Date(c.t).getTime() / 1000) as any,
      value: c.v,
      color: c.c >= c.o ? 'rgba(25,184,158,0.35)' : 'rgba(229,72,77,0.35)'
    })));
    chart.timeScale().fitContent();
    chartRef.current = chart;
    const resize = () => chart.applyOptions({ width: containerRef.current?.clientWidth || 600 });
    resize();
    window.addEventListener('resize', resize);
    return () => { window.removeEventListener('resize', resize); chart.remove(); };
  }, [candles]);

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[2fr_1fr]">
      <div>
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-1">
            {TIMEFRAMES.map((t) => (
              <button key={t} onClick={() => setTf(t)} className={`pill ${tf === t ? 'border-accent-gold/60 bg-accent-gold/10 text-accent-gold' : 'pill-neu'}`}>{t}</button>
            ))}
          </div>
          {position.quote.synthesized && (
            <span className="font-mono text-[10px] uppercase tracking-wider text-amber-300">Synthesized series</span>
          )}
        </div>
        <div ref={containerRef} className="h-[320px] w-full rounded-md border border-white/[0.05] bg-ink-950/60" />
        {loading && <div className="mt-2 text-[11px] text-accent-steel">Loading live OHLCV…</div>}
        {!!news.length && (
          <div className="mt-3">
            <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-accent-steel">Recent headlines</div>
            <ul className="mt-1 space-y-1 text-xs">
              {news.slice(0, 4).map((n) => (
                <li key={n.id}><a href={n.link} className="text-accent-steel hover:text-accent-gold" target="_blank" rel="noreferrer">{n.title}</a> <span className="font-mono text-[10px] uppercase tracking-wider text-accent-steel/60">· {n.source}</span></li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <div className="space-y-2">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.15em] text-accent-gold">
          <Sparkles size={12} /> AI chart explanation
        </div>
        {explanation ? (
          <div className="card p-3 text-[12px] leading-relaxed">
            <Row label="Direction" value={`${explanation.direction.tag} (${fmtPct(explanation.direction.pct)})`} />
            <Row label="Range" value={`${explanation.range.low.toFixed(2)} – ${explanation.range.high.toFixed(2)}`} />
            <Row label="Volume" value={explanation.volume_tag} />
            <Row label="Pattern" value={`${explanation.pattern.name} — ${explanation.pattern.explanation}`} />
            <Row label="Key moment" value={explanation.key_moment} />
            <Row label="Support" value={String(explanation.support)} />
            <Row label="Resistance" value={String(explanation.resistance)} />
            <Row label="Next target" value={String(explanation.next_target)} />
            <Row label="Last candle" value={explanation.last_candle} />
          </div>
        ) : (
          <div className="text-[11px] text-accent-steel">Loading chart commentary…</div>
        )}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-2 border-t border-white/[0.05] py-1 first:border-t-0">
      <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-accent-steel">{label}</div>
      <div className="max-w-[60%] text-right text-[12px]">{value}</div>
    </div>
  );
}
