import { colors } from '../../theme';
import { GuideIllustrationFrame } from './GuideIllustrationFrame';

export interface BidAskSpreadIllustrationProps {
  variant?: 'default' | 'analysis' | 'example';
}

export function BidAskSpreadIllustration({ variant = 'default' }: BidAskSpreadIllustrationProps) {
  if (variant === 'example') {
    return (
      <GuideIllustrationFrame width={160} height={96}>
        <text x={16} y={24} fill={colors.green} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          bid 1.0002
        </text>
        <text x={88} y={24} fill={colors.red} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          ask 1.0008
        </text>
        <line x1={24} y1={38} x2={136} y2={38} stroke={colors.line2} strokeWidth={1} />
        <rect x={28} y={32} width={4} height={14} rx={1} fill={colors.green} />
        <rect x={128} y={28} width={4} height={18} rx={1} fill={colors.red} />
        <line x1={36} y1={48} x2={124} y2={48} stroke={colors.accent} strokeWidth={2} />
        <text x={80} y={62} textAnchor="middle" fill={colors.ink3} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          mid 1.0005
        </text>
        <text x={80} y={76} textAnchor="middle" fill={colors.accent} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          spread 0.060%
        </text>
      </GuideIllustrationFrame>
    );
  }

  if (variant === 'analysis') {
    return (
      <GuideIllustrationFrame>
        <rect x={24} y={30} width={92} height={28} rx={4} fill={colors.panel2} stroke={colors.line2} />
        <rect x={32} y={40} width={4} height={12} rx={1} fill={colors.green} />
        <rect x={104} y={36} width={4} height={16} rx={1} fill={colors.red} />
        <line x1={40} y1={52} x2={100} y2={52} stroke={colors.accent} strokeWidth={2} />
        <text x={70} y={26} textAnchor="middle" fill={colors.accent} fontSize={8} fontFamily="IBM Plex Mono, monospace">
          spread %
        </text>
      </GuideIllustrationFrame>
    );
  }

  return (
    <GuideIllustrationFrame>
      <line x1={20} y1={44} x2={120} y2={44} stroke={colors.line2} strokeWidth={1} />
      <rect x={28} y={36} width={4} height={16} rx={1} fill={colors.green} />
      <text x={18} y={32} fill={colors.green} fontSize={8} fontFamily="IBM Plex Mono, monospace">
        bid
      </text>
      <rect x={88} y={32} width={4} height={20} rx={1} fill={colors.red} />
      <text x={98} y={28} fill={colors.red} fontSize={8} fontFamily="IBM Plex Mono, monospace">
        ask
      </text>
      <line x1={36} y1={52} x2={88} y2={52} stroke={colors.accent} strokeWidth={1} />
      <text x={52} y={66} fill={colors.accent} fontSize={8} fontFamily="IBM Plex Mono, monospace">
        spread
      </text>
    </GuideIllustrationFrame>
  );
}
