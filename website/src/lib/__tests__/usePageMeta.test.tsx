import { describe, expect, it } from 'vitest';
import { render } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { applyPageMetaToDocument } from '../applyPageMeta';
import { buildHomePageMeta } from '../siteMeta';
import { usePageMeta } from '../usePageMeta';

function MetaProbe() {
  usePageMeta({
    title: 'Test title',
    description: 'Test description for SEO',
    jsonLd: { '@context': 'https://schema.org', '@type': 'WebPage', name: 'Test title' },
  });
  return null;
}

describe('applyPageMetaToDocument', () => {
  it('updates description and open graph tags', () => {
    applyPageMetaToDocument(buildHomePageMeta('https://example.com'));
    expect(document.title).toBe('Token Liquidity Ranking · Crypto Liquidity Audit');
    expect(document.querySelector('meta[name="description"]')?.getAttribute('content')).toBe(
      buildHomePageMeta('https://example.com').description,
    );
    expect(document.querySelector('meta[property="og:title"]')?.getAttribute('content')).toBe(
      'Token Liquidity Ranking · Crypto Liquidity Audit',
    );
  });
});

describe('usePageMeta', () => {
  it('injects route json-ld script', () => {
    render(
      <MemoryRouter>
        <MetaProbe />
      </MemoryRouter>,
    );
    const jsonLdScript = document.getElementById('page-jsonld');
    expect(jsonLdScript?.textContent).toContain('"@type":"WebPage"');
    expect(document.querySelector('meta[name="twitter:description"]')?.getAttribute('content')).toBe(
      'Test description for SEO',
    );
  });
});
