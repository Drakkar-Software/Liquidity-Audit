import { describe, expect, it } from 'vitest';
import { fmtSignedUsd, fmtUsd, fmtUsdShort, fmtVolShort } from '../format';

describe('fmtUsd', () => {
  it('formats whole-dollar amounts', () => {
    expect(fmtUsd(12345)).toBe('$12,345');
  });
});

describe('fmtSignedUsd', () => {
  it('prefixes positive values with plus', () => {
    expect(fmtSignedUsd(3525)).toBe('+$3,525');
  });

  it('uses a minus sign for negative values', () => {
    expect(fmtSignedUsd(-820)).toBe('−$820');
  });
});

describe('fmtUsdShort', () => {
  it('formats thousands and millions', () => {
    expect(fmtUsdShort(9500)).toBe('$9.5k');
    expect(fmtUsdShort(100000)).toBe('$100k');
    expect(fmtUsdShort(3_400_000)).toBe('$3.4M');
  });
});

describe('fmtVolShort', () => {
  it('formats volume without a leading dollar sign', () => {
    expect(fmtVolShort(2_100_000_000)).toBe('2.1B');
    expect(fmtVolShort(890_000_000)).toBe('890M');
  });
});
