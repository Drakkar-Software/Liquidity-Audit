import { describe, expect, it } from 'vitest';
import pairAnalysisSample from '../../test/fixtures/pair-analysis.sample.json';
import {
  buildCanonical,
  buildDefaultOgImage,
  buildFailedIssueLabels,
  buildFaqPageJsonLd,
  buildHomePageJsonLd,
  buildHomePageMeta,
  buildPairMeta,
  buildPairOgDescription,
  buildPairOgImageAlt,
  buildPairOgTitle,
  buildPairReportJsonLd,
  buildStaticPageMeta,
  buildWebSiteJsonLd,
  DEFAULT_DESCRIPTION,
  DEFAULT_OG_IMAGE_ALT,
  finalizeMetaTitle,
  injectMetaTags,
  isSocialCrawler,
  META_DESCRIPTION_MAX_LENGTH,
  META_DESCRIPTION_MIN_LENGTH,
  META_IMAGE_ALT_MAX_LENGTH,
  META_TITLE_MIN_LENGTH,
  META_TITLE_MAX_LENGTH,
  PAGE_META,
  parsePairPath,
  resolveWorkerSiteUrl,
  SITE_NAME,
  truncateOgDescription,
} from '../siteMeta';
import type { PairAnalysisMetaFields, PairAnalysisMetaSource } from '../siteMeta';

const sampleAnalysis = (pairAnalysisSample as PairAnalysisMetaSource).analysis as PairAnalysisMetaFields;

function assertValidJsonLdGraph(jsonLd: Record<string, unknown>): void {
  expect(jsonLd['@context']).toBe('https://schema.org');
  const graph = jsonLd['@graph'] as Record<string, unknown>[] | undefined;
  if (graph) {
    for (const node of graph) {
      expect(node['@type']).toBeTruthy();
    }
    expect(JSON.parse(JSON.stringify(jsonLd))).toBeTruthy();
    return;
  }
  expect(jsonLd['@type']).toBeTruthy();
  expect(JSON.parse(JSON.stringify(jsonLd))).toBeTruthy();
}

describe('PAGE_META descriptions', () => {
  it('keeps every static description between 120 and 320 characters', () => {
    const descriptions = [
      DEFAULT_DESCRIPTION,
      ...Object.values(PAGE_META).map((page) => page.description),
    ];
    for (const description of descriptions) {
      expect(description.length).toBeGreaterThanOrEqual(META_DESCRIPTION_MIN_LENGTH);
      expect(description.length).toBeLessThanOrEqual(META_DESCRIPTION_MAX_LENGTH);
    }
  });
});

describe('PAGE_META titles', () => {
  it('keeps every static title between 30 and 65 characters', () => {
    for (const page of Object.values(PAGE_META)) {
      const titleLength = finalizeMetaTitle(page.title).length;
      expect(titleLength).toBeGreaterThanOrEqual(META_TITLE_MIN_LENGTH);
      expect(titleLength).toBeLessThanOrEqual(META_TITLE_MAX_LENGTH);
    }
  });
});

describe('DEFAULT_OG_IMAGE_ALT', () => {
  it('is non-empty and within the alt text limit', () => {
    expect(DEFAULT_OG_IMAGE_ALT.length).toBeGreaterThan(0);
    expect(DEFAULT_OG_IMAGE_ALT.length).toBeLessThanOrEqual(META_IMAGE_ALT_MAX_LENGTH);
  });
});

describe('resolveWorkerSiteUrl', () => {
  it('uses request origin when configured site url host differs', () => {
    expect(
      resolveWorkerSiteUrl(
        'https://liquidity-analysis.example.workers.dev',
        'https://liquidity-analysis.octobot.workers.dev',
      ),
    ).toBe('https://liquidity-analysis.octobot.workers.dev');
  });

  it('keeps configured site url when host matches request origin', () => {
    expect(
      resolveWorkerSiteUrl(
        'https://liquidity-analysis.octobot.workers.dev',
        'https://liquidity-analysis.octobot.workers.dev',
      ),
    ).toBe('https://liquidity-analysis.octobot.workers.dev');
  });
});

