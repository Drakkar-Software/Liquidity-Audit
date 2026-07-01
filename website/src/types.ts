// View-model types for the Liquidity Audit UI (Layer 3 of the data contract).
// Field names are camelCase, produced by the backend -> view-model adapter.
// See docs/03-data-contract.md for the full backend -> view-model mapping.

import type { Status, Severity } from './theme';

export type { Status, Severity };
export type Grade = 'A' | 'B' | 'C' | 'D' | 'F';

export interface Issue {
  /** Backend check key; display copy in lib/issueCopy.ts */
  label: string;
  ok: boolean;
}

export interface SlippagePoint {
  size: number;
  pct: number;
  highlight?: boolean;
}

export interface PeerRow {
  /** Peer name, or "Yours" / "Median". */
  name: string;
  spread: number;
  depth: number;
  slippageTradeSize?: number;
  slippagePct: number;
  slippage10k?: number;
  isYours: boolean;
}

export interface HealthMetric {
  severity: Severity;
  title: string;
  impact: string;
  evidence: string;
}

/** Only `title` is user-facing — never render `evidence`/threshold USD. */
export interface DelistingFactor {
  title: string;
  severity?: Severity;
  evidence?: string;
}

export interface MmPresence {
  detected: boolean;
  label: string;
}

export interface SimulatorEntry {
  size: number;
  omitted: boolean;
  fillRatio: number | null;
  overpayPct: number | null;
  overpayUsd: number | null;
  fairPrice: number | null;
  avgPrice: number | null;
  highlight: boolean;
}

export interface LostOpportunity {
  size: number;
  cost: number;
  range: string;
  note?: string;
}

export interface RootCause {
  rank: number;
  title: string;
  evidence: string;
  impact: string;
}

export interface Improvement {
  metric: string;
  current: string;
  potential: string;
}

export interface RoadmapItem {
  issue: string;
  fix: string;
  cost: string;
  impact: string;
}

export interface ImplementationOption {
  id: string;
  title: string;
  pros: string;
  cons: string;
  url: string;
}

/** A row in the public rankings table (comparison page). */
export interface RankingRow {
  symbol: string;
  score: number;
  /** Pre-formatted short volume, e.g. "1.2M". */
  vol: string;
  rank: number;
  highlight?: boolean;
}

/** The full token report view model. */
export interface TokenViewModel {
  // identity
  symbol: string;
  pair: string;
  exchange: string;
  exchangeSlug: string;
  projectName: string;
  updatedAgo: string;

  // score block
  score: number;
  grade: Grade;
  status: Status;
  statusClass: string;
  verdict: string;
  slippageDisplaySize: number;
  issues: Issue[];

  // report sections (empty array / null = section hidden)
  slippage: SlippagePoint[];
  peers: PeerRow[];
  healthDashboard: HealthMetric[];
  delistingRisk: DelistingFactor[];
  mmPresence: MmPresence;
  investorSimulator: SimulatorEntry[];
  lostOpportunity: LostOpportunity | null;
  rootCauses: RootCause[];
  improvements: Improvement[];
  roadmap: RoadmapItem[];
  implementationOptions: ImplementationOption[];
}

/** Rankings overlay used by the comparison page. */
export interface RankingsViewModel {
  exchange: string;
  exchangeLabel: string;
  updatedLabel: string;
  rows: RankingRow[];
}
