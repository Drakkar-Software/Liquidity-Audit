import { getFailedIssueDisplayLabel } from './issueCopy';

export const SITE_NAME = 'Crypto Liquidity Audit';

export const DEFAULT_DESCRIPTION =
  'Rank spot pairs by liquidity score. Token liquidity ranking and liquidity audit crypto: independent spread, depth, and slippage from order-book snapshots.';

export const DEFAULT_OG_IMAGE_ALT =
  'Crypto Liquidity Audit, default preview image for token liquidity ranking and pair reports';

export const PAGE_META = {
  home: {
    title: 'Token Liquidity Ranking · Crypto Liquidity Audit',
    description: DEFAULT_DESCRIPTION,
  },
  methodology: {
    title: 'Check Token Liquidity · Methodology · Crypto Liquidity Audit',
    description:
      'How to check crypto token liquidity on spot CEX pairs: read the liquidity score, order book depth, spread, and slippage from one visible snapshot.',
  },
  cryptoLiquidity: {
    title: 'Crypto Liquidity · Liquidity Analysis · Crypto Liquidity Audit',
    description:
      'What crypto liquidity means for spot traders, how liquidity analysis works on visible order books, and trading liquidity on CEX pairs.',
  },
  orderBookAnalysis: {
    title: 'Order Book Analysis · Crypto Order Book · Crypto Liquidity Audit',
    description:
      'Order book analysis for spot pairs: crypto order book depth, spread, and order book liquidity analysis from one snapshot per exchange.',
  },
  bidAskSpread: {
    title: 'Bid Ask Spread · Crypto Spread · Crypto Liquidity Audit',
    description:
      'What bid ask spread means on spot pairs, how crypto spread affects fills, and how we read spread from a visible order book.',
  },
  liquidityScore: {
    title: 'Liquidity Score · Crypto Pairs · Crypto Liquidity Audit',
    description:
      'What the crypto liquidity score measures on spot pairs, how liquidity score rankings work per exchange, and how to open a token pair report.',
  },
  about: {
    title: 'About · Crypto Liquidity Audit',
    description:
      'Independent crypto liquidity analysis for token teams and investors: transparent spot-pair scoring, exchange benchmarks, and numbers before recommendations.',
  },
  learn: {
    title: 'Learn · Crypto Liquidity Audit',
    description:
      'Crypto liquidity report glossary: spread, depth, slippage, peer median, volume consistency, and letter grades used on spot CEX pair reports.',
  },
  caseStudies: {
    title: 'Case Studies · Crypto Liquidity Audit',
    description:
      'Case studies on lowering CEX–DEX arbitrage with DEX price feeds and staying listed on MEXC by tightening spread and depth with automated quoting.',
  },
  notFound: {
    title: 'Not found · Crypto Liquidity Audit',
    description:
      'The crypto liquidity page you requested is not on Crypto Liquidity Audit. Return to token rankings, methodology, or browse a spot pair liquidity report.',
  },
  loadError: {
    title: 'Analysis unavailable · Crypto Liquidity Audit',
    description:
      'This crypto spot pair liquidity analysis is temporarily unavailable. Try again or choose another token from the Crypto Liquidity Audit rankings.',
  },
} as const;

export const SOCIAL_CRAWLER_PATTERN =
  /facebookexternalhit|Facebot|Twitterbot|LinkedInBot|Slackbot|Discordbot|WhatsApp|TelegramBot/i;

export const PAGE_JSON_LD_ID = 'page-jsonld';

export interface FaqItem {
  question: string;
  answer: string;
}

export interface BreadcrumbItem {
  name: string;
  path: string;
}

export const META_DESCRIPTION_MIN_LENGTH = 120;

export const META_DESCRIPTION_MAX_LENGTH = 320;

export const META_TITLE_MIN_LENGTH = 30;

export const META_TITLE_MAX_LENGTH = 65;

export const META_IMAGE_ALT_MAX_LENGTH = 125;

export const DEFAULT_OG_IMAGE_WIDTH = 1200;

export const DEFAULT_OG_IMAGE_HEIGHT = 630;

export interface PageMetaTags {
  title: string;
  description: string;
  canonicalUrl: string;
  ogType?: 'website' | 'article';
  ogImage?: string;
  ogImageAlt?: string;
  siteName?: string;
  noIndex?: boolean;
  jsonLd?: Record<string, unknown> | Record<string, unknown>[];
}

export interface PairAnalysisMetaFields {
  score_100?: number;
  grade?: string;
  verdict?: string;
  issues?: { label: string; ok: boolean }[];
  status?: string;
}

