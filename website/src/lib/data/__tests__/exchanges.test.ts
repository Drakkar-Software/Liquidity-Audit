import { describe, expect, it } from 'vitest';
import { capitalizeExchange, isActiveExchangeSlug, isExchangeSlug } from '../exchanges';

describe('isExchangeSlug', () => {
  it('accepts active exchanges', () => {
    expect(isExchangeSlug('mexc')).toBe(true);
    expect(isExchangeSlug('coinex')).toBe(true);
    expect(isExchangeSlug('bingx')).toBe(true);
    expect(isExchangeSlug('weex')).toBe(true);
  });

  it('accepts legacy loadable exchanges', () => {
    expect(isExchangeSlug('bitmart')).toBe(true);
  });

  it('rejects unknown exchanges', () => {
    expect(isExchangeSlug('binance')).toBe(false);
  });
});

describe('isActiveExchangeSlug', () => {
  it('accepts only active exchanges', () => {
    expect(isActiveExchangeSlug('mexc')).toBe(true);
    expect(isActiveExchangeSlug('coinex')).toBe(true);
    expect(isActiveExchangeSlug('bingx')).toBe(true);
    expect(isActiveExchangeSlug('weex')).toBe(true);
    expect(isActiveExchangeSlug('bitmart')).toBe(false);
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
