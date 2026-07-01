import { fmtVolShort } from '../../format';
import type {
  Grade,
  LostOpportunity,
  PeerRow,
  RankingsViewModel,
  SimulatorEntry,
  Status,
  TokenViewModel,
} from '../../types';
import { capitalizeExchange } from './exchanges';
import {
  IMPLEMENTATION_OPTIONS,
  shouldShowImplementationOptions,
} from './implementationOptions';
import type { PairAnalysisPayload, RankingsPayload } from './loader';

const INVESTOR_SIMULATOR_MAX_CARDS = 3;
const SLIPPAGE_DISPLAY_SIZE_PREFERENCE = [10000, 1000, 100] as const;

function formatUpdatedAgo(fetchedAt: string | undefined): string {
  if (!fetchedAt) {
    return 'unknown';
  }
  const fetchedDate = new Date(fetchedAt);
  if (Number.isNaN(fetchedDate.getTime())) {
    return fetchedAt;
  }
  const ageMs = Date.now() - fetchedDate.getTime();
  const ageHours = Math.floor(ageMs / (1000 * 60 * 60));
  if (ageHours < 1) {
    return 'less than 1h ago';
  }
  if (ageHours < 48) {
    return `${ageHours}h ago`;
  }
  const ageDays = Math.floor(ageHours / 24);
  return `${ageDays}d ago`;
}

