import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import type { RankingsPayload } from '../../lib/data/loader';

vi.mock('../../lib/data/loader', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../lib/data/loader')>();
  return {
    ...actual,
    fetchRankings: vi.fn(),
  };
});

import { fetchRankings } from '../../lib/data/loader';
import { ComparisonRoute } from '../ComparisonRoute';

const mexcRankingsPayload: RankingsPayload = {
  exchange: 'mexc',
  updated_at: '2026-06-14T20:00:00Z',
  pairs: [{ symbol: 'SOL/USDT', score_100: 92, volume_quote: 2_100_000_000, rank: 1 }],
};

describe('ComparisonRoute', () => {
  it('renders the static shell and skeletons while rankings are loading', () => {
    vi.mocked(fetchRankings).mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter>
        <ComparisonRoute />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Token Liquidity Ranking' })).toBeInTheDocument();
    expect(screen.getByTestId('rankings-table-skeleton')).toBeInTheDocument();
    expect(screen.queryByText('Analysis unavailable')).not.toBeInTheDocument();
  });

  it('replaces skeletons with rankings after fetch completes', async () => {
    vi.mocked(fetchRankings).mockResolvedValue(mexcRankingsPayload);

    render(
      <MemoryRouter>
        <ComparisonRoute />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.queryByTestId('rankings-table-skeleton')).not.toBeInTheDocument();
    });
    expect(screen.getAllByText('SOL/USDT').length).toBeGreaterThanOrEqual(1);
  });
});
