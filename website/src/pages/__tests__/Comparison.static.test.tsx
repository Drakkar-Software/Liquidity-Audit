import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Comparison } from '../Comparison';

describe('Comparison static shell', () => {
  it('renders hero and guides with skeletons when rankings are not loaded', () => {
    render(
      <MemoryRouter>
        <Comparison
          rankings={null}
          exchange="mexc"
          pairCatalog={[]}
          onExchangeChange={() => {}}
          onOpenReport={() => {}}
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Token Liquidity Ranking' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 2, name: 'Guides' })).toBeInTheDocument();
    expect(screen.getByTestId('quick-links-skeleton')).toBeInTheDocument();
    expect(screen.getByTestId('rankings-table-skeleton')).toBeInTheDocument();
    expect(screen.queryByText('Analysis unavailable')).not.toBeInTheDocument();
  });

  it('shows inline rankings error without hiding the static shell', () => {
    render(
      <MemoryRouter>
        <Comparison
          rankings={null}
          exchange="mexc"
          pairCatalog={[]}
          rankingsError="Rankings unavailable for MEXC."
          onExchangeChange={() => {}}
          onOpenReport={() => {}}
        />
      </MemoryRouter>,
    );

    expect(screen.getByRole('heading', { level: 1, name: 'Token Liquidity Ranking' })).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Rankings unavailable for MEXC.');
    expect(screen.queryByTestId('rankings-table-skeleton')).not.toBeInTheDocument();
    expect(screen.queryByTestId('quick-links-skeleton')).not.toBeInTheDocument();
  });
});
