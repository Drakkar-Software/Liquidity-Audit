import { describe, expect, it } from 'vitest';
import { capitalizeExchange, isExchangeSlug } from '../exchanges';

describe('isExchangeSlug', () => {
  it('accepts supported exchanges', () => {
    expect(isExchangeSlug('mexc')).toBe(true);
    expect(isExchangeSlug('bitmart')).toBe(true);
  });

  it('rejects unknown exchanges', () => {
    expect(isExchangeSlug('binance')).toBe(false);
  });
});

describe('capitalizeExchange', () => {
  it('capitalizes the first letter', () => {
    expect(capitalizeExchange('mexc')).toBe('Mexc');
  });

  it('returns empty string for blank input', () => {
    expect(capitalizeExchange('')).toBe('');
  });
});
