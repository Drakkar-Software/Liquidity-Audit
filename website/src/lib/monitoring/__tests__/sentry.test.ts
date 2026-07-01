import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('@sentry/react', () => ({
  init: vi.fn(),
  captureException: vi.fn(),
}));

import * as Sentry from '@sentry/react';
import { captureAppError, getSentryDsn, initSentryMonitoring, isSentryEnabled } from '../sentry';

describe('getSentryDsn', () => {
  it('returns the trimmed sentry dsn env value', () => {
    vi.stubEnv('VITE_SENTRY_DSN', '  https://example@sentry.io/1  ');
    expect(getSentryDsn()).toBe('https://example@sentry.io/1');
  });

  it('returns an empty string when unset', () => {
    vi.stubEnv('VITE_SENTRY_DSN', '');
    expect(getSentryDsn()).toBe('');
  });
});

describe('isSentryEnabled', () => {
  it('is false when the dsn is missing', () => {
    vi.stubEnv('VITE_SENTRY_DSN', '');
    expect(isSentryEnabled()).toBe(false);
  });

  it('is false during vitest even when a dsn is configured', () => {
    vi.stubEnv('VITE_SENTRY_DSN', 'https://example@sentry.io/1');
    expect(isSentryEnabled()).toBe(false);
  });
});

describe('initSentryMonitoring', () => {
  beforeEach(() => {
    vi.mocked(Sentry.init).mockClear();
  });

  it('does not initialize sentry during tests', () => {
    vi.stubEnv('VITE_SENTRY_DSN', 'https://example@sentry.io/1');
    initSentryMonitoring();
    expect(Sentry.init).not.toHaveBeenCalled();
  });
});

describe('captureAppError', () => {
  beforeEach(() => {
    vi.mocked(Sentry.captureException).mockClear();
  });

  it('does not report when sentry is disabled', () => {
    vi.stubEnv('VITE_SENTRY_DSN', '');
    captureAppError(new Error('test failure'));
    expect(Sentry.captureException).not.toHaveBeenCalled();
  });
});
