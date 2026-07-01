import type { ReactNode } from 'react';
import { colors } from '../../theme';

export interface GuideIllustrationFrameProps {
  children: ReactNode;
  width?: number;
  height?: number;
}

/** Shared wrapper for decorative guide SVGs. */
export function GuideIllustrationFrame({
  children,
  width = 140,
  height = 88,
}: GuideIllustrationFrameProps) {
  return (
    <svg
      aria-hidden
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{ display: 'block', flexShrink: 0 }}
    >
      <rect x={0} y={0} width={width} height={height} rx={8} fill={colors.panel} stroke={colors.line} />
      <g className="guide-illustration-motion">{children}</g>
    </svg>
  );
}
