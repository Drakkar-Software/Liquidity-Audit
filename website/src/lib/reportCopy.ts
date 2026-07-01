import { fmtUsd, fmtUsdShort } from '../format';
import type { LostOpportunity, SimulatorEntry, TokenViewModel } from '../types';
import { allIssuesPassed } from './reportVisibility';

const POSITIVE_VERDICT_MARKERS = ['at or better than', 'executes'];

const TRIVIAL_LOST_OPPORTUNITY_RANGES = new Set(['0%', '0.0–0.0%', '0.0-0.0%']);

export interface LostOpportunityCopy {
  noteOnly: string | null;
  lead: string;
  body: string;
  range: string | null;
  isPositive: boolean;
}

export function isTrivialLostOpportunityRange(range: string): boolean {
  return TRIVIAL_LOST_OPPORTUNITY_RANGES.has(range.trim());
}

export function shouldUsePositiveLostOpportunityCopy(vm: TokenViewModel): boolean {
  const lostOpportunity = vm.lostOpportunity;
  if (lostOpportunity == null) {
    return false;
  }
  if (vm.status === 'Good' || allIssuesPassed(vm)) {
    return true;
  }
  if (lostOpportunity.range && isTrivialLostOpportunityRange(lostOpportunity.range)) {
    return true;
  }
  return false;
}

export function lostOpportunityText(vm: TokenViewModel): LostOpportunityCopy {
  const lostOpportunity = vm.lostOpportunity as LostOpportunity;
  if (lostOpportunity.note) {
    return {
      noteOnly: lostOpportunity.note,
      lead: '',
      body: '',
      range: null,
      isPositive: false,
    };
  }

  const sizeLabel =
    lostOpportunity.size != null
      ? fmtUsd(lostOpportunity.size)
      : fmtUsdShort(vm.slippageDisplaySize).replace('.0', '');
  const lead = `${sizeLabel} purchase → ~${fmtUsd(lostOpportunity.cost || 0)} execution cost.`;
  const isPositive = shouldUsePositiveLostOpportunityCopy(vm);

  if (isPositive) {
    return {
      noteOnly: null,
      lead,
      body:
        'Larger buys still fill with low slippage on the visible book.',
      range: null,
      isPositive: true,
    };
  }

  return {
    noteOnly: null,
    lead,
    body: 'Larger entries typically lose',
    range: lostOpportunity.range || 'significant slippage',
    isPositive: false,
  };
}

export function hasMeaningfulInvestorOverpay(investorSimulator: SimulatorEntry[]): boolean {
  return investorSimulator.some(
    (simulationRow) => !simulationRow.omitted && (simulationRow.overpayPct ?? 0) >= 1,
  );
}

function normalizeVerdictExchangeCasing(verdict: string, exchangeSlug: string, exchange: string): string {
  if (!exchangeSlug) {
    return verdict;
  }
  const pattern = new RegExp(exchangeSlug.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
  return verdict.replace(pattern, exchange);
}

export function executiveSummaryText(vm: TokenViewModel): string {
  const normalizedVerdict = normalizeVerdictExchangeCasing(vm.verdict, vm.exchangeSlug, vm.exchange);

  if (vm.status !== 'Good') {
    return normalizedVerdict;
  }

  const verdictIsPositive = POSITIVE_VERDICT_MARKERS.some((marker) =>
    normalizedVerdict.toLowerCase().includes(marker),
  );
  if (verdictIsPositive) {
    return normalizedVerdict;
  }

  return `${vm.pair} has strong liquidity on ${vm.exchange}. Execution costs stay low at common trade sizes.`;
}

export function investorSimulatorIntro(vm: TokenViewModel): string {
  if (!hasMeaningfulInvestorOverpay(vm.investorSimulator)) {
    return `${vm.pair} trades with tight spreads on ${vm.exchange}. Common buy sizes fill close to fair price with little slippage.`;
  }

  const sizeLabel = fmtUsdShort(vm.slippageDisplaySize).replace('.0', '');
  return `A ${sizeLabel} buy already shows real execution cost. That is a top reason larger investors skip ${vm.pair}.`;
}
