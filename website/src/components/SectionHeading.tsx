import React from 'react';
import { colors, fonts } from '../theme';

export interface SectionHeadingProps {
  title: string;
  /** Optional muted suffix shown after the title, e.g. "vs Mexc average". */
  sub?: string;
}

/** Heading row used by report detail sections. */
export function SectionHeading({ title, sub }: SectionHeadingProps) {
  return (
    <div className="token-report-section-heading">
      <h2 style={{ font: `600 15px ${fonts.sans}`, color: colors.ink }}>
        {title}
        {sub ? <span style={{ color: colors.ink3, fontWeight: 400 }}> {sub}</span> : null}
      </h2>
    </div>
  );
}

/** The accent eyebrow label, e.g. "METRIC FORMULAS". */
export function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        font: `500 11px ${fonts.mono}`,
        letterSpacing: '.1em',
        color: colors.accent,
        marginBottom: 12,
      }}
    >
      {children}
    </div>
  );
}