describe('parsePairPath', () => {
  it('parses pair report paths', () => {
    expect(parsePairPath('/pairs/mexc/XYZ_USDT')).toEqual({
      exchange: 'mexc',
      slug: 'XYZ_USDT',
    });
  });

  it('returns null for non-pair paths', () => {
    expect(parsePairPath('/methodology')).toBeNull();
  });
});

describe('isSocialCrawler', () => {
  it('detects common social bot user agents', () => {
    expect(isSocialCrawler('facebookexternalhit/1.1')).toBe(true);
    expect(isSocialCrawler('Twitterbot/1.0')).toBe(true);
    expect(isSocialCrawler('Mozilla/5.0 Chrome/120')).toBe(false);
  });
});

describe('buildCanonical', () => {
  it('builds absolute canonical URLs', () => {
    expect(buildCanonical('https://example.com', '/about')).toBe('https://example.com/about');
    expect(buildCanonical('https://example.com/', '/')).toBe('https://example.com/');
  });
});

describe('buildDefaultOgImage', () => {
  it('points at the default PNG asset', () => {
    expect(buildDefaultOgImage('https://example.com')).toBe('https://example.com/og-default.png');
  });
});

describe('buildFailedIssueLabels', () => {
  it('returns lowercased failed issue labels up to the limit', () => {
    expect(buildFailedIssueLabels(sampleAnalysis.issues)).toBe(
      'wide spread, thin depth, high slippage',
    );
  });
});

describe('truncateOgDescription', () => {
  it('truncates long text with an ellipsis', () => {
    const longText = 'x'.repeat(META_DESCRIPTION_MAX_LENGTH + 10);
    expect(truncateOgDescription(longText)).toHaveLength(META_DESCRIPTION_MAX_LENGTH);
    expect(truncateOgDescription(longText).endsWith('…')).toBe(true);
  });
});

describe('buildPairOgTitle', () => {
  it('includes score, grade, and exchange when available', () => {
    expect(buildPairOgTitle('XYZ/USDT', 'mexc', sampleAnalysis)).toBe(
      'XYZ/USDT: 42/100 (D) · MEXC · Crypto Liquidity Audit',
    );
  });

  it('falls back to pair and site name when score is missing', () => {
    expect(buildPairOgTitle('XYZ/USDT', '', {})).toBe('XYZ/USDT · Crypto Liquidity Audit');
  });
});

describe('finalizeMetaTitle', () => {
  it('truncates long pair titles with an ellipsis', () => {
    const longPairTitle = buildPairOgTitle(
      'EXTREMELYLONGTOKENNAMEFORTESTING/USDT',
      'mexc',
      { score_100: 42, grade: 'D' },
    );
    expect(longPairTitle.length).toBeLessThanOrEqual(META_TITLE_MAX_LENGTH);
    expect(longPairTitle.endsWith('…')).toBe(true);
  });
});