export interface PairAnalysisMetaSource {
  symbol: string;
  exchange: string;
  full_name?: string;
  raw?: {
    fetched_at?: string;
  };
  analysis?: PairAnalysisMetaFields;
}

export function normalizeSiteUrl(siteUrl: string): string {
  return siteUrl.replace(/\/$/, '');
}

export function getSiteUrlFromValue(siteUrlValue: string | undefined): string {
  const trimmed = siteUrlValue?.trim();
  if (!trimmed) {
    return '';
  }
  return normalizeSiteUrl(trimmed);
}

export function resolveWorkerSiteUrl(siteUrlValue: string | undefined, requestOrigin: string): string {
  const configuredSiteUrl = getSiteUrlFromValue(siteUrlValue);
  const requestSiteUrl = normalizeSiteUrl(requestOrigin);
  if (!configuredSiteUrl) {
    return requestSiteUrl;
  }
  try {
    const configuredHost = new URL(configuredSiteUrl).host;
    const requestHost = new URL(requestSiteUrl).host;
    if (configuredHost !== requestHost) {
      return requestSiteUrl;
    }
  } catch {
    return requestSiteUrl;
  }
  return configuredSiteUrl;
}

export function getSiteUrl(): string {
  return getSiteUrlFromValue(import.meta.env.VITE_SITE_URL);
}

