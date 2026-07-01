import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Tooltip } from '../Tooltip';
import { renderIssueTooltip } from '../../lib/issueTooltipContent';

describe('Tooltip', () => {
  it('renders children only when content is empty', () => {
    render(
      <Tooltip content={null}>
        <button type="button">Chip</button>
      </Tooltip>,
    );
    expect(screen.getByRole('button', { name: 'Chip' })).toBeInTheDocument();
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });

  it('shows formatted tooltip on hover', async () => {
    const user = userEvent.setup();
    render(
      <Tooltip
        content={renderIssueTooltip({
          title: 'Spread',
          body: 'Best bid/ask spread from the snapshot vs a configured maximum.',
        })}
      >
        <span>Trigger</span>
      </Tooltip>,
    );

    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
    await user.hover(screen.getByText('Trigger'));
    const tooltip = screen.getByRole('tooltip');
    expect(tooltip).toHaveTextContent('Spread');
    expect(tooltip).toHaveTextContent(
      'Best bid/ask spread from the snapshot vs a configured maximum.',
    );
    expect(screen.getByText('Trigger').closest('[title]')).toBeNull();
  });

  it('shows tooltip on focus and hides on blur', async () => {
    const user = userEvent.setup();
    render(
      <Tooltip
        content={renderIssueTooltip({
          title: 'Volume',
          body: '24h quote volume compared to the median for active pairs on this exchange.',
        })}
      >
        <span>Focus me</span>
      </Tooltip>,
    );

    await user.tab();
    expect(screen.getByRole('tooltip')).toBeInTheDocument();
    await user.tab();
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });

  it('toggles tooltip on touch tap and closes on outside tap', () => {
    render(
      <Tooltip
        content={renderIssueTooltip({
          title: 'Depth',
          body: 'Resting liquidity when bid/ask depth or total visible depth falls below configured minimums.',
        })}
      >
        <span>Tap me</span>
      </Tooltip>,
    );

    const trigger = screen.getByText('Tap me').closest('span[tabindex="0"]');
    expect(trigger).not.toBeNull();
    fireEvent.pointerDown(trigger!, { pointerType: 'touch' });
    expect(screen.getByRole('tooltip')).toHaveTextContent('Depth');

    fireEvent.pointerDown(document.body, { pointerType: 'touch' });
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();
  });

  it('toggles tooltip on click when coarse pointer is preferred', () => {
    const matchMedia = vi.fn().mockImplementation((query: string) => ({
      matches: query.includes('hover: none') || query.includes('pointer: coarse'),
      media: query,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));
    vi.stubGlobal('matchMedia', matchMedia);

    render(
      <Tooltip
        content={renderIssueTooltip({
          title: 'Slippage',
          body: 'Buy slippage at the report trade size vs the median of up to 3 similar-volume peers.',
        })}
      >
        <span>Mobile chip</span>
      </Tooltip>,
    );

    const trigger = screen.getByText('Mobile chip');
    fireEvent.click(trigger);
    expect(screen.getByRole('tooltip')).toHaveTextContent('Slippage');

    fireEvent.click(document.body);
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument();

    vi.unstubAllGlobals();
  });
});
