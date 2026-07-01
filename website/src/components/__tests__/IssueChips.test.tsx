import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { IssueChips } from '../IssueChips';
import type { DelistingFactor, Issue } from '../../types';

const passingIssues: Issue[] = [
  { label: 'Good volume', ok: true },
  { label: 'Wide spread', ok: true },
];

const mixedIssues: Issue[] = [
  { label: 'Good volume', ok: true },
  { label: 'Wide spread', ok: false },
];

const delistingRisk: DelistingFactor[] = [{ title: 'Low depth' }];

describe('IssueChips', () => {
  it('collapses to a single chip when all checks pass', async () => {
    const user = userEvent.setup();
    render(<IssueChips issues={passingIssues} delistingRisk={[]} />);
    const chip = screen.getByText('✓ All checks passed');
    expect(chip).toBeInTheDocument();
    expect(screen.queryByText('✕ Wide spread')).not.toBeInTheDocument();
    expect(chip.closest('[title]')).toBeNull();

    await user.hover(chip);
    const tooltip = screen.getByRole('tooltip');
    expect(tooltip).toHaveTextContent('All checks passed');
    expect(tooltip).toHaveTextContent('All five liquidity checks passed at snapshot time.');
  });

  it('renders display text and custom tooltips when checks fail', async () => {
    const user = userEvent.setup();
    render(<IssueChips issues={mixedIssues} delistingRisk={[]} />);
    const adequateVolume = screen.getByText('✓ Adequate volume');
    const wideSpread = screen.getByText('✕ Wide spread');
    expect(adequateVolume).toBeInTheDocument();
    expect(wideSpread).toBeInTheDocument();
    expect(adequateVolume.closest('[title]')).toBeNull();

    await user.hover(adequateVolume);
    expect(screen.getByRole('tooltip')).toHaveTextContent('Volume');
    expect(screen.getByRole('tooltip')).toHaveTextContent(
      '24h quote volume compared to the median for active pairs on this exchange.',
    );

    await user.unhover(adequateVolume);
    await user.hover(wideSpread);
    expect(screen.getByRole('tooltip')).toHaveTextContent('Spread');
    expect(screen.getByRole('tooltip')).toHaveTextContent(
      'Best bid/ask spread from the snapshot vs a configured maximum.',
    );
  });

  it('shows delisting risk chip with custom tooltip when factors are present', async () => {
    const user = userEvent.setup();
    render(<IssueChips issues={mixedIssues} delistingRisk={delistingRisk} />);
    const chip = screen.getByText('⚠ Delisting risk');
    expect(chip).toBeInTheDocument();
    expect(chip.closest('[title]')).toBeNull();

    await user.hover(chip);
    const tooltip = screen.getByRole('tooltip');
    expect(tooltip).toHaveTextContent('Delisting risk');
    expect(tooltip).toHaveTextContent('Not a guarantee of delisting.');
  });
});