export function buildCanonical(siteUrl: string, path: string): string {
  const origin = normalizeSiteUrl(siteUrl);
  if (!origin) {
    return path.startsWith('/') ? path : `/${path}`;
  }
  if (!path || path === '/') {
    return `${origin}/`;
  }
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${origin}${normalizedPath}`;
}

export function buildDefaultOgImage(siteUrl: string): string {
  return buildCanonical(siteUrl, '/og-default.png');
}

export function isDefaultOgImage(ogImage: string): boolean {
  return ogImage.endsWith('/og-default.png');
}

function formatExchangeLabel(exchange: string): string {
  return exchange.toUpperCase();
}

export function buildFailedIssueLabels(
  issues: { label: string; ok: boolean }[] | undefined,
  maxLabels = 3,
): string {
  if (!issues) {
    return '';
  }
  return issues
    .filter((issue) => !issue.ok)
    .map((issue) => getFailedIssueDisplayLabel(issue.label))
    .slice(0, maxLabels)
    .join(', ');
}

function truncateWithEllipsis(text: string, maxLength: number): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLength) {
    return trimmed;
  }
  return `${trimmed.slice(0, maxLength - 1).trimEnd()}…`;
}

export function truncateOgDescription(
  text: string,
  maxLength = META_DESCRIPTION_MAX_LENGTH,
): string {
  return truncateWithEllipsis(text, maxLength);
}

export function finalizeMetaDescription(text: string, minSuffix?: string): string {
  let result = truncateWithEllipsis(text, META_DESCRIPTION_MAX_LENGTH);
  if (result.length < META_DESCRIPTION_MIN_LENGTH && minSuffix) {
    result = truncateWithEllipsis(`${result} ${minSuffix.trim()}`, META_DESCRIPTION_MAX_LENGTH);
  }
  return result;
}

export function finalizeMetaTitle(text: string): string {
  return truncateWithEllipsis(text, META_TITLE_MAX_LENGTH);
}

export function finalizeImageAlt(text: string): string {
  return truncateWithEllipsis(text, META_IMAGE_ALT_MAX_LENGTH);
}

export function buildPairOgTitle(
  pair: string,
  exchange: string,
  analysis: PairAnalysisMetaFields,
): string {
  const exchangeLabel = formatExchangeLabel(exchange);
  let title: string;
  if (analysis.score_100 != null && analysis.grade) {
    title = `${pair}: ${analysis.score_100}/100 (${analysis.grade}) · ${exchangeLabel} · ${SITE_NAME}`;
  } else if (exchange) {
    title = `${pair} · ${exchangeLabel} · ${SITE_NAME}`;
  } else {
    title = `${pair} · ${SITE_NAME}`;
  }
  return finalizeMetaTitle(title);
}

export function buildPairOgDescription(
  pair: string,
  exchange: string,
  analysis: PairAnalysisMetaFields,
): string {
  const exchangeLabel = formatExchangeLabel(exchange);
  const score = analysis.score_100;
  const grade = analysis.grade;
  const failedIssueLabels = buildFailedIssueLabels(analysis.issues);
  const reportSuffix = `Full crypto spot liquidity report on ${exchangeLabel} with spread, depth, slippage, and peer benchmarks from one order-book snapshot.`;

  if (score != null && grade) {
    const structuredDescription = `${pair} on ${exchangeLabel}: crypto liquidity score ${score}/100 (${grade}).`;
    if (failedIssueLabels) {
      return finalizeMetaDescription(`${structuredDescription} ${failedIssueLabels}.`, reportSuffix);
    }
    return finalizeMetaDescription(
      `${structuredDescription} Spread, depth, and slippage from a visible CEX spot order-book snapshot.`,
      reportSuffix,
    );
  }

  const verdict = analysis.verdict?.trim();
  if (verdict) {
    return finalizeMetaDescription(truncateOgDescription(verdict), reportSuffix);
  }

  return finalizeMetaDescription(
    `Crypto liquidity report for ${pair} on ${exchangeLabel}, with spread, depth, slippage checks and a 0–100 score from one visible CEX spot order-book snapshot.`,
  );
}

export function buildPairOgImageAlt(
  pair: string,
  exchange: string,
  analysis: PairAnalysisMetaFields,
): string {
  const exchangeLabel = formatExchangeLabel(exchange);
  if (analysis.score_100 != null && analysis.grade) {
    const statusSuffix = analysis.status ? ` (${analysis.status})` : '';
    return finalizeImageAlt(
      `${pair} liquidity score ${analysis.score_100}/100 (${analysis.grade})${statusSuffix} on ${exchangeLabel}, ${SITE_NAME}`,
    );
  }
  return finalizeImageAlt(`${pair} liquidity report on ${exchangeLabel}, ${SITE_NAME}`);
}

export function parsePairPath(pathname: string): { exchange: string; slug: string } | null {
  const match = pathname.match(/^\/pairs\/([^/]+)\/([^/]+)\/?$/);
  if (!match) {
    return null;
  }
  return { exchange: match[1].toLowerCase(), slug: match[2] };
}

export function isSocialCrawler(userAgent: string | null | undefined): boolean {
  if (!userAgent) {
    return false;
  }
  return SOCIAL_CRAWLER_PATTERN.test(userAgent);
}

export function buildPairMeta(
  siteUrl: string,
  exchange: string,
  slug: string,
  pair: string,
  payload: PairAnalysisMetaSource | null,
): PageMetaTags {
  const canonicalPath = `/pairs/${exchange}/${slug}`;
  const canonicalUrl = buildCanonical(siteUrl, canonicalPath);
  const analysis: PairAnalysisMetaFields = payload?.analysis ?? {};
  const title = buildPairOgTitle(pair, exchange, analysis);
  const description = buildPairOgDescription(pair, exchange, analysis);
  const ogImageAlt = buildPairOgImageAlt(pair, exchange, analysis);
  const score = analysis.score_100;
  const grade = analysis.grade;

  return {
    title,
    description,
    canonicalUrl,
    ogType: 'article',
    ogImage: buildDefaultOgImage(siteUrl),
    ogImageAlt,
    siteName: SITE_NAME,
    jsonLd: buildPairReportJsonLd({
      siteUrl,
      pair,
      exchange,
      pageTitle: title,
      verdict: description,
      score: score ?? null,
      grade: grade ?? null,
      url: canonicalUrl,
      dateModified: payload?.raw?.fetched_at ?? null,
    }),
  };
}

export function buildWebSiteJsonLdNode(siteUrl: string): Record<string, unknown> {
  const origin = normalizeSiteUrl(siteUrl);
  return {
    '@type': 'WebSite',
    '@id': `${origin}/#website`,
    name: SITE_NAME,
    url: `${origin}/`,
    description: DEFAULT_DESCRIPTION,
  };
}

export function buildWebSiteJsonLd(siteUrl: string): Record<string, unknown> {
  return {
    '@context': 'https://schema.org',
    ...buildWebSiteJsonLdNode(siteUrl),
  };
}

export function buildHomePageJsonLd(
  siteUrl: string,
  title: string,
  description: string,
): Record<string, unknown> {
  const canonicalUrl = buildCanonical(siteUrl, '/');
  const webPageJsonLd = buildWebPageJsonLd({
    siteUrl,
    title,
    description,
    url: canonicalUrl,
  });
  const graph = webPageJsonLd['@graph'] as Record<string, unknown>[];
  return {
    '@context': 'https://schema.org',
    '@graph': [buildWebSiteJsonLdNode(siteUrl), ...graph],
  };
}

