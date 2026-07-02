import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Comparison } from '../Comparison';
import type { RankingsPayload } from '../../lib/data/loader';
import type { RankingsViewModel } from '../../types';

const rankings: RankingsViewModel = {
  exchange: 'mexc',
  exchangeLabel: 'MEXC',
  updatedLabel: '2h ago',
  rows: [
    { symbol: 'SOL/USDT', score: 80, vol: '1.2M', rank: 1 },
    { symbol: 'ETH/USDT', score: 75, vol: '900K', rank: 2 },
  ],
};

const rankingsPayload: RankingsPayload = {
  exchange: 'mexc',
  updated_at: '2026-06-14T20:00:00+00:00',
  rankings_min_volume_quote: 1000,
  pairs: [
    { symbol: 'SOL/USDT', score_100: 80, volume_quote: 1_200_000, rank: 1 },
    { symbol: 'ETH/USDT', score_100: 75, volume_quote: 900_000, rank: 2 },
    { symbol: 'XYZ/USDT', score_100: 42, volume_quote: 2, rank: 3 },
  ],
};

const bitmartRankingsPayload: RankingsPayload = {
  exchange: 'bitmart',
  updated_at: '2026-07-01T13:14:26+00:00',
  rankings_min_volume_quote: 1000,
  pairs: [
    { symbol: 'SOL/USDT', score_100: 92, volume_quote: 2_100_000_000, rank: 1 },
    { symbol: 'ULX/USDT', score_100: 15, volume_quote: 0, rank: null },
  ],
};

function renderComparison(rankingsPayloadForTest: RankingsPayload) {
  const onOpenReport = vi.fn();
  render(
    <MemoryRouter>
      <Comparison
        rankings={rankings}
        exchange={rankingsPayloadForTest.exchange}
        rankingsPayload={rankingsPayloadForTest}
        onExchangeChange={() => {}}
        onOpenReport={onOpenReport}
      />
    </MemoryRouter>,
  );
  return { onOpenReport };
}

describe('Comparison search combobox', () => {
  it('exposes listbox semantics when suggestions are visible', async () => {
    const user = userEvent.setup();
    renderComparison(rankingsPayload);

    const input = document.getElementById('pair-search-input') as HTMLInputElement;
    await user.click(input);
    await user.type(input, 'so');

    expect(input).toHaveAttribute('aria-expanded', 'true');
    expect(input).toHaveAttribute('aria-controls', 'pair-search-listbox');
    expect(screen.getByRole('listbox')).toBeInTheDocument();
  });

  it('moves aria-activedescendant with arrow keys and submits highlighted option on Enter', async () => {
    const user = userEvent.setup();
    const { onOpenReport } = renderComparison(rankingsPayload);

    const input = document.getElementById('pair-search-input') as HTMLInputElement;
    await user.click(input);

    await user.keyboard('{ArrowDown}');
    expect(input).toHaveAttribute('aria-activedescendant', 'pair-suggestion-0');

    await user.keyboard('{ArrowDown}');
    expect(input).toHaveAttribute('aria-activedescendant', 'pair-suggestion-1');

    await user.keyboard('{Enter}');
    expect(onOpenReport).toHaveBeenCalledWith('ETH/USDT');
  });

  it('shows low-volume pairs when typing a matching query', async () => {
    const user = userEvent.setup();
    renderComparison(bitmartRankingsPayload);

    const input = document.getElementById('pair-search-input') as HTMLInputElement;
    await user.click(input);
    await user.type(input, 'ULX');

    expect(screen.getByRole('option', { name: 'ULX/USDT' })).toBeInTheDocument();
  });

  it('does not show low-volume pairs in the default dropdown', async () => {
    const user = userEvent.setup();
    renderComparison(bitmartRankingsPayload);

    const input = document.getElementById('pair-search-input') as HTMLInputElement;
    await user.click(input);

    expect(screen.queryByRole('option', { name: 'ULX/USDT' })).not.toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'SOL/USDT' })).toBeInTheDocument();
  });
});
