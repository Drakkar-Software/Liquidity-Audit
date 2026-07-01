import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { applyPageMetaToDocument, clearRoutePageMeta } from './applyPageMeta';
import type { PageMetaTags } from './siteMeta';
import {
  buildCanonical,
  buildDefaultOgImage,
  DEFAULT_DESCRIPTION,
  getSiteUrl,
  SITE_NAME,
} from './siteMeta';

export interface PageMetaInput {
  title: string;
  description: string;
  canonicalPath?: string;
  ogType?: 'website' | 'article';
  ogImage?: string;
  ogImageAlt?: string;
  noIndex?: boolean;
  jsonLd?: Record<string, unknown> | Record<string, unknown>[];
}

function resolvePageMetaTags(meta: PageMetaInput, pathname: string): PageMetaTags {
  const siteUrl = getSiteUrl();
  const canonicalPath = meta.canonicalPath ?? pathname;
  const canonicalUrl = buildCanonical(siteUrl, canonicalPath);
  return {
    title: meta.title,
    description: meta.description,
    canonicalUrl,
    ogType: meta.ogType,
    ogImage: meta.ogImage ?? (siteUrl ? buildDefaultOgImage(siteUrl) : undefined),
    ogImageAlt: meta.ogImageAlt,
    siteName: SITE_NAME,
    noIndex: meta.noIndex,
    jsonLd: meta.jsonLd,
  };
}

export function usePageMeta(meta: PageMetaInput): void {
  const location = useLocation();

  useEffect(() => {
    applyPageMetaToDocument(resolvePageMetaTags(meta, location.pathname));
    return () => {
      clearRoutePageMeta();
    };
  }, [
    meta.title,
    meta.description,
    meta.canonicalPath,
    meta.ogType,
    meta.ogImage,
    meta.ogImageAlt,
    meta.noIndex,
    JSON.stringify(meta.jsonLd),
    location.pathname,
  ]);
}

export function useDocumentTitle(title: string): void {
  usePageMeta({
    title,
    description: DEFAULT_DESCRIPTION,
  });
}
