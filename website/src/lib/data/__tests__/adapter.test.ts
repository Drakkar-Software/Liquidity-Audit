import { describe, expect, it } from 'vitest';
import pairAnalysisSample from '../../../test/fixtures/pair-analysis.sample.json';
import rankingsMexcSample from '../../../test/fixtures/rankings-mexc.sample.json';
import { pairAnalysisToToken, rankingsToViewModel } from '../adapter';
import type { PairAnalysisPayload, RankingsPayload } from '../loader';

describe('pairAnalysisToToken', () => {
  it('maps core report fields from pair analysis payload', () => {
    const viewModel = pairAnalysisToToken(pairAnalysisSample as PairAnalysisPayload);

    expect(viewModel.pair).toBe('XYZ/USDT');
    expect(viewModel.projectName).toBe('XYZ Protocol');
    expect(viewModel.score).toBe(42);
    expect(viewModel.grade).toBe('D');
    expect(viewModel.status).toBe('Poor');
    expect(viewModel.issues).toHaveLength(5);
    expect(viewModel.peers).toHaveLength(5);
    expect(viewModel.improvements).toHaveLength(3);
    expect(viewModel.implementationOptions.length).toBeGreaterThan(0);
  });
});

describe('rankingsToViewModel', () => {
  it('maps rankings rows with formatted volume', () => {
    const viewModel = rankingsToViewModel(rankingsMexcSample as RankingsPayload);

    expect(viewModel.exchange).toBe('mexc');
    expect(viewModel.exchangeLabel).toBe('MEXC');
    expect(viewModel.rows[0]?.symbol).toBe('SOL/USDT');
    expect(viewModel.rows[0]?.score).toBe(92);
    expect(viewModel.rows[0]?.vol).toBe('2.1B');
  });
});
