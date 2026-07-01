import { describe, expect, it } from 'vitest';
import {
  IMPLEMENTATION_OPTIONS_SCORE_THRESHOLD,
  shouldShowImplementationOptions,
} from '../implementationOptions';

describe('shouldShowImplementationOptions', () => {
  it('shows options when roadmap is non-empty', () => {
    expect(shouldShowImplementationOptions(95, 1)).toBe(true);
  });

  it('shows options when score is below threshold', () => {
    expect(shouldShowImplementationOptions(IMPLEMENTATION_OPTIONS_SCORE_THRESHOLD - 1, 0)).toBe(true);
  });

  it('hides options for healthy scores without roadmap', () => {
    expect(shouldShowImplementationOptions(IMPLEMENTATION_OPTIONS_SCORE_THRESHOLD, 0)).toBe(false);
  });

  it('hides options when score is null and roadmap is empty', () => {
    expect(shouldShowImplementationOptions(null, 0)).toBe(false);
  });
});
