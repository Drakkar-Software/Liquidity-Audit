// Small formatting helpers shared across report sections.

/** 12345 -> "$12,345" */
export const fmtUsd = (n: number): string =>
  '$' + Math.round(n).toLocaleString('en-US');

/** 3525 -> "+$3,525" ; -820 -> "−$820" (uses a real minus sign) */
export const fmtSignedUsd = (n: number): string =>
  (n >= 0 ? '+' : '−') + '$' + Math.abs(Math.round(n)).toLocaleString('en-US');

/** 8.2 -> "8.2%" */
export const fmtPct = (n: number): string => `${n}%`;

/** 9500 -> "$9.5k" ; 100000 -> "$100k" ; 3400000 -> "$3.4M" */
export const fmtUsdShort = (n: number): string => {
  const abs = Math.abs(n);
  if (abs >= 1e9) return `$${trim(n / 1e9)}B`;
  if (abs >= 1e6) return `$${trim(n / 1e6)}M`;
  if (abs >= 1e3) return `$${trim(n / 1e3)}k`;
  return `$${trim(n)}`;
};

/** 18000000000 -> "18.0B" (no leading $) — used for rankings volume. */
export const fmtVolShort = (n: number): string => {
  const abs = Math.abs(n);
  if (abs >= 1e9) return `${(n / 1e9).toFixed(1)}B`;
  if (abs >= 1e6) return `${(n / 1e6).toFixed(0)}M`;
  if (abs >= 1e3) return `${(n / 1e3).toFixed(0)}k`;
  return `${n}`;
};

function trim(n: number): string {
  // 9.5 -> "9.5" ; 100 -> "100"
  const r = Math.round(n * 10) / 10;
  return Number.isInteger(r) ? String(r) : r.toFixed(1);
}