export function buildWebPageJsonLd(options: {
  siteUrl: string;
  title: string;
  description: string;
  url: string;
  breadcrumbs?: BreadcrumbItem[];
}): Record<string, unknown> {
  const origin = normalizeSiteUrl(options.siteUrl);
  const graph: Record<string, unknown>[] = [
    {
      '@type': 'WebPage',
      '@id': `${options.url}#webpage`,
      url: options.url,
      name: options.title,
      description: options.description,
      isPartOf: { '@id': `${origin}/#website` },
    },
  ];

  if (options.breadcrumbs && options.breadcrumbs.length > 0) {
    graph.push({
      '@type': 'BreadcrumbList',
      '@id': `${options.url}#breadcrumb`,
      itemListElement: options.breadcrumbs.map((crumb, index) => ({
        '@type': 'ListItem',
        position: index + 1,
        name: crumb.name,
        item: buildCanonical(origin, crumb.path),
      })),
    });
  }

  return {
    '@context': 'https://schema.org',
    '@graph': graph,
  };
}

export function buildPairReportJsonLd(options: {
  siteUrl: string;
  pair: string;
  exchange: string;
  pageTitle?: string;
  verdict: string;
  score: number | null;
  grade: string | null;
  url: string;
  dateModified?: string | null;
}): Record<string, unknown> {
  const origin = normalizeSiteUrl(options.siteUrl);
  const exchangeLabel = options.exchange.toUpperCase();
  const headline = `${options.pair} liquidity report on ${exchangeLabel}`;
  const webPage: Record<string, unknown> = {
    '@type': 'WebPage',
    '@id': `${options.url}#webpage`,
    url: options.url,
    name: options.pageTitle ?? headline,
    description: options.verdict,
    isPartOf: { '@id': `${origin}/#website` },
  };
  if (options.dateModified) {
    webPage.dateModified = options.dateModified;
  }

  return {
    '@context': 'https://schema.org',
    '@graph': [
      webPage,
      {
        '@type': 'BreadcrumbList',
        '@id': `${options.url}#breadcrumb`,
        itemListElement: [
          {
            '@type': 'ListItem',
            position: 1,
            name: 'Home',
            item: `${origin}/`,
          },
          {
            '@type': 'ListItem',
            position: 2,
            name: 'Token rankings',
            item: `${origin}/`,
          },
          {
            '@type': 'ListItem',
            position: 3,
            name: `${options.pair} on ${exchangeLabel}`,
            item: options.url,
          },
        ],
      },
    ],
  };
}

export function buildFaqPageJsonLd(faqs: FaqItem[], pageUrl?: string): Record<string, unknown> {
  const faqPage: Record<string, unknown> = {
    '@type': 'FAQPage',
    mainEntity: faqs.map((faq) => ({
      '@type': 'Question',
      name: faq.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: faq.answer,
      },
    })),
  };
  if (pageUrl) {
    faqPage['@id'] = `${pageUrl}#faq`;
  }
  return faqPage;
}

function mergeWebPageAndFaqJsonLd(
  webPageJsonLd: Record<string, unknown>,
  faqs?: FaqItem[],
  pageUrl?: string,
): Record<string, unknown> {
  if (!faqs || faqs.length === 0) {
    return webPageJsonLd;
  }
  const graph = webPageJsonLd['@graph'] as Record<string, unknown>[];
  return {
    '@context': 'https://schema.org',
    '@graph': [...graph, buildFaqPageJsonLd(faqs, pageUrl)],
  };
}

export function buildStaticPageMeta(
  siteUrl: string,
  pageKey: keyof typeof PAGE_META,
  path: string,
  pageLabel: string,
  options?: { faqs?: FaqItem[] },
): PageMetaTags {
  const page = PAGE_META[pageKey];
  const canonicalUrl = buildCanonical(siteUrl, path);
  const title = finalizeMetaTitle(page.title);
  const description = finalizeMetaDescription(page.description);
  const webPageJsonLd = buildWebPageJsonLd({
    siteUrl,
    title,
    description,
    url: canonicalUrl,
    breadcrumbs: [
      { name: 'Home', path: '/' },
      { name: pageLabel, path },
    ],
  });
  return {
    title,
    description,
    canonicalUrl,
    ogType: 'website',
    ogImage: buildDefaultOgImage(siteUrl),
    ogImageAlt: DEFAULT_OG_IMAGE_ALT,
    siteName: SITE_NAME,
    jsonLd: mergeWebPageAndFaqJsonLd(webPageJsonLd, options?.faqs, canonicalUrl),
  };
}

