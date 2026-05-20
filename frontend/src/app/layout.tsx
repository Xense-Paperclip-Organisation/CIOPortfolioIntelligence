import type { Metadata } from 'next';
import './globals.css';
import { ThemeToggle } from '@/components/ThemeToggle';

export const metadata: Metadata = {
  title: 'CIO Portfolio Intelligence — Emirates NBD',
  description: 'Personalized, portfolio-aware advisory dashboard (POC)'
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;700&family=JetBrains+Mono:wght@400;500&display=swap"
        />
      </head>
      <body className="min-h-screen font-sans antialiased">
        <header className="sticky top-0 z-20 border-b border-white/[0.06] bg-ink-950/80 backdrop-blur-xl">
          <div className="mx-auto flex max-w-[1440px] items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <div className="grid h-9 w-9 place-items-center rounded-md bg-gradient-to-br from-accent-gold/80 to-amber-200/40 font-display text-base font-bold text-ink-950">eN</div>
              <div className="leading-tight">
                <div className="font-display text-sm font-bold tracking-tight">Emirates NBD Wealth</div>
                <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-accent-steel">CIO Portfolio Intelligence · POC</div>
              </div>
            </div>
            <ThemeToggle />
          </div>
        </header>
        <main className="mx-auto max-w-[1440px] px-6 py-6">{children}</main>
        <footer className="mx-auto max-w-[1440px] px-6 pb-10 pt-4 text-center font-mono text-[10px] uppercase tracking-wider text-accent-steel/70">
          Demo-grade POC · placeholder disclaimers only · live data from yfinance, public RSS, FRED, exchangerate.host
        </footer>
      </body>
    </html>
  );
}
