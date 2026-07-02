export function getAnalysisDataBase(): string {
  const configuredBase = import.meta.env.VITE_ANALYSIS_DATA_BASE;
  if (configuredBase) {
    return configuredBase.replace(/\/$/, '');
  }
  return '/data/analysis';
}

export function pairToSlug(pair: string): string {
  return pair.replace('/', '_');
}

export function slugToPair(symbolSlug: string): string {
  return symbolSlug.replace('_', '/');
}

export function normalizePairInput(input: string): string {
  const trimmed = input.trim().toUpperCase();
  if (!trimmed) {
    return '';
  }
  if (trimmed.includes('/')) {
    return trimmed;
  }
  return `${trimmed}/USDT`;
}

export class AnalysisFetchError extends Error {
  readonly status?: number;
  readonly url?: string;
  readonly invalidJson: boolean;

  constructor(
    message: string,
    status?: number,
    url?: string,
    invalidJson = false,
  ) {
    super(message);
    this.name = 'AnalysisFetchError';
    this.status = status;
    this.url = url;
    this.invalidJson = invalidJson;
  }
}

async function fetchJson<T>(url: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url);
  } catch {
    throw new AnalysisFetchError('Network request failed', undefined, url);
  }

  if (!response.ok) {
    throw new AnalysisFetchError(`HTTP ${response.status}`, response.status, url);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new AnalysisFetchError('Invalid JSON response', response.status, url, true);
  }
}

export interface RankingsPairRow {
  symbol: string;
  score_100: number;
  volume_quote: number;
  rank: number | null;
}

export interface RankingsPayload {
  exchange: string;
  updated_at: string;
  rankings_min_volume_quote?: number;
  pairs: RankingsPairRow[];
}

const DEFAULT_RANKINGS_MIN_VOLUME_QUOTE = 1000;

export function resolveRankingsMinVolumeQuote(rankingsPayload: RankingsPayload): number {
  return rankingsPayload.rankings_min_volume_quote ?? DEFAULT_RANKINGS_MIN_VOLUME_QUOTE;
}

export function isRankingsEligible(
  row: RankingsPairRow,
  rankingsMinVolumeQuote: number,
): boolean {
  return row.volume_quote >= rankingsMinVolumeQuote;
}

export interface PairAnalysisPayload {
  exchange: string;
  symbol: string;
  full_name: string;
  raw: Record<string, unknown>;
  analysis: Record<string, unknown>;
}

export async function fetchRankings(exchange: string): Promise<RankingsPayload> {
  const dataBase = getAnalysisDataBase();
  return fetchJson<RankingsPayload>(`${dataBase}/rankings/${exchange.toLowerCase()}.json`);
}

export async function fetchPairAnalysis(exchange: string, pair: string): Promise<PairAnalysisPayload> {
  const dataBase = getAnalysisDataBase();
  const slug = pairToSlug(pair);
  return fetchJson<PairAnalysisPayload>(`${dataBase}/pairs/${exchange.toLowerCase()}/${slug}.json`);
}

export function buildRankingsCatalog(rankingsPayload: RankingsPayload): string[] {
  const rankingsMinVolumeQuote = resolveRankingsMinVolumeQuote(rankingsPayload);
  return rankingsPayload.pairs
    .filter((row) => isRankingsEligible(row, rankingsMinVolumeQuote))
    .sort((leftRow, rightRow) => (leftRow.rank ?? Number.MAX_SAFE_INTEGER) - (rightRow.rank ?? Number.MAX_SAFE_INTEGER))
    .map((row) => row.symbol);
}

export function buildSearchCatalog(rankingsPayload: RankingsPayload): string[] {
  return rankingsPayload.pairs.map((row) => row.symbol);
}

export function filterPairCatalog(catalog: string[], query: string, maxResults = 8): string[] {
  const normalizedQuery = query.trim().toUpperCase();
  if (!normalizedQuery) {
    return catalog.slice(0, maxResults);
  }
  return catalog
    .filter((symbol) => symbol.toUpperCase().includes(normalizedQuery))
    .slice(0, maxResults);
}

export function resolvePairSuggestions(
  rankingsPayload: RankingsPayload,
  query: string,
  maxResults = 8,
): string[] {
  const normalizedQuery = query.trim();
  if (!normalizedQuery) {
    return filterPairCatalog(buildRankingsCatalog(rankingsPayload), '', maxResults);
  }
  return filterPairCatalog(buildSearchCatalog(rankingsPayload), normalizedQuery, maxResults);
}
