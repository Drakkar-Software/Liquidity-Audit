import * as Sentry from '@sentry/react';

let sentryInitialized = false;

export function getSentryDsn(): string {
  const configuredDsn = import.meta.env.VITE_SENTRY_DSN;
  return configuredDsn?.trim() ?? '';
}

export function isSentryEnabled(): boolean {
  return Boolean(getSentryDsn()) && import.meta.env.MODE !== 'test';
}

export function initSentryMonitoring(): void {
  if (typeof window === 'undefined' || sentryInitialized || !isSentryEnabled()) {
    return;
  }

  Sentry.init({
    dsn: getSentryDsn(),
    environment: import.meta.env.MODE,
    tracesSampleRate: 0,
    replaysSessionSampleRate: 0,
    replaysOnErrorSampleRate: 0,
  });

  sentryInitialized = true;
}

export function captureAppError(
  error: Error,
  context?: { componentStack?: string | null },
): void {
  if (!isSentryEnabled()) {
    return;
  }

  Sentry.captureException(error, {
    contexts: context?.componentStack
      ? { react: { componentStack: context.componentStack } }
      : undefined,
  });
}