export function buildHomePageMeta(siteUrl: string): PageMetaTags {
  const canonicalUrl = buildCanonical(siteUrl, '/');
  const title = finalizeMetaTitle(PAGE_META.home.title);
  const description = finalizeMetaDescription(PAGE_META.home.description);
  return {
    title,
    description,
    canonicalUrl,
    ogType: 'website',
    ogImage: buildDefaultOgImage(siteUrl),
    ogImageAlt: DEFAULT_OG_IMAGE_ALT,
    siteName: SITE_NAME,
    jsonLd: buildHomePageJsonLd(siteUrl, title, description),
  };
}

function escapeHtmlAttribute(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function serializeJsonLd(jsonLd: Record<string, unknown> | Record<string, unknown>[]): string {
  return JSON.stringify(jsonLd).replace(/</g, '\\u003c');
}

/** Remove shell defaults so injected pair/page meta is the only title, OG, and JSON-LD in the document. */
export function stripManagedHeadTags(html: string): string {
  return html
    .replace(/<title>[\s\S]*?<\/title>\s*/gi, '')
    .replace(/<meta\s+name="description"[\s\S]*?\/>\s*/gi, '')
    .replace(/<meta\s+name="robots"[\s\S]*?\/>\s*/gi, '')
    .replace(/<link\s+rel="canonical"[\s\S]*?\/>\s*/gi, '')
    .replace(/<meta\s+property="og:[^"]*"[\s\S]*?\/>\s*/gi, '')
    .replace(/<meta\s+name="twitter:[^"]*"[\s\S]*?\/>\s*/gi, '')
    .replace(/<script\s+type="application\/ld\+json"[\s\S]*?<\/script>\s*/gi, '');
}

export function injectMetaTags(html: string, meta: PageMetaTags): string {
  const siteName = meta.siteName ?? SITE_NAME;
  const ogType = meta.ogType ?? 'website';
  const ogImage = meta.ogImage ?? buildDefaultOgImage(meta.canonicalUrl);
  const robotsContent = meta.noIndex ? 'noindex, nofollow' : 'index, follow';

  const tags = [
    `<title>${escapeHtmlAttribute(meta.title)}</title>`,
    `<meta name="description" content="${escapeHtmlAttribute(meta.description)}" />`,
    `<meta name="robots" content="${robotsContent}" />`,
    `<link rel="canonical" href="${escapeHtmlAttribute(meta.canonicalUrl)}" />`,
    `<meta property="og:title" content="${escapeHtmlAttribute(meta.title)}" />`,
    `<meta property="og:description" content="${escapeHtmlAttribute(meta.description)}" />`,
    `<meta property="og:url" content="${escapeHtmlAttribute(meta.canonicalUrl)}" />`,
    `<meta property="og:type" content="${ogType}" />`,
    `<meta property="og:image" content="${escapeHtmlAttribute(ogImage)}" />`,
    `<meta property="og:site_name" content="${escapeHtmlAttribute(siteName)}" />`,
    `<meta name="twitter:card" content="summary_large_image" />`,
    `<meta name="twitter:title" content="${escapeHtmlAttribute(meta.title)}" />`,
    `<meta name="twitter:description" content="${escapeHtmlAttribute(meta.description)}" />`,
    `<meta name="twitter:image" content="${escapeHtmlAttribute(ogImage)}" />`,
  ];

  if (isDefaultOgImage(ogImage)) {
    tags.push(
      `<meta property="og:image:width" content="${DEFAULT_OG_IMAGE_WIDTH}" />`,
      `<meta property="og:image:height" content="${DEFAULT_OG_IMAGE_HEIGHT}" />`,
    );
  }

  if (meta.ogImageAlt) {
    tags.push(
      `<meta property="og:image:alt" content="${escapeHtmlAttribute(meta.ogImageAlt)}" />`,
      `<meta name="twitter:image:alt" content="${escapeHtmlAttribute(meta.ogImageAlt)}" />`,
    );
  }

  if (meta.jsonLd) {
    tags.push(
      `<script id="${PAGE_JSON_LD_ID}" type="application/ld+json">${serializeJsonLd(meta.jsonLd)}</script>`,
    );
  }

  const injectionBlock = tags.join('\n    ');
  const htmlWithoutManagedTags = stripManagedHeadTags(html);
  if (htmlWithoutManagedTags.includes('</head>')) {
    return htmlWithoutManagedTags.replace('</head>', `    ${injectionBlock}\n  </head>`);
  }
  return htmlWithoutManagedTags;
}
