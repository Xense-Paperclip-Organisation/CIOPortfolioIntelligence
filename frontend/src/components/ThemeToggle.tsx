'use client';
import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

export function ThemeToggle() {
  const [light, setLight] = useState(false);
  useEffect(() => {
    const stored = window.localStorage.getItem('cio-theme');
    if (stored === 'light') {
      document.documentElement.classList.add('light');
      setLight(true);
    }
  }, []);
  const toggle = () => {
    const next = !light;
    setLight(next);
    document.documentElement.classList.toggle('light', next);
    window.localStorage.setItem('cio-theme', next ? 'light' : 'dark');
  };
  return (
    <button
      onClick={toggle}
      aria-label="Toggle theme"
      className="flex items-center gap-2 rounded-md border border-token-border bg-token-surface px-3 py-1.5 text-xs font-medium text-token-fg-muted transition hover:border-token-accent hover:text-token-accent focus-visible:ring-2"
    >
      {light ? <Sun size={14} /> : <Moon size={14} />}
      {light ? 'Light' : 'Dark'}
    </button>
  );
}
