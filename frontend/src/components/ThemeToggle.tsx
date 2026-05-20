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
      className="flex items-center gap-2 rounded-md border border-white/[0.08] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-accent-steel transition hover:border-accent-gold/40 hover:text-accent-gold"
    >
      {light ? <Sun size={14} /> : <Moon size={14} />}
      {light ? 'Light' : 'Dark'}
    </button>
  );
}
