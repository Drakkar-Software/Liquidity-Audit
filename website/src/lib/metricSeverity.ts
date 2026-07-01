import { colors } from '../theme';

export type MetricComparison = 'good' | 'worst' | 'neutral';
export type OverpaySeverity = 'good' | 'fair' | 'poor';

export type PeerMetricName = 'depth' | 'spread' | 'slippagePct';

const GOOD_RATIO = 1.25;
const WORST_RATIO = 0.75;

/** Compare a Yours peer metric to the median row (wireframe peerMetricCellClass). */
export function peerMetricComparison(
  yoursValue: number,
  medianValue: number,
  metric: PeerMetricName,
): MetricComparison {
  if (medianValue <= 0) {
    return 'neutral';
  }

  if (metric === 'depth') {
    if (yoursValue < medianValue * WORST_RATIO) {
      return 'worst';
    }
    if (yoursValue > medianValue * GOOD_RATIO) {
      return 'good';
    }
    return 'neutral';
  }

  if (yoursValue > medianValue * GOOD_RATIO) {
    return 'worst';
  }
  if (yoursValue < medianValue * WORST_RATIO) {
    return 'good';
  }
  return 'neutral';
}

/** Classify investor simulator overpay (wireframe overpaySeverityClass). */
export function overpaySeverity(overpayPct: number | null): OverpaySeverity {
  if (overpayPct == null || overpayPct < 1) {
    return 'good';
  }
  if (overpayPct <= 5) {
    return 'fair';
  }
  return 'poor';
}

export function comparisonColor(comparison: MetricComparison): string {
  if (comparison === 'good') {
    return colors.green;
  }
  if (comparison === 'worst') {
    return colors.red;
  }
  return colors.accent;
}

export function comparisonTextColor(comparison: MetricComparison): string {
  if (comparison === 'good') {
    return colors.green;
  }
  if (comparison === 'worst') {
    return colors.red;
  }
  return colors.accent;
}

export function overpaySeverityColor(severity: OverpaySeverity): string {
  if (severity === 'good') {
    return colors.green;
  }
  if (severity === 'fair') {
    return colors.amber;
  }
  return colors.red;
}

export function overpaySeverityBorderColor(severity: OverpaySeverity): string {
  if (severity === 'good') {
    return colors.green;
  }
  if (severity === 'fair') {
    return colors.amber;
  }
  return colors.red;
}
