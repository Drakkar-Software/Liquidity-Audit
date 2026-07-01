import { describe, expect, it } from 'vitest';
import { METHODOLOGY_FAQS } from '../methodologyFaqs';
import { STATIC_MARKETING_PATHS, STATIC_PRERENDER_PAGES } from '../staticPrerenderPages';

describe('STATIC_PRERENDER_PAGES', () => {
  it('lists eight static marketing routes', () => {
    expect(STATIC_PRERENDER_PAGES).toHaveLength(8);
    expect(STATIC_MARKETING_PATHS).toEqual(STATIC_PRERENDER_PAGES.map((page) => page.path));
  });

  it('includes methodology FAQs for JSON-LD', () => {
    const methodologyPage = STATIC_PRERENDER_PAGES.find((page) => page.path === '/methodology');
    expect(methodologyPage?.faqs).toBe(METHODOLOGY_FAQS);
    expect(methodologyPage?.faqs?.length).toBeGreaterThan(0);
  });
});
