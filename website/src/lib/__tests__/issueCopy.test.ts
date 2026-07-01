import { describe, expect, it } from 'vitest';
import {
  ALL_CHECKS_PASSED_TOOLTIP,
  DELISTING_RISK_TOOLTIP,
  getFailedIssueDisplayLabel,
  getIssueChipDisplay,
  ISSUE_CHECK_LABELS,
} from '../issueCopy';

describe('getIssueChipDisplay', () => {
  it('returns pass text and structured tooltip when ok', () => {
    expect(getIssueChipDisplay('Good volume', true)).toEqual({
      text: 'Adequate volume',
      tooltip: {
        title: 'Volume',
        body: '24h quote volume compared to the median for active pairs on this exchange.',
      },
    });
    expect(getIssueChipDisplay('Wide spread', true)).toEqual({
      text: 'Tight spread',
      tooltip: {
        title: 'Spread',
        body: 'Best bid/ask spread from the snapshot vs a configured maximum.',
      },
    });
  });

  it('returns fail text and structured tooltip when not ok', () => {
    expect(getIssueChipDisplay('Good volume', false)).toEqual({
      text: 'Low volume',
      tooltip: {
        title: 'Volume',
        body: '24h quote volume compared to the median for active pairs on this exchange.',
      },
    });
    expect(getIssueChipDisplay('Low depth', false)).toEqual({
      text: 'Thin depth',
      tooltip: {
        title: 'Depth',
        body:
          'Resting liquidity when bid/ask depth or total visible depth falls below configured minimums.',
      },
    });
  });

  it('covers every backend label in pass and fail form', () => {
    for (const label of ISSUE_CHECK_LABELS) {
      const pass = getIssueChipDisplay(label, true);
      const fail = getIssueChipDisplay(label, false);
      expect(pass.text).not.toBe(fail.text);
      expect(pass.tooltip?.title).toBeTruthy();
      expect(pass.tooltip?.body).toBeTruthy();
      expect(pass.tooltip).toEqual(fail.tooltip);
    }
  });

  it('falls back for unknown labels', () => {
    expect(getIssueChipDisplay('Unknown check', true)).toEqual({
      text: 'Unknown check',
      tooltip: null,
    });
  });
});

describe('getFailedIssueDisplayLabel', () => {
  it('returns lowercase fail text for known labels', () => {
    expect(getFailedIssueDisplayLabel('Good volume')).toBe('low volume');
    expect(getFailedIssueDisplayLabel('Low depth')).toBe('thin depth');
    expect(getFailedIssueDisplayLabel('Wide spread')).toBe('wide spread');
  });

  it('lowercases unknown labels', () => {
    expect(getFailedIssueDisplayLabel('Custom')).toBe('custom');
  });
});

describe('shared tooltip copy', () => {
  it('defines structured delisting and all-passed tooltips', () => {
    expect(DELISTING_RISK_TOOLTIP.title).toBe('Delisting risk');
    expect(DELISTING_RISK_TOOLTIP.body.length).toBeGreaterThan(20);
    expect(ALL_CHECKS_PASSED_TOOLTIP.title).toBe('All checks passed');
    expect(ALL_CHECKS_PASSED_TOOLTIP.body.length).toBeGreaterThan(10);
  });
});
