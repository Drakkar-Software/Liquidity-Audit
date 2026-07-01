import { describe, expect, it } from 'vitest';
import { AnalysisFetchError } from '../loader';
import { pairAnalysisErrorMessage, rankingsErrorMessage } from '../loadErrors';

describe('pairAnalysisErrorMessage', () => {
  it('returns invalid URL message when params are missing', () => {
    expect(pairAnalysisErrorMessage('', '')).toBe('The report URL is invalid.');
  });

  it('returns missing-analysis message for 404 errors', () => {
    const error = new AnalysisFetchError('HTTP 404', 404, '/data/pairs/mexc/XYZ_USDT.json');
    expect(pairAnalysisErrorMessage('mexc', 'XYZ/USDT', error)).toContain('No analysis for XYZ/USDT on MEXC');
  });

  it('returns generic load failure for other errors', () => {
    expect(pairAnalysisErrorMessage('mexc', 'XYZ/USDT', new Error('timeout'))).toContain(
      'could not be loaded right now',
    );
  });
});

describe('rankingsErrorMessage', () => {
  it('returns exchange-specific message for missing rankings', () => {
    const error = new AnalysisFetchError('HTTP 404', 404);
    expect(rankingsErrorMessage('mexc', error)).toBe('Could not load rankings for MEXC.');
  });

  it('returns generic message for other failures', () => {
    expect(rankingsErrorMessage('mexc', new Error('timeout'))).toBe('Rankings data could not be loaded.');
  });
});
