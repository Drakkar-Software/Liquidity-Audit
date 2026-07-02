import type { ReactElement } from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { About } from '../About';
import { Learn } from '../Learn';
import { CaseStudies } from '../CaseStudies';
import { Comparison } from '../Comparison';
import { CryptoLiquidity } from '../CryptoLiquidity';
import { OrderBookAnalysis } from '../OrderBookAnalysis';
import { BidAskSpread } from '../BidAskSpread';
import { LiquidityScore } from '../LiquidityScore';
import { Methodology } from '../Methodology';
import { xyzViewModel } from '../../lib/data/samples';
import { TokenReport } from '../TokenReport';
import type { RankingsViewModel } from '../../types';

function renderPage(ui: ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

function expectSingleH1(): HTMLElement {
  const headings = screen.getAllByRole('heading', { level: 1 });
  expect(headings).toHaveLength(1);
  return headings[0];
}

function expectAtLeastTwoH2s(): void {
  expect(screen.getAllByRole('heading', { level: 2 }).length).toBeGreaterThanOrEqual(2);
}

function expectCryptoKeywordInHeadings(): void {
  const headingText = screen
    .getAllByRole('heading')
    .map((heading) => heading.textContent ?? '')
    .join(' ');
  expect(headingText.toLowerCase()).toMatch(/crypto|token|spot|order book|bid|liquidity score/);
}

const rankings: RankingsViewModel = {
  exchange: 'mexc',
  exchangeLabel: 'MEXC',
  updatedLabel: '2h ago',
  rows: [{ symbol: 'SOL/USDT', score: 80, vol: '1.2M', rank: 1 }],
};

describe('SEO heading hierarchy', () => {
  it('About has one H1 and crypto-specific H2 sections', () => {
    renderPage(<About />);
    expectSingleH1();
    expect(screen.getByRole('heading', { level: 1, name: 'Independent crypto liquidity analysis' })).toBeInTheDocument();
    expectAtLeastTwoH2s();
    expectCryptoKeywordInHeadings();
  });

  it('Learn has one H1 and glossary H2 sections', () => {
    renderPage(<Learn />);
    expectSingleH1();
    expect(screen.getByRole('heading', { level: 1, name: 'Crypto liquidity terms' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Crypto liquidity report glossary' })).toBeInTheDocument();
    expectAtLeastTwoH2s();
  });

  it('Case studies has one H1 and per-case H2 headings', () => {
    renderPage(<CaseStudies />);
    expectSingleH1();
    expect(screen.getByRole('heading', { level: 1, name: 'Crypto liquidity case studies' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: '90-day crypto liquidity recovery' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: '60-day spread and depth improvement' })).toBeInTheDocument();
  });

  it('Home comparison has one H1 and multiple H2 sections', () => {
    renderPage(
      <Comparison
        rankings={rankings}
        exchange="mexc"
        pairCatalog={['SOL/USDT']}
        onExchangeChange={() => {}}
        onOpenReport={() => {}}
      />,
    );
    expectSingleH1();
    expect(screen.getByRole('heading', { level: 2, name: 'Crypto spot liquidity rankings' })).toBeInTheDocument();
    expectAtLeastTwoH2s();
  });

  it('Methodology has one H1 and multiple H2 sections', () => {
    renderPage(<Methodology />);
    expectSingleH1();
    expectAtLeastTwoH2s();
  });

  it.each([
    { name: 'Crypto liquidity', component: <CryptoLiquidity /> },
    { name: 'Order book analysis', component: <OrderBookAnalysis /> },
    { name: 'Bid-ask spread', component: <BidAskSpread /> },
    { name: 'Liquidity score', component: <LiquidityScore /> },
  ])('$name pillar has one H1 and at least two H2s', ({ component }) => {
    renderPage(component);
    expectSingleH1();
    expectAtLeastTwoH2s();
    expectCryptoKeywordInHeadings();
  });

  it('Token report has one H1 and section H2 headings', () => {
    renderPage(<TokenReport vm={xyzViewModel} />);
    const pageTitle = screen.getByRole('heading', {
      level: 1,
      name: 'XYZ/USDT crypto liquidity report',
    });
    expect(pageTitle).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1);
    const sectionHeadings = screen.getAllByRole('heading', { level: 2 });
    expect(sectionHeadings.length).toBeGreaterThanOrEqual(2);
    expect(within(document.body).getByRole('heading', { level: 2, name: /Health dashboard/i })).toBeInTheDocument();
  });
});
