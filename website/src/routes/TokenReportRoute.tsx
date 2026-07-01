import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { pairAnalysisToToken } from '../lib/data/adapter';
import { isExchangeSlug } from '../lib/data/exchanges';
import { fetchPairAnalysis, slugToPair, type PairAnalysisPayload } from '../lib/data/loader';
import { pairAnalysisErrorMessage } from '../lib/data/loadErrors';
import { useLoadErrorPageMeta, useTokenReportPageMeta } from '../lib/pageMetaHooks';
import { TokenReport } from '../pages/TokenReport';
import { LoadError, LoadingScreen } from '../components/LoadState';
import type { TokenViewModel } from '../types';

export function TokenReportRoute() {
  const { exchange: exchangeParam, symbolSlug } = useParams();
  const exchange = exchangeParam?.toLowerCase() ?? '';
  const pair = symbolSlug ? slugToPair(symbolSlug) : '';
  const slug = symbolSlug ?? '';

  const [viewModel, setViewModel] = useState<TokenViewModel | null>(null);
  const [analysisPayload, setAnalysisPayload] = useState<PairAnalysisPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useTokenReportPageMeta({
    exchange,
    slug,
    pair,
    viewModel,
    payload: analysisPayload,
  });

  useEffect(() => {
    if (!exchange || !pair || !isExchangeSlug(exchange)) {
      setError(pairAnalysisErrorMessage(exchange, pair));
      setViewModel(null);
      setAnalysisPayload(null);
      return;
    }

    let cancelled = false;
    setViewModel(null);
    setAnalysisPayload(null);
    setError(null);

    fetchPairAnalysis(exchange, pair)
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setAnalysisPayload(payload);
        setViewModel(pairAnalysisToToken(payload));
      })
      .catch((fetchError: unknown) => {
        if (cancelled) {
          return;
        }
        setError(pairAnalysisErrorMessage(exchange, pair, fetchError));
      });

    return () => {
      cancelled = true;
    };
  }, [exchange, pair]);

  if (error) {
    return <TokenReportLoadError message={error} />;
  }

  if (!viewModel) {
    return <LoadingScreen label={`Loading ${pair || 'report'}…`} />;
  }

  return <TokenReport vm={viewModel} />;
}

function TokenReportLoadError({ message }: { message: string }) {
  useLoadErrorPageMeta(message);
  return <LoadError message={message} />;
}
