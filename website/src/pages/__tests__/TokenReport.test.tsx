import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { xyzViewModel } from '../../lib/data/samples';
import { LIQUIDITY_AUDIT_GITHUB_URL } from '../../lib/pillarGuides';
import { TokenReport } from '../TokenReport';

describe('TokenReport', () => {
  it('shows only one visible on-screen score block', () => {
    const { container } = render(
      <MemoryRouter>
        <TokenReport vm={xyzViewModel} />
      </MemoryRouter>,
    );

    const printScore = container.querySelector('.print-only.token-report-score-compact');
    expect(printScore).not.toBeNull();
    expect(printScore).not.toBeVisible();

    const screenScore = container.querySelector('.no-print.token-report-score-compact');
    expect(screenScore).toBeVisible();
    expect(within(screenScore as HTMLElement).getByText('42')).toBeVisible();
    expect(screen.getByText('XYZ Protocol · Mexc')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'XYZ/USDT crypto liquidity report' })).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 2 }).length).toBeGreaterThanOrEqual(2);
  });

  it('links the open-source audit pipeline on GitHub', () => {
    render(
      <MemoryRouter>
        <TokenReport vm={xyzViewModel} />
      </MemoryRouter>,
    );

    expect(screen.getByText('Explore further:')).toBeInTheDocument();
    const pipelineLink = screen.getByRole('link', { name: 'Open-source audit pipeline on GitHub' });
    expect(pipelineLink).toHaveAttribute('href', LIQUIDITY_AUDIT_GITHUB_URL);
    expect(pipelineLink).toHaveAttribute('target', '_blank');
  });
});
