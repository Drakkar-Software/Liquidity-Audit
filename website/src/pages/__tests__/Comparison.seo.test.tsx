import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Comparison } from '../Comparison';
import type { RankingsViewModel } from '../../types';

const rankings: RankingsViewModel = {
  exchange: 'mexc',
  exchangeLabel: 'MEXC',
  updatedLabel: '2h ago',
  rows: [{ symbol: 'SOL/USDT', score: 80, vol: '1.2M', rank: 1 }],
};

function renderComparison() {
  return render(
    <MemoryRouter>
      <Comparison
        rankings={rankings}
        exchange="mexc"
        rankingsPayload={{
          exchange: 'mexc',
          updated_at: '2026-06-14T20:00:00+00:00',
          pairs: [{ symbol: 'SOL/USDT', score_100: 80, volume_quote: 1_200_000, rank: 1 }],
        }}
        onExchangeChange={() => {}}
        onOpenReport={() => {}}
      />
    </MemoryRouter>,
  );
}

describe('Comparison SEO copy', () => {
  it('uses token liquidity ranking as the page H1', () => {
    renderComparison();
    expect(screen.getByRole('heading', { level: 1, name: 'Token Liquidity Ranking' })).toBeInTheDocument();
  });

  it('mentions guides below in the intro copy', () => {
    renderComparison();
    expect(screen.getByText(/guides below for definitions/i)).toBeInTheDocument();
  });

  it('shows guide cards at the end of the page, not in the hero', () => {
    renderComparison();
    expect(screen.queryByText('Guides:', { exact: true })).not.toBeInTheDocument();

    const guidesHeading = screen.getByRole('heading', { level: 2, name: 'Guides' });
    const guidesSection = guidesHeading.closest('section');
    expect(guidesSection).not.toBeNull();

    const sectionScope = within(guidesSection as HTMLElement);
    expect(sectionScope.getByRole('link', { name: /Crypto liquidity/i })).toHaveAttribute(
      'href',
      '/crypto-liquidity',
    );
    expect(sectionScope.getByRole('link', { name: /Liquidity score/i })).toHaveAttribute(
      'href',
      '/liquidity-score',
    );
  });
});