describe('buildPairOgDescription', () => {
  it('prefers structured copy with failed issues over the full verdict', () => {
    const description = buildPairOgDescription('XYZ/USDT', 'mexc', sampleAnalysis);
    expect(description).toContain('crypto liquidity score 42/100 (D)');
    expect(description).toContain('wide spread, thin depth, high slippage');
    expect(description).not.toContain('8× worse');
    expect(description.length).toBeGreaterThanOrEqual(META_DESCRIPTION_MIN_LENGTH);
    expect(description.length).toBeLessThanOrEqual(META_DESCRIPTION_MAX_LENGTH);
  });

  it('enriches score-only copy to meet the minimum description length', () => {
    const description = buildPairOgDescription('USDC/USDT', 'mexc', {
      score_100: 100,
      grade: 'A',
      issues: [{ label: 'Good volume', ok: true }],
    });
    expect(description).toContain('crypto liquidity score 100/100 (A)');
    expect(description).toContain('order-book snapshot');
    expect(description.length).toBeGreaterThanOrEqual(META_DESCRIPTION_MIN_LENGTH);
  });

  it('appends exchange context when a short verdict is under the minimum', () => {
    const description = buildPairOgDescription('XYZ/USDT', 'mexc', {
      verdict: 'Wide spread on this pair.',
    });
    expect(description).toContain('Full crypto spot liquidity report on MEXC');
    expect(description.length).toBeGreaterThanOrEqual(META_DESCRIPTION_MIN_LENGTH);
  });

  it('uses truncated verdict when score is unavailable', () => {
    const description = buildPairOgDescription('XYZ/USDT', 'mexc', {
      verdict: 'x'.repeat(META_DESCRIPTION_MAX_LENGTH + 20),
    });
    expect(description.endsWith('…')).toBe(true);
    expect(description.length).toBeLessThanOrEqual(META_DESCRIPTION_MAX_LENGTH);
  });
});

describe('buildPairOgImageAlt', () => {
  it('describes score and exchange for accessible preview text', () => {
    expect(buildPairOgImageAlt('XYZ/USDT', 'mexc', { score_100: 42, grade: 'D' })).toBe(
      'XYZ/USDT liquidity score 42/100 (D) on MEXC, Crypto Liquidity Audit',
    );
    expect(buildPairOgImageAlt('XYZ/USDT', 'mexc', { score_100: 42, grade: 'D' }).length).toBeLessThanOrEqual(
      META_IMAGE_ALT_MAX_LENGTH,
    );
  });

  it('includes status when available', () => {
    expect(
      buildPairOgImageAlt('XYZ/USDT', 'mexc', { ...sampleAnalysis, status: 'Poor' }),
    ).toContain('(Poor)');
  });
});

describe('buildWebSiteJsonLd', () => {
  it('includes website name without a search action', () => {
    const jsonLd = buildWebSiteJsonLd('https://example.com');
    expect(jsonLd['@type']).toBe('WebSite');
    expect(jsonLd.name).toBe(SITE_NAME);
    expect(jsonLd.description).toBe(DEFAULT_DESCRIPTION);
    expect(jsonLd.potentialAction).toBeUndefined();
  });
});

describe('buildHomePageJsonLd', () => {
  it('includes WebSite and WebPage nodes in the graph', () => {
    const jsonLd = buildHomePageJsonLd(
      'https://example.com',
      'Token Liquidity Ranking · Crypto Liquidity Audit',
      DEFAULT_DESCRIPTION,
    );
    assertValidJsonLdGraph(jsonLd);
    const graph = jsonLd['@graph'] as Record<string, unknown>[];
    expect(graph.some((node) => node['@type'] === 'WebSite')).toBe(true);
    expect(graph.some((node) => node['@type'] === 'WebPage')).toBe(true);
  });
});

describe('buildPairReportJsonLd', () => {
  it('escapes verdict text in serialized output', () => {
    const jsonLd = buildPairReportJsonLd({
      siteUrl: 'https://example.com',
      pair: 'XYZ/USDT',
      exchange: 'mexc',
      verdict: 'Score < 50 & "wide" spread',
      score: 42,
      grade: 'D',
      url: 'https://example.com/pairs/mexc/XYZ_USDT',
      dateModified: '2026-06-14T18:30:00+00:00',
    });
    const serialized = JSON.stringify(jsonLd);
    expect(serialized).toContain('Score < 50 & \\"wide\\" spread');
    expect(serialized).toContain('BreadcrumbList');
  });

  it('uses the provided page title for WebPage name', () => {
    const jsonLd = buildPairReportJsonLd({
      siteUrl: 'https://example.com',
      pair: 'XYZ/USDT',
      exchange: 'mexc',
      pageTitle: 'XYZ/USDT: 42/100 (D) · MEXC · Crypto Liquidity Audit',
      verdict: 'Short description',
      score: 42,
      grade: 'D',
      url: 'https://example.com/pairs/mexc/XYZ_USDT',
    });
    const graph = (jsonLd['@graph'] as Record<string, unknown>[])[0];
    expect(graph.name).toBe('XYZ/USDT: 42/100 (D) · MEXC · Crypto Liquidity Audit');
  });
});

