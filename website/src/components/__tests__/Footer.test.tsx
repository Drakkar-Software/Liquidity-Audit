import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Footer } from '../Footer';
import {
  CRYPTO_MARKET_MAKING_BLOG_URL,
  OPEN_SOURCE_MARKET_MAKING_BLOG_URL,
} from '../../lib/pillarGuides';

function renderFooter() {
  return render(
    <MemoryRouter>
      <Footer />
    </MemoryRouter>,
  );
}

describe('Footer', () => {
  it('shows site brand and disclaimer in the brand column', () => {
    renderFooter();
    expect(screen.getByRole('link', { name: /LIQUIDITY.*AUDIT/i })).toHaveAttribute('href', '/');
    expect(screen.getByText('Independent analysis · Not financial advice')).toBeInTheDocument();
  });

  it('lists guides with natural titles in a vertical list', () => {
    renderFooter();
    expect(screen.getByText('Guides')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Crypto liquidity' })).toHaveAttribute('href', '/crypto-liquidity');
    expect(screen.getByRole('link', { name: 'Liquidity score' })).toHaveAttribute('href', '/liquidity-score');
  });

  it('lists audit links in a separate column', () => {
    renderFooter();
    expect(screen.getByText('Audit')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Methodology' })).toHaveAttribute('href', '/methodology');
    expect(screen.getByRole('link', { name: 'Case studies' })).toHaveAttribute('href', '/case-studies');
  });

  it('links market making blog posts only in the market making column', () => {
    renderFooter();
    expect(screen.getByText('Market making')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Crypto market making' })).toHaveAttribute(
      'href',
      CRYPTO_MARKET_MAKING_BLOG_URL,
    );
    expect(screen.getByRole('link', { name: 'Open source market making' })).toHaveAttribute(
      'href',
      OPEN_SOURCE_MARKET_MAKING_BLOG_URL,
    );
    expect(screen.queryByRole('link', { name: 'market making' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'liquidity provider crypto' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'https://market-making.octobot.cloud/' })).not.toBeInTheDocument();
  });
});
