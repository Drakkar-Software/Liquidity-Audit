import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { Comparison } from '../Comparison';
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

function renderComparison(pairCatalog: string[]) {
  const onOpenReport = vi.fn();
  render(
    <MemoryRouter>
      <Comparison
        rankings={rankings}
        exchange="mexc"
        pairCatalog={pairCatalog}
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
    renderComparison(['SOL/USDT', 'ETH/USDT', 'XYZ/USDT']);

    const input = document.getElementById('pair-search-input') as HTMLInputElement;
    await user.click(input);
    await user.type(input, 'so');

    expect(input).toHaveAttribute('aria-expanded', 'true');
    expect(input).toHaveAttribute('aria-controls', 'pair-search-listbox');
    expect(screen.getByRole('listbox')).toBeInTheDocument();
  });

  it('moves aria-activedescendant with arrow keys and submits highlighted option on Enter', async () => {
    const user = userEvent.setup();
    const { onOpenReport } = renderComparison(['SOL/USDT', 'ETH/USDT', 'XYZ/USDT']);

    const input = document.getElementById('pair-search-input') as HTMLInputElement;
    await user.click(input);

    await user.keyboard('{ArrowDown}');
    expect(input).toHaveAttribute('aria-activedescendant', 'pair-suggestion-0');

    await user.keyboard('{ArrowDown}');
    expect(input).toHaveAttribute('aria-activedescendant', 'pair-suggestion-1');

    await user.keyboard('{Enter}');
    expect(onOpenReport).toHaveBeenCalledWith('ETH/USDT');
  });
});
