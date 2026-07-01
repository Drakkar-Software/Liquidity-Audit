/** Backend issue keys from analysis.issues[].label — display copy lives here. */

export const ISSUE_CHECK_LABELS = [
  'Good volume',
  'Wide spread',
  'Low depth',
  'High slippage',
  'Quote gaps',
] as const;

export type IssueCheckLabel = (typeof ISSUE_CHECK_LABELS)[number];

export interface IssueTooltipContent {
  title: string;
  body: string;
}

interface IssueCheckCopy {
  passText: string;
  failText: string;
  tooltip: IssueTooltipContent;
}

const ISSUE_CHECK_COPY: Record<IssueCheckLabel, IssueCheckCopy> = {
  'Good volume': {
    passText: 'Adequate volume',
    failText: 'Low volume',
    tooltip: {
      title: 'Volume',
      body: '24h quote volume compared to the median for active pairs on this exchange.',
    },
  },
  'Wide spread': {
    passText: 'Tight spread',
    failText: 'Wide spread',
    tooltip: {
      title: 'Spread',
      body: 'Best bid/ask spread from the snapshot vs a configured maximum.',
    },
  },
  'Low depth': {
    passText: 'Solid depth',
    failText: 'Thin depth',
    tooltip: {
      title: 'Depth',
      body:
        'Resting liquidity when bid/ask depth or total visible depth falls below configured minimums.',
    },
  },
  'High slippage': {
    passText: 'Low slippage',
    failText: 'High slippage',
    tooltip: {
      title: 'Slippage',
      body:
        'Buy slippage at the report trade size vs the median of up to 3 similar-volume peers.',
    },
  },
  'Quote gaps': {
    passText: 'Continuous quotes',
    failText: 'Quote gaps',
    tooltip: {
      title: 'Quote gaps',
      body: 'Bid and ask price levels in the visible book vs minimum level counts.',
    },
  },
};

export const DELISTING_RISK_CHIP_TEXT = 'Delisting risk';

export const DELISTING_RISK_TOOLTIP: IssueTooltipContent = {
  title: 'Delisting risk',
  body:
    'Depth and/or 24h volume below exchange-style delisting minimums used in this audit. Not a guarantee of delisting.',
};

export const ALL_CHECKS_PASSED_TOOLTIP: IssueTooltipContent = {
  title: 'All checks passed',
  body: 'All five liquidity checks passed at snapshot time.',
};

function isIssueCheckLabel(label: string): label is IssueCheckLabel {
  return (ISSUE_CHECK_LABELS as readonly string[]).includes(label);
}

export function getIssueChipDisplay(
  label: string,
  ok: boolean,
): { text: string; tooltip: IssueTooltipContent | null } {
  if (!isIssueCheckLabel(label)) {
    return { text: label, tooltip: null };
  }
  const copy = ISSUE_CHECK_COPY[label];
  return {
    text: ok ? copy.passText : copy.failText,
    tooltip: copy.tooltip,
  };
}

export function getFailedIssueDisplayLabel(label: string): string {
  if (!isIssueCheckLabel(label)) {
    return label.toLowerCase();
  }
  return ISSUE_CHECK_COPY[label].failText.toLowerCase();
}