function formatUpdatedLabel(updatedAt: string): string {
  const updatedDate = new Date(updatedAt);
  if (Number.isNaN(updatedDate.getTime())) {
    return updatedAt;
  }
  return updatedDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

interface RawPeerRow {
  name: string;
  spread: number;
  depth: number;
  slippage_pct?: number | null;
  slippage_10k?: number | null;
  slippage10k?: number | null;
  slippage_trade_size?: number | null;
  is_yours?: boolean;
  isYours?: boolean;
}

function mapPeerRow(peerRow: RawPeerRow): PeerRow {
  let slippagePct = peerRow.slippage_pct;
  if (slippagePct == null && peerRow.slippage_10k != null && peerRow.slippage_10k > 0) {
    slippagePct = peerRow.slippage_10k;
  }
  if (slippagePct == null && peerRow.slippage10k != null && peerRow.slippage10k > 0) {
    slippagePct = peerRow.slippage10k;
  }
  let slippageTradeSize = peerRow.slippage_trade_size;
  if (slippageTradeSize == null && slippagePct != null && peerRow.slippage_10k != null) {
    slippageTradeSize = 10000;
  }
  return {
    name: peerRow.name,
    spread: peerRow.spread,
    depth: peerRow.depth,
    slippageTradeSize: slippageTradeSize ?? undefined,
    slippagePct: slippagePct ?? 0,
    slippage10k: slippagePct ?? undefined,
    isYours: peerRow.is_yours != null ? peerRow.is_yours : Boolean(peerRow.isYours),
  };
}

interface RawSlippageRow {
  size: number;
  pct?: number | null;
  omitted?: boolean;
}

function resolveSlippageDisplaySizeFromRaw(slippageRows: RawSlippageRow[]): number | null {
  for (const tradeSize of SLIPPAGE_DISPLAY_SIZE_PREFERENCE) {
    for (const slippageRow of slippageRows) {
      if (slippageRow.size === tradeSize && !slippageRow.omitted && slippageRow.pct != null) {
        return tradeSize;
      }
    }
  }
  return null;
}

function selectInvestorSimulatorRows(rows: SimulatorEntry[]): SimulatorEntry[] {
  const fillableRows = rows
    .filter((row) => !row.omitted)
    .sort((leftRow, rightRow) => rightRow.size - leftRow.size);
  const omittedRows = rows
    .filter((row) => row.omitted)
    .sort((leftRow, rightRow) => rightRow.size - leftRow.size);
  let selectedRows = fillableRows.slice(0, INVESTOR_SIMULATOR_MAX_CARDS);
  const remainingCardCount = INVESTOR_SIMULATOR_MAX_CARDS - selectedRows.length;
  if (remainingCardCount > 0) {
    omittedRows.sort((leftRow, rightRow) => leftRow.size - rightRow.size);
    selectedRows = selectedRows.concat(omittedRows.slice(0, remainingCardCount));
  }
  return selectedRows.sort((leftRow, rightRow) => rightRow.size - leftRow.size);
}

interface RawSimulatorRow {
  size: number;
  omitted?: boolean;
  fill_ratio?: number | null;
  fillRatio?: number | null;
  overpay_pct?: number | null;
  overpayPct?: number | null;
  overpay_usd?: number | null;
  overpayUsd?: number | null;
  fair_price?: number | null;
  fairPrice?: number | null;
  avg_price?: number | null;
  avgPrice?: number | null;
  highlight?: boolean;
}

function mapSimulatorRow(row: RawSimulatorRow): SimulatorEntry {
  return {
    size: row.size,
    omitted: row.omitted === true,
    fillRatio: row.fill_ratio != null ? row.fill_ratio : (row.fillRatio ?? null),
    overpayPct: row.overpay_pct != null ? row.overpay_pct : (row.overpayPct ?? null),
    overpayUsd: row.overpay_usd != null ? row.overpay_usd : (row.overpayUsd ?? null),
    fairPrice: row.fair_price != null ? row.fair_price : (row.fairPrice ?? null),
    avgPrice: row.avg_price != null ? row.avg_price : (row.avgPrice ?? null),
    highlight: Boolean(row.highlight),
  };
}

export function pairAnalysisToToken(pairAnalysis: PairAnalysisPayload): TokenViewModel {
  const raw = pairAnalysis.raw ?? {};
  const analysis = pairAnalysis.analysis ?? {};
  const peersBlock = (analysis.peers as { rows?: RawPeerRow[] }) ?? {};
  const peerRows = (peersBlock.rows ?? []).map(mapPeerRow);
  const yoursPeer = peerRows.find((peer) => peer.isYours);

  let slippageDisplaySize =
    (analysis.slippage_display_size as number | undefined) ??
    (analysis.slippageDisplaySize as number | undefined) ??
    null;
  if (slippageDisplaySize == null && yoursPeer?.slippageTradeSize != null) {
    slippageDisplaySize = yoursPeer.slippageTradeSize;
  }
  if (slippageDisplaySize == null) {
    slippageDisplaySize = resolveSlippageDisplaySizeFromRaw((raw.slippage as RawSlippageRow[]) ?? []);
  }

  const rawSimulator =
    (analysis.investor_simulator as RawSimulatorRow[] | undefined) ??
    (analysis.investorSimulator as RawSimulatorRow[] | undefined) ??
    [];
  let investorSimulator = rawSimulator.map(mapSimulatorRow);

  if (slippageDisplaySize != null && investorSimulator.length) {
    investorSimulator = investorSimulator.map((row) => ({
      ...row,
      highlight: row.size === slippageDisplaySize,
    }));
  }
  if (investorSimulator.length) {
    investorSimulator = selectInvestorSimulatorRows(investorSimulator);
  }

  const status = (analysis.status as Status | undefined) ?? 'Poor';
  const roadmap =
    (analysis.roadmap as TokenViewModel['roadmap'] | undefined) ??
  [];
  const score = analysis.score_100 as number;
  const lostOpportunityRaw =
    (analysis.lost_opportunity as LostOpportunity | undefined) ??
    (analysis.lostOpportunity as LostOpportunity | undefined) ??
    null;

  return {
    symbol: (pairAnalysis.symbol || (raw.symbol as string) || '').split('/')[0],
    pair: pairAnalysis.symbol || (raw.symbol as string),
    exchange: capitalizeExchange(pairAnalysis.exchange || (raw.exchange as string)),
    exchangeSlug: (pairAnalysis.exchange || (raw.exchange as string) || '').toLowerCase(),
    projectName: pairAnalysis.full_name || (raw.full_name as string) || pairAnalysis.symbol,
    score,
    grade: analysis.grade as Grade,
    status,
    statusClass:
      (analysis.status_class as string | undefined) ??
      (analysis.statusClass as string | undefined) ??
      'status-poor',
    slippageDisplaySize: slippageDisplaySize ?? 0,
    updatedAgo: formatUpdatedAgo(raw.fetched_at as string | undefined),
    verdict: analysis.verdict as string,
    issues: (analysis.issues as TokenViewModel['issues'] | undefined) ?? [],
    slippage: ((raw.slippage as RawSlippageRow[]) ?? []).map((row) => ({
      size: row.size,
      pct: row.pct != null ? row.pct : 0,
      highlight: row.size === 10000,
    })),
    peers: peerRows,
    healthDashboard:
      (analysis.health_dashboard as TokenViewModel['healthDashboard'] | undefined) ??
      (analysis.healthDashboard as TokenViewModel['healthDashboard'] | undefined) ??
      [],
    delistingRisk:
      (analysis.delisting_risk as TokenViewModel['delistingRisk'] | undefined) ??
      (analysis.delistingRisk as TokenViewModel['delistingRisk'] | undefined) ??
      [],
    mmPresence:
      (analysis.mm_presence as TokenViewModel['mmPresence'] | undefined) ??
      (analysis.mmPresence as TokenViewModel['mmPresence'] | undefined) ?? {
        detected: false,
        label: 'Not detected',
      },
    investorSimulator,
    lostOpportunity: lostOpportunityRaw,
    rootCauses:
      (analysis.root_causes as TokenViewModel['rootCauses'] | undefined) ??
      (analysis.rootCauses as TokenViewModel['rootCauses'] | undefined) ??
      [],
    improvements: (analysis.improvements as TokenViewModel['improvements'] | undefined) ?? [],
    roadmap,
    implementationOptions: shouldShowImplementationOptions(score, roadmap.length)
      ? IMPLEMENTATION_OPTIONS
      : [],
  };
}

export function rankingsToViewModel(rankingsPayload: RankingsPayload): RankingsViewModel {
  const exchange = rankingsPayload.exchange.toLowerCase();
  return {
    exchange,
    exchangeLabel: exchange.toUpperCase(),
    updatedLabel: formatUpdatedLabel(rankingsPayload.updated_at),
    rows: rankingsPayload.pairs.slice(0, 20).map((row) => ({
      symbol: row.symbol,
      score: row.score_100,
      vol: fmtVolShort(row.volume_quote),
      rank: row.rank,
    })),
  };
}
