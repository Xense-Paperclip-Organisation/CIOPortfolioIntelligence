'use client';

import React from 'react';
import { RefreshCw } from 'lucide-react';

interface Props {
  children: React.ReactNode;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-[60vh] items-center justify-center px-6">
          <div className="card max-w-lg w-full p-8 text-center">
            <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full border border-negative/30 bg-negative/10">
              <span className="font-mono text-lg text-negative">!</span>
            </div>
            <h2 className="font-display text-lg font-semibold text-token-fg">Something went wrong</h2>
            <p className="mt-2 text-sm text-token-fg-muted">
              An unexpected error occurred while rendering the dashboard.
            </p>
            {this.state.error.message && (
              <pre className="mt-3 max-w-full overflow-x-auto rounded-md border border-token-border bg-black/40 p-3 text-left text-[11px] text-token-fg-muted">
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={() => { this.setState({ error: null }); window.location.reload(); }}
              className="mt-5 inline-flex items-center gap-2 rounded-md border border-token-accent/40 bg-token-accent/10 px-4 py-2 text-sm font-medium text-accent hover:bg-token-accent/20"
            >
              <RefreshCw size={14} /> Reload dashboard
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
