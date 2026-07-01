import { colors } from '../../theme';
import { GuideIllustrationFrame } from './GuideIllustrationFrame';

export function MethodologyStepFlowIllustration() {
  return (
    <GuideIllustrationFrame width={160} height={72}>
      <rect x={12} y={24} width={36} height={24} rx={4} fill={colors.panel2} stroke={colors.line2} />
      <text x={30} y={40} textAnchor="middle" fill={colors.ink2} fontSize={7} fontFamily="IBM Plex Sans, sans-serif">
        Exchange
      </text>
      <path d="M52 36h16" stroke={colors.accent} strokeWidth={1.5} />
      <polygon points="68,36 64,33 64,39" fill={colors.accent} />
      <rect x={72} y={24} width={36} height={24} rx={4} fill={colors.panel2} stroke={colors.line2} />
      <text x={90} y={40} textAnchor="middle" fill={colors.ink2} fontSize={7} fontFamily="IBM Plex Sans, sans-serif">
        Search
      </text>
      <path d="M112 36h16" stroke={colors.accent} strokeWidth={1.5} />
      <polygon points="128,36 124,33 124,39" fill={colors.accent} />
      <rect x={132} y={24} width={16} height={24} rx={4} fill={colors.panel2} stroke={colors.accent} />
    </GuideIllustrationFrame>
  );
}
