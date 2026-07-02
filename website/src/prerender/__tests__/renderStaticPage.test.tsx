import { describe, expect, it } from 'vitest';
import { renderStaticPage } from '../renderStaticPage';

describe('renderStaticPage', () => {
  it('renders methodology heading markup for crawlers', async () => {
    const { appHtml, hydrationData } = await renderStaticPage('/methodology');
    expect(appHtml).toContain('<h1');
    expect(appHtml).toContain('Methodology');
    expect(appHtml).toContain('https://github.com/Drakkar-Software/Liquidity-Audit');
    expect((appHtml.match(/<h2/g) ?? []).length).toBeGreaterThanOrEqual(2);
    expect(hydrationData.loaderData).toBeDefined();
  });

  it('renders about page with H1 and multiple H2 tags', async () => {
    const { appHtml } = await renderStaticPage('/about');
    expect(appHtml).toContain('<h1');
    expect(appHtml).toContain('Independent crypto liquidity analysis');
    expect((appHtml.match(/<h2/g) ?? []).length).toBeGreaterThanOrEqual(2);
  });

  it('renders learn page with H1 and multiple H2 tags', async () => {
    const { appHtml } = await renderStaticPage('/learn');
    expect(appHtml).toContain('<h1');
    expect(appHtml).toContain('Crypto liquidity terms');
    expect((appHtml.match(/<h2/g) ?? []).length).toBeGreaterThanOrEqual(2);
  });

  it('renders crypto liquidity pillar page markup', async () => {
    const { appHtml } = await renderStaticPage('/crypto-liquidity');
    expect(appHtml).toContain('<h1');
    expect(appHtml).toMatch(/Crypto liquidity/i);
  });

  it('renders home static shell with skeleton placeholders', async () => {
    const { appHtml } = await renderStaticPage('/');
    expect(appHtml).toContain('Token Liquidity Ranking');
    expect(appHtml).toContain('data-testid="rankings-table-skeleton"');
    expect(appHtml).toContain('data-testid="quick-links-skeleton"');
    expect(appHtml).not.toContain('ETH/USDT');
  });
});
