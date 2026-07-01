import type { Improvement, TokenViewModel } from '../types';

function parseMetricPercent(text: string | null | undefined): number | null {
  if (text == null || text === '' || text === '—') {
    return null;
  }
  const parsed = parseFloat(String(text).replace('%', ''));
  return Number.isNaN(parsed) ? null : parsed;
}

function parseMetricUsd(text: string | null | undefined): number | null {
  if (text == null || text === '' || text === '—') {
    return null;
  }
  const normalized = String(text).replace('$', '').replace(/,/g, '').trim();
  if (normalized.endsWith('k')) {
    return parseFloat(normalized) * 1000;
  }
  if (normalized.endsWith('M')) {
    return parseFloat(normalized) * 1_000_000;
  }
  if (normalized.endsWith('B')) {
    return parseFloat(normalized) * 1_000_000_000;
  }
  const parsed = parseFloat(normalized);
  return Number.isNaN(parsed) ? null : parsed;
}

/** Mirrors IssueChips: every check passes and no delisting risk. */
export function allIssuesPassed(vm: TokenViewModel): boolean {
  return (
    vm.issues.length > 0 &&
    vm.issues.every((issue) => issue.ok) &&
    vm.delistingRisk.length === 0
  );
}

/** Port of wireframe improvementsHaveMeaningfulGap (dynamic-report.js). */
export function improvementsHaveMeaningfulGap(improvements: Improvement[]): boolean {
  return improvements.some((row) => {
    if (row.metric === 'Spread') {
      const currentSpread = parseMetricPercent(row.current);
      const potentialSpread = parseMetricPercent(row.potential);
      return (
        currentSpread != null &&
        potentialSpread != null &&
        currentSpread > potentialSpread + 0.05
      );
    }
    if (row.metric.indexOf('Depth') !== -1) {
      const currentDepth = parseMetricUsd(row.current);
      const potentialDepth = parseMetricUsd(row.potential);
      return (
        currentDepth != null &&
        potentialDepth != null &&
        currentDepth < potentialDepth * 0.95
      );
    }
    if (row.metric.indexOf('Slippage') !== -1) {
      const currentSlippage = parseMetricPercent(row.current);
      const potentialSlippage = parseMetricPercent(row.potential);
      if (currentSlippage == null) {
        return potentialSlippage != null && potentialSlippage > 0.1;
      }
      return potentialSlippage != null && currentSlippage > potentialSlippage + 0.05;
    }
    return false;
  });
}

export function shouldShowImprovements(vm: TokenViewModel): boolean {
  return !allIssuesPassed(vm) && improvementsHaveMeaningfulGap(vm.improvements);
}
