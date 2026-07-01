import posthog from 'posthog-js';
import type { PostHogConfig } from 'posthog-js';

export const POSTHOG_PROJECT_ID = '211740';

export const POSTHOG_EU_INGEST_HOST = 'https://eu.i.posthog.com';

export const POSTHOG_EU_UI_HOST = 'https://eu.posthog.com';

export const POSTHOG_DEFAULTS = '2026-05-30' as const;

let posthogInitialized = false;

export function getPostHogKey(): string {
  const configuredKey = import.meta.env.VITE_POSTHOG_KEY;
  return configuredKey?.trim() ?? '';
}

export function getPostHogHost(): string {
  const configuredHost = import.meta.env.VITE_POSTHOG_HOST;
  return configuredHost?.trim() || POSTHOG_EU_INGEST_HOST;
}

export function isPostHogEnabled(): boolean {
  return Boolean(getPostHogKey()) && import.meta.env.MODE !== 'test';
}

export function buildPostHogOptions(): Partial<PostHogConfig> {
  return {
    api_host: getPostHogHost(),
    ui_host: POSTHOG_EU_UI_HOST,
    defaults: POSTHOG_DEFAULTS,
    capture_pageview: false,
    capture_pageleave: true,
    autocapture: true,
  };
}

export function initPostHogMonitoring(): void {
  if (posthogInitialized || !isPostHogEnabled()) {
    return;
  }

  posthog.init(getPostHogKey(), buildPostHogOptions());
  posthogInitialized = true;
}

export function getPostHogClient(): typeof posthog | null {
  if (!isPostHogEnabled() || !posthogInitialized) {
    return null;
  }

  return posthog;
}
