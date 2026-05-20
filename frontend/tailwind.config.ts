import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: ['./src/**/*.{ts,tsx,js,jsx,mdx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#0A0E14',
          900: '#0F1620',
          800: '#15202B',
          700: '#1B2A3A',
          600: '#243549',
          100: '#E2E8F0'
        },
        accent: {
          gold: '#C8A95A',
          emerald: '#19B89E',
          ruby: '#E5484D',
          amber: '#F1A33F',
          steel: '#A3B0C5'
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['"Plus Jakarta Sans"', 'Inter', 'ui-sans-serif', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace']
      },
      boxShadow: {
        card: '0 1px 0 rgba(255,255,255,0.04) inset, 0 12px 30px rgba(0,0,0,0.35)'
      }
    }
  },
  plugins: []
};

export default config;
