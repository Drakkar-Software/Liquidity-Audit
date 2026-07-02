import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { rankingsToViewModel } from '../lib/data/adapter';
import { DEFAULT_EXCHANGE, isExchangeSlug } from '../lib/data/exchanges';
import {
  fetchRankings,
  normalizePairInput,
  pairToSlug,
  type RankingsPayload,
} from '../lib/data/loader';
import { rankingsErrorMessage } from '../lib/data/loadErrors';
import { useHomePageMeta, useLoadErrorPageMeta } from '../lib/pageMetaHooks';
import { Comparison } from '../pages/Comparison';
import type { RankingsViewModel } from '../types';

export function ComparisonRoute() {
  useHomePageMeta();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const exchangeParam = searchParams.get('exchange') ?? DEFAULT_EXCHANGE;
  const exchange = isExchangeSlug(exchangeParam) ? exchangeParam : DEFAULT_EXCHANGE;

  const [rankings, setRankings] = useState<RankingsViewModel | null>(null);
  const [rankingsPayload, setRankingsPayload] = useState<RankingsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setRankings(null);
    setError(null);

    fetchRankings(exchange)
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setRankings(rankingsToViewModel(payload));
        setRankingsPayload(payload);
      })
      .catch((fetchError: unknown) => {
        if (cancelled) {
          return;
        }
        setError(rankingsErrorMessage(exchange, fetchError));
      });

    return () => {
      cancelled = true;
    };
  }, [exchange]);

  const handleExchangeChange = (nextExchange: string) => {
    if (!isExchangeSlug(nextExchange)) {
      return;
    }
    setSearchParams({ exchange: nextExchange });
  };

  const handleOpenReport = (pairInput: string) => {
    const pair = normalizePairInput(pairInput);
    if (!pair) {
      return;
    }
    navigate(`/pairs/${exchange}/${pairToSlug(pair)}`);
  };

  return (
    <>
      {error ? <ComparisonFetchErrorMeta message={error} /> : null}
      <Comparison
        rankings={rankings}
        exchange={exchange}
        rankingsPayload={rankingsPayload}
        rankingsError={error}
        onExchangeChange={handleExchangeChange}
        onOpenReport={handleOpenReport}
      />
    </>
  );
}

function ComparisonFetchErrorMeta({ message }: { message: string }) {
  useLoadErrorPageMeta(message);
  return null;
}
