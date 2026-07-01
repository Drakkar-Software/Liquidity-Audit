import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QuickLinksSkeleton, RankingsTableSkeleton } from '../RankingsSkeleton';

describe('QuickLinksSkeleton', () => {
  it('renders the quick links skeleton row', () => {
    render(<QuickLinksSkeleton />);
    expect(screen.getByTestId('quick-links-skeleton')).toBeInTheDocument();
    expect(screen.getByText('Quick links:')).toBeInTheDocument();
  });
});

describe('RankingsTableSkeleton', () => {
  it('marks the table region busy with status text for assistive tech', () => {
    render(<RankingsTableSkeleton />);
    expect(screen.getByTestId('rankings-table-skeleton')).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByRole('status')).toHaveTextContent('Loading rankings…');
  });
});
