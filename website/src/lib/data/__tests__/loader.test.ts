import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  AnalysisFetchError,
  buildPairCatalog,
  fetchPairAnalysis,
  fetchRankings,
  filterPairCatalog,
  getAnalysisDataBase,
  normalizePairInput,
  pairToSlug,
  slugToPair,
  type RankingsPayload,
} from '../loader';

describe('pairToSlug', () => {
  it('replaces slash with underscore', () => {
    expect(pairToSlug('SOL/USDT')).toBe('SOL_USDT');
  });
});

describe('slugToPair', () => {
  it('replaces only the first underscore', () => {
    expect(slugToPair('FOO_BAR_BAZ')).toBe('FOO/BAR_BAZ');
  });

  it('converts a standard slug', () => {
    expect(slugToPair('XYZ_USDT')).toBe('XYZ/USDT');
  });
});

describe('normalizePairInput', () => {
  it('returns empty string for blank input', () => {
    expect(normalizePairInput('   ')).toBe('');
  });

  it('uppercases and appends USDT when no slash', () => {
    expect(normalizePairInput('sol')).toBe('SOL/USDT');
  });

  it('preserves slash pairs', () => {
    expect(normalizePairInput('eth/usdt')).toBe('ETH/USDT');
  });
});

describe('buildPairCatalog', () => {
  it('maps pair symbols from rankings payload', () => {
    const payload: RankingsPayload = {
      exchange: 'mexc',
      updated_at: '2026-06-14T20:00:00+00:00',
      pairs: [
        { symbol: 'SOL/USDT', score_100: 92, volume_quote: 1, rank: 1 },
        { symbol: 'XYZ/USDT', score_100: 42, volume_quote: 2, rank: 2 },
      ],
    };
    expect(buildPairCatalog(payload)).toEqual(['SOL/USDT', 'XYZ/USDT']);
  });
});

describe('filterPairCatalog', () => {
  const catalog = ['SOL/USDT', 'ETH/USDT', 'XYZ/USDT', 'ARB/USDT'];

  it('returns the first results when query is empty', () => {
    expect(filterPairCatalog(catalog, '', 2)).toEqual(['SOL/USDT', 'ETH/USDT']);
  });

  it('filters by substring', () => {
    expect(filterPairCatalog(catalog, 'xy')).toEqual(['XYZ/USDT']);
  });
});

describe('getAnalysisDataBase', () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    vi.stubEnv('VITE_ANALYSIS_DATA_BASE', '');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('defaults to /data/analysis', () => {
    expect(getAnalysisDataBase()).toBe('/data/analysis');
  });

  it('strips a trailing slash from configured base', () => {
    vi.stubEnv('VITE_ANALYSIS_DATA_BASE', 'https://example.com/data/');
    expect(getAnalysisDataBase()).toBe('https://example.com/data');
  });
});

describe('fetchRankings', () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    vi.stubEnv('VITE_ANALYSIS_DATA_BASE', '');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('fetches rankings JSON from the analysis base', async () => {
    const payload: RankingsPayload = {
      exchange: 'mexc',
      updated_at: '2026-06-14T20:00:00+00:00',
      pairs: [],
    };
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    await expect(fetchRankings('mexc')).resolves.toEqual(payload);
    expect(fetch).toHaveBeenCalledWith('/data/analysis/rankings/mexc.json');
  });

  it('throws AnalysisFetchError on HTTP failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
      }),
    );

    await expect(fetchRankings('mexc')).rejects.toMatchObject({
      name: 'AnalysisFetchError',
      status: 404,
    });
  });

  it('throws AnalysisFetchError on invalid JSON', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => {
          throw new SyntaxError('Invalid JSON');
        },
      }),
    );

    await expect(fetchRankings('mexc')).rejects.toMatchObject({
      name: 'AnalysisFetchError',
      invalidJson: true,
    });
  });

  it('throws AnalysisFetchError on network failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('Failed to fetch')),
    );

    await expect(fetchRankings('mexc')).rejects.toBeInstanceOf(AnalysisFetchError);
  });
});

describe('fetchPairAnalysis', () => {
  beforeEach(() => {
    vi.unstubAllEnvs();
    vi.stubEnv('VITE_ANALYSIS_DATA_BASE', '');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('fetches pair JSON using slug path', async () => {
    const payload = { exchange: 'mexc', symbol: 'XYZ/USDT' };
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => payload,
      }),
    );

    await expect(fetchPairAnalysis('mexc', 'XYZ/USDT')).resolves.toEqual(payload);
    expect(fetch).toHaveBeenCalledWith('/data/analysis/pairs/mexc/XYZ_USDT.json');
  });
});
