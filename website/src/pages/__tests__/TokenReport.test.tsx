import { describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { xyzViewModel } from '../../lib/data/samples';
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
  });
});
