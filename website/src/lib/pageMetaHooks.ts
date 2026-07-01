import {
  buildHomePageMeta,
  buildStaticPageMeta,
  buildPairMeta,
  DEFAULT_OG_IMAGE_ALT,
  finalizeMetaDescription,
  finalizeMetaTitle,
  getSiteUrl,
  PAGE_META,
} from './siteMeta';
import type { FaqItem } from './siteMeta';
import { usePageMeta } from './usePageMeta';
import type { TokenViewModel } from '../types';

export type StaticPageKey =
  | 'methodology'
  | 'about'
  | 'learn'
  | 'caseStudies'
  | 'cryptoLiquidity'
  | 'orderBookAnalysis'
  | 'bidAskSpread'
  | 'liquidityScore';

export function useHomePageMeta(): void {
  const siteUrl = getSiteUrl();
  const meta = buildHomePageMeta(siteUrl);
  usePageMeta({
    title: meta.title,
    description: meta.description,
    ogType: meta.ogType,
    ogImage: meta.ogImage,
    ogImageAlt: meta.ogImageAlt,
    jsonLd: meta.jsonLd,
  });
}

export function useStaticPageMeta(
  pageKey: StaticPageKey,
  path: string,
  pageLabel: string,
  options?: { faqs?: FaqItem[] },
): void {
  const siteUrl = getSiteUrl();
  const meta = buildStaticPageMeta(siteUrl, pageKey, path, pageLabel, options);
  usePageMeta({
    title: meta.title,
    description: meta.description,
    canonicalPath: path,
    ogType: meta.ogType,
    ogImage: meta.ogImage,
    ogImageAlt: meta.ogImageAlt,
    jsonLd: meta.jsonLd,
  });
}

export function useNotFoundPageMeta(): void {
  usePageMeta({
    title: finalizeMetaTitle(PAGE_META.notFound.title),
    description: finalizeMetaDescription(PAGE_META.notFound.description),
    ogImageAlt: DEFAULT_OG_IMAGE_ALT,
    noIndex: true,
  });
}

export function useLoadErrorPageMeta(message: string): void {
  usePageMeta({
    title: finalizeMetaTitle(PAGE_META.loadError.title),
    description: finalizeMetaDescription(
      message || PAGE_META.loadError.description,
      PAGE_META.loadError.description,
    ),
    ogImageAlt: DEFAULT_OG_IMAGE_ALT,
    noIndex: true,
  });
}

export function useTokenReportPageMeta(options: {
  exchange: string;
  slug: string;
  pair: string;
  viewModel: TokenViewModel | null;
  payload: {
    symbol: string;
    exchange: string;
    full_name?: string;
    raw?: { fetched_at?: string };
    analysis?: {
      score_100?: number;
      grade?: string;
      verdict?: string;
      issues?: { label: string; ok: boolean }[];
      status?: string;
    };
  } | null;
}): void {
  const siteUrl = getSiteUrl();
  const pairMeta = buildPairMeta(
    siteUrl,
    options.exchange,
    options.slug,
    options.pair,
    options.payload ?? {
      symbol: options.pair,
      exchange: options.exchange,
      analysis: options.viewModel
        ? {
            score_100: options.viewModel.score,
            grade: options.viewModel.grade,
            verdict: options.viewModel.verdict,
            issues: options.viewModel.issues,
            status: options.viewModel.status,
          }
        : undefined,
    },
  );

  usePageMeta({
    title: pairMeta.title,
    description: pairMeta.description,
    canonicalPath: `/pairs/${options.exchange}/${options.slug}`,
    ogType: pairMeta.ogType,
    ogImage: pairMeta.ogImage,
    ogImageAlt: pairMeta.ogImageAlt,
    jsonLd: pairMeta.jsonLd,
  });
}
