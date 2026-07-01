import { describe, expect, it } from 'vitest';
import { solViewModel, xyzViewModel } from '../data/samples';
import {
  allIssuesPassed,
  improvementsHaveMeaningfulGap,
  shouldShowImprovements,
} from '../reportVisibility';

describe('allIssuesPassed', () => {
  it('returns true when every issue passes and there is no delisting risk', () => {
    expect(allIssuesPassed(solViewModel)).toBe(true);
  });

  it('returns false when any issue fails', () => {
    expect(allIssuesPassed(xyzViewModel)).toBe(false);
  });
});

describe('improvementsHaveMeaningfulGap', () => {
  it('detects spread, depth, and slippage gaps', () => {
    expect(improvementsHaveMeaningfulGap(xyzViewModel.improvements)).toBe(true);
  });

  it('returns false for empty improvements', () => {
    expect(improvementsHaveMeaningfulGap([])).toBe(false);
  });
});

describe('shouldShowImprovements', () => {
  it('shows improvements for poor-health tokens with meaningful gaps', () => {
    expect(shouldShowImprovements(xyzViewModel)).toBe(true);
  });

  it('hides improvements when all checks passed', () => {
    expect(shouldShowImprovements(solViewModel)).toBe(false);
  });
});
