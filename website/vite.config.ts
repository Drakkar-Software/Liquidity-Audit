/// <reference types="vitest/config" />
import { defineConfig, loadEnv, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { DEFAULT_DESCRIPTION, DEFAULT_OG_IMAGE_ALT, buildWebSiteJsonLd, normalizeSiteUrl } from './src/lib/siteMeta';

function htmlSiteMetaPlugin(siteUrl: string): Plugin {
  const normalizedSiteUrl = normalizeSiteUrl(siteUrl);
  const websiteJsonLd = JSON.stringify(buildWebSiteJsonLd(normalizedSiteUrl)).replace(/</g, '\\u003c');

  return {
    name: 'html-site-meta',
    transformIndexHtml(html) {
      return html
        .replaceAll('__SITE_URL__', normalizedSiteUrl)
        .replaceAll('__DEFAULT_DESCRIPTION__', DEFAULT_DESCRIPTION)
        .replaceAll('__DEFAULT_OG_IMAGE_ALT__', DEFAULT_OG_IMAGE_ALT)
        .replace('__WEBSITE_JSON_LD__', websiteJsonLd);
    },
  };
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  if (mode === 'production') {
    const analysisDataBase = env.VITE_ANALYSIS_DATA_BASE?.trim();
    if (!analysisDataBase) {
      throw new Error(
        'VITE_ANALYSIS_DATA_BASE must be set for production builds (public R2 JSON base URL).',
      );
    }
    const siteUrl = env.VITE_SITE_URL?.trim();
    if (!siteUrl) {
      throw new Error('VITE_SITE_URL must be set for production builds (public site origin, no trailing slash).');
    }
    const posthogKey = env.VITE_POSTHOG_KEY?.trim();
    if (!posthogKey) {
      throw new Error('VITE_POSTHOG_KEY must be set for production builds (PostHog EU Cloud).');
    }
    const sentryDsn = env.VITE_SENTRY_DSN?.trim();
    if (!sentryDsn) {
      throw new Error('VITE_SENTRY_DSN must be set for production builds (Sentry error reporting DSN).');
    }
  }

  const siteUrl = env.VITE_SITE_URL?.trim() || 'http://localhost:5173';

  return {
    plugins: [react(), htmlSiteMetaPlugin(siteUrl)],
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      css: true,
      exclude: ['**/node_modules/**', '**/e2e/**'],
    },
  };
});
