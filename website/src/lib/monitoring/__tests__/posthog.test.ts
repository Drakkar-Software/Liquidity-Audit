import { describe, expect, it, vi } from 'vitest';
import {
  buildPostHogOptions,
  getPostHogHost,
  getPostHogKey,
  isPostHogEnabled,
  POSTHOG_DEFAULTS,
  POSTHOG_EU_INGEST_HOST,
  POSTHOG_EU_UI_HOST,
  POSTHOG_PROJECT_ID,
} from '../posthog';

describe('POSTHOG_PROJECT_ID', () => {
  it('documents the EU cloud project id', () => {
    expect(POSTHOG_PROJECT_ID).toBe('211740');
  });
});

describe('getPostHogKey', () => {
  it('returns the trimmed posthog key env value', () => {
    vi.stubEnv('VITE_POSTHOG_KEY', '  phc_example  ');
    expect(getPostHogKey()).toBe('phc_example');
  });
});

describe('getPostHogHost', () => {
  it('defaults to the EU cloud ingest host', () => {
    vi.stubEnv('VITE_POSTHOG_HOST', '');
    expect(getPostHogHost()).toBe(POSTHOG_EU_INGEST_HOST);
  });

  it('uses a configured host override', () => {
    vi.stubEnv('VITE_POSTHOG_HOST', 'https://custom.posthog.example');
    expect(getPostHogHost()).toBe('https://custom.posthog.example');
  });
});

describe('buildPostHogOptions', () => {
  it('targets EU cloud ingest and ui hosts with SPA tracking settings', () => {
    vi.stubEnv('VITE_POSTHOG_HOST', '');
    expect(buildPostHogOptions()).toEqual({
      api_host: POSTHOG_EU_INGEST_HOST,
      ui_host: POSTHOG_EU_UI_HOST,
      defaults: POSTHOG_DEFAULTS,
      capture_pageview: false,
      capture_pageleave: true,
      autocapture: true,
    });
  });
});

describe('isPostHogEnabled', () => {
  it('is false when the key is missing', () => {
    vi.stubEnv('VITE_POSTHOG_KEY', '');
    expect(isPostHogEnabled()).toBe(false);
  });

  it('is false during vitest even when a key is configured', () => {
    vi.stubEnv('VITE_POSTHOG_KEY', 'phc_example');
    expect(isPostHogEnabled()).toBe(false);
  });
});
