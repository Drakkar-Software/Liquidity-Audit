import React from 'react';
import { Link } from 'react-router-dom';
import { captureAppError } from '../lib/monitoring';
import { colors, fonts } from '../theme';

interface AppErrorBoundaryState {
  error: Error | null;
}

export interface AppErrorBoundaryProps {
  children: React.ReactNode;
}

/** Catches render errors in route content and shows a recoverable fallback instead of a white screen. */
export class AppErrorBoundary extends React.Component<AppErrorBoundaryProps, AppErrorBoundaryState> {
  constructor(props: AppErrorBoundaryProps) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error: Error): AppErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    console.error('AppErrorBoundary caught a render error:', error, errorInfo);
    captureAppError(error, { componentStack: errorInfo.componentStack });
  }

  render() {
    if (this.state.error) {
      return (
        <div
          className="page-section-centered"
          style={{
            padding: '48px 20px',
            textAlign: 'center',
            background: colors.screen,
            border: `1px solid ${colors.line2}`,
            borderRadius: 0,
          }}
        >
          <h1 style={{ margin: '0 0 12px', font: `600 22px ${fonts.sans}`, color: colors.ink }}>
            Something went wrong
          </h1>
          <p style={{ margin: '0 0 24px', font: `400 14px ${fonts.sans}`, color: colors.ink2 }}>
            This page could not be displayed. Try reloading or return to the home page.
          </p>
          {import.meta.env.DEV ? (
            <pre
              style={{
                margin: '0 0 24px',
                padding: 16,
                textAlign: 'left',
                overflow: 'auto',
                font: `400 12px ${fonts.mono}`,
                color: colors.red,
                background: colors.panel,
                border: `1px solid ${colors.line}`,
                borderRadius: 8,
              }}
            >
              {this.state.error.message}
            </pre>
          ) : null}
          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={() => window.location.reload()}
              style={{
                font: `600 13px ${fonts.mono}`,
                color: colors.accentInk,
                background: colors.accent,
                borderRadius: 7,
                padding: '12px 22px',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Reload page
            </button>
            <Link
              to="/"
              onClick={() => this.setState({ error: null })}
              style={{
                font: `600 13px ${fonts.mono}`,
                color: colors.ink2,
                border: `1px solid ${colors.line2}`,
                borderRadius: 7,
                padding: '12px 22px',
                textDecoration: 'none',
              }}
            >
              Back home
            </Link>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
