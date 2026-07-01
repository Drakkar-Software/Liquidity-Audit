// Design tokens for Liquidity Audit.
// Mirror of the CSS custom properties used in the original mockup.

export const colors = {
  accent: '#36d6c3',
  accentInk: '#06231f', // text/icon color on accent fills
  canvas: '#191c22',
  screen: '#0a0d12',
  panel: '#0f141b',
  panel2: '#131a23',
  line: '#1d242e',
  line2: '#2a323d',
  ink: '#e8edf2',
  ink2: '#9aa7b4',
  ink3: '#5f6b78',
  red: '#f0584d',
  amber: '#e0a83a',
  green: '#46c46a',
  navBg: '#0c1016',
  tableHead: '#0c1117',
} as const;

export const fonts = {
  sans: "'IBM Plex Sans', system-ui, -apple-system, sans-serif",
  mono: "'IBM Plex Mono', ui-monospace, SFMono-Regular, monospace",
} as const;

export type Status = 'Good' | 'Fair' | 'Poor';
export type Severity = 'Critical' | 'Moderate' | 'Low';

/** Primary color for a score/status (used for grade, dial, etc.). */
export function statusColor(status: Status): string {
  if (status === 'Good') return colors.green;
  if (status === 'Fair') return colors.amber;
  return colors.red;
}

/** Faint tinted background for the score block, matched to status. */
export function statusTint(status: Status): string {
  if (status === 'Good') return 'rgba(70,196,106,.05)';
  if (status === 'Fair') return 'rgba(224,168,58,.05)';
  return 'rgba(240,88,77,.04)';
}

/** Color for a health-metric severity. */
export function severityColor(severity: Severity): string {
  if (severity === 'Critical') return colors.red;
  if (severity === 'Moderate') return colors.amber;
  return colors.green;
}
