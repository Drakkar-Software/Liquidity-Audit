import type { ReactElement } from 'react';
import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CryptoLiquidity } from '../CryptoLiquidity';
import { OrderBookAnalysis } from '../OrderBookAnalysis';
import { BidAskSpread } from '../BidAskSpread';
import { LiquidityScore } from '../LiquidityScore';

const TIER_A_BANNED = /\b(leverage|delve|embark|harness|foster|utilize|underscore|moreover|furthermore|additionally)\b/i;

function renderPillar(ui: ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

const PILLAR_PAGES = [
  { name: 'Crypto liquidity', component: CryptoLiquidity },
  { name: 'Order book analysis', component: OrderBookAnalysis },
  { name: 'Bid-ask spread', component: BidAskSpread },
  { name: 'Liquidity score', component: LiquidityScore },
] as const;

describe('CryptoLiquidity', () => {
  it('renders the natural title as H1', () => {
    renderPillar(<CryptoLiquidity />);
    expect(screen.getByRole('heading', { level: 1, name: 'Crypto liquidity' })).toBeInTheDocument();
  });

  it('does not show the market-making footer note', () => {
    renderPillar(<CryptoLiquidity />);
    expect(screen.queryByText(/crypto market making automation/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/liquidity provider crypto/i)).not.toBeInTheDocument();
  });
});

describe('OrderBookAnalysis', () => {
  it('renders the natural title as H1', () => {
    renderPillar(<OrderBookAnalysis />);
    expect(screen.getByRole('heading', { level: 1, name: 'Order book analysis' })).toBeInTheDocument();
  });

  it('renders related guide cards', () => {
    renderPillar(<OrderBookAnalysis />);
    const relatedHeading = screen.getByRole('heading', { level: 2, name: 'Related guides' });
    const relatedSection = relatedHeading.parentElement as HTMLElement;
    expect(within(relatedSection).getByRole('link', { name: /Crypto liquidity/i })).toHaveClass(
      'guide-card-link',
    );
  });
});

describe('BidAskSpread', () => {
  it('renders the natural title as H1', () => {
    renderPillar(<BidAskSpread />);
    expect(screen.getByRole('heading', { level: 1, name: 'Bid-ask spread' })).toBeInTheDocument();
  });
});

describe('LiquidityScore', () => {
  it('renders the natural title as H1', () => {
    renderPillar(<LiquidityScore />);
    expect(screen.getByRole('heading', { level: 1, name: 'Liquidity score' })).toBeInTheDocument();
  });
});

describe('pillar example sections', () => {
  it.each(PILLAR_PAGES)('renders an Example section with numeric copy on $name', ({ component: PillarComponent }) => {
    renderPillar(<PillarComponent />);
    const exampleSection = document.querySelector('.pillar-example') as HTMLElement;
    expect(exampleSection).not.toBeNull();
    const exampleHeading = within(exampleSection).getByRole('heading', { level: 2, name: 'Example' });
    expect(exampleHeading).toBeInTheDocument();
    const exampleCopy = within(exampleSection).getByRole('paragraph');
    expect(exampleCopy.textContent).toMatch(/\d/);
    const exampleVisual = exampleSection.querySelector('.pillar-example-visual') as HTMLElement;
    expect(exampleSection.querySelector('.pillar-example-visual svg')).not.toBeNull();
    expect(exampleVisual.compareDocumentPosition(exampleCopy) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it('renders Example before the first body section on crypto liquidity', () => {
    renderPillar(<CryptoLiquidity />);
    const exampleSection = document.querySelector('.pillar-example') as HTMLElement;
    const firstBodySectionHeading = screen.getByRole('heading', { level: 2, name: 'Liquidity analysis' });
    expect(exampleSection.compareDocumentPosition(firstBodySectionHeading) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});

describe('pillar copy voice lint', () => {
  it('avoids Tier A banned words in pillar titles', () => {
    const titles = ['Crypto liquidity', 'Order book analysis', 'Bid-ask spread', 'Liquidity score'];
    for (const title of titles) {
      expect(TIER_A_BANNED.test(title)).toBe(false);
    }
  });
});