describe('buildPairMeta', () => {
  it('maps pair analysis payload into page meta', () => {
    const meta = buildPairMeta(
      'https://example.com',
      'mexc',
      'XYZ_USDT',
      'XYZ/USDT',
      pairAnalysisSample as PairAnalysisMetaSource,
    );
    expect(meta.title).toBe('XYZ/USDT: 42/100 (D) · MEXC · Crypto Liquidity Audit');
    expect(meta.description).toContain('crypto liquidity score 42/100 (D)');
    expect(meta.description).toContain('wide spread');
    expect(meta.ogImage).toBe('https://example.com/og-default.png');
    expect(meta.ogImageAlt).toContain('42/100 (D)');
    expect(meta.canonicalUrl).toBe('https://example.com/pairs/mexc/XYZ_USDT');
    expect(meta.jsonLd).toBeDefined();
  });

  it('uses generic copy when payload is missing', () => {
    const meta = buildPairMeta('https://example.com', 'mexc', 'XYZ_USDT', 'XYZ/USDT', null);
    expect(meta.title).toBe('XYZ/USDT · MEXC · Crypto Liquidity Audit');
    expect(meta.description).toContain('Crypto liquidity report for XYZ/USDT on MEXC');
    expect(meta.description.length).toBeGreaterThanOrEqual(META_DESCRIPTION_MIN_LENGTH);
    expect(meta.description.length).toBeLessThanOrEqual(META_DESCRIPTION_MAX_LENGTH);
  });
});

describe('buildHomePageMeta', () => {
  it('includes website and webpage json-ld and default image alt', () => {
    const meta = buildHomePageMeta('https://example.com');
    assertValidJsonLdGraph(meta.jsonLd as Record<string, unknown>);
    const graph = (meta.jsonLd as Record<string, unknown>)['@graph'] as Record<string, unknown>[];
    expect(graph.some((node) => node['@type'] === 'WebSite')).toBe(true);
    expect(graph.some((node) => node['@type'] === 'WebPage')).toBe(true);
    expect(meta.ogImage).toBe('https://example.com/og-default.png');
    expect(meta.ogImageAlt).toBe(DEFAULT_OG_IMAGE_ALT);
    expect(meta.title).toBe('Token Liquidity Ranking · Crypto Liquidity Audit');
  });
});

describe('buildFaqPageJsonLd', () => {
  it('maps questions and answers into FAQPage schema', () => {
    const jsonLd = buildFaqPageJsonLd([
      { question: 'What is a liquidity score?', answer: 'A 0–100 grade from one snapshot.' },
    ]);
    expect(jsonLd['@type']).toBe('FAQPage');
    const mainEntity = jsonLd.mainEntity as Record<string, unknown>[];
    expect(mainEntity[0]).toMatchObject({
      '@type': 'Question',
      name: 'What is a liquidity score?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'A 0–100 grade from one snapshot.',
      },
    });
  });
});

describe('buildStaticPageMeta', () => {
  it('includes default image alt for static pages', () => {
    const meta = buildStaticPageMeta('https://example.com', 'methodology', '/methodology', 'Methodology');
    expect(meta.ogImageAlt).toBe(DEFAULT_OG_IMAGE_ALT);
    expect(meta.description.length).toBeGreaterThanOrEqual(META_DESCRIPTION_MIN_LENGTH);
  });

  it('merges FAQ schema into the page json-ld graph with an @id', () => {
    const meta = buildStaticPageMeta('https://example.com', 'methodology', '/methodology', 'Methodology', {
      faqs: [{ question: 'How do you measure liquidity?', answer: 'Spread, depth, and slippage.' }],
    });
    const graph = (meta.jsonLd as Record<string, unknown>)['@graph'] as Record<string, unknown>[];
    const faqNode = graph.find((node) => node['@type'] === 'FAQPage');
    expect(faqNode).toBeDefined();
    expect(faqNode?.['@id']).toBe('https://example.com/methodology#faq');
    assertValidJsonLdGraph(meta.jsonLd as Record<string, unknown>);
  });

  it('includes pillar page meta keys', () => {
    const meta = buildStaticPageMeta(
      'https://example.com',
      'cryptoLiquidity',
      '/crypto-liquidity',
      'Crypto liquidity',
    );
    expect(meta.title).toContain('Crypto Liquidity');
    expect(meta.canonicalUrl).toBe('https://example.com/crypto-liquidity');
  });
});

describe('injectMetaTags', () => {
  it('injects meta, canonical, json-ld, and default image alt before head close', () => {
    const html = '<!DOCTYPE html><html><head><title>Old</title></head><body></body></html>';
    const output = injectMetaTags(html, buildHomePageMeta('https://example.com'));
    expect(output).toContain(
      '<meta property="og:title" content="Token Liquidity Ranking · Crypto Liquidity Audit" />',
    );
    expect(output).toContain('<link rel="canonical" href="https://example.com/" />');
    expect(output).toContain('application/ld+json');
    expect(output).toContain('"@type":"WebSite"');
    expect(output).toContain('"@type":"WebPage"');
    expect(output).toContain('<meta property="og:image" content="https://example.com/og-default.png" />');
    expect(output).toContain('<meta property="og:image:width" content="1200" />');
    expect(output).toContain('<meta property="og:image:height" content="630" />');
    expect(output).toContain('property="og:image:alt"');
    expect(output).toContain(DEFAULT_OG_IMAGE_ALT);
  });

  it('replaces shell default meta so crawlers see a single og:title', () => {
    const shellHtml = `<!DOCTYPE html><html><head>
    <title>Crypto Liquidity Audit</title>
    <meta property="og:title" content="Crypto Liquidity Audit" />
    <meta property="og:description" content="Generic site description." />
    <meta property="og:url" content="https://example.com/" />
    <script type="application/ld+json">{"@type":"WebSite"}</script>
    </head><body></body></html>`;
    const meta = buildPairMeta(
      'https://example.com',
      'mexc',
      'USDC_USDT',
      'USDC/USDT',
      {
        symbol: 'USDC/USDT',
        exchange: 'mexc',
        analysis: { score_100: 100, grade: 'A' },
      },
    );
    const output = injectMetaTags(shellHtml, meta);
    expect(output.match(/property="og:title"/g)).toHaveLength(1);
    expect(output).toContain('USDC/USDT: 100/100 (A) · MEXC · Crypto Liquidity Audit');
    expect(output).not.toContain('property="og:title" content="Token Liquidity Rankings');
    expect(output).not.toContain('Generic site description');
    expect(output).not.toContain('"@type":"WebSite"');
    expect(output).toContain('property="og:image:alt"');
  });

  it('injects pair image alt text and escapes unsafe characters', () => {
    const meta = buildPairMeta(
      'https://example.com',
      'mexc',
      'ABC/USDT',
      'ABC/USDT',
      {
        symbol: 'ABC/USDT',
        exchange: 'mexc',
        analysis: {
          score_100: 25,
          grade: 'F',
          verdict: 'Score < 50 & "wide" spread',
        },
      },
    );
    const output = injectMetaTags('<!DOCTYPE html><html><head></head><body></body></html>', meta);
    expect(output).toContain('property="og:image:alt"');
    expect(output).toContain('name="twitter:image:alt"');
    expect(output).toContain('25/100 (F)');
    expect(output).not.toContain('content="Score < 50');
  });
});
