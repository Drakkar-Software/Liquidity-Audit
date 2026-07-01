import { colors } from '../../theme';
import { GuideIllustrationFrame } from './GuideIllustrationFrame';

export interface CryptoLiquidityIllustrationProps {
  variant?: 'default' | 'example';
}

export function CryptoLiquidityIllustration({ variant = 'default' }: CryptoLiquidityIllustrationProps) {
  if (variant === 'example') {
    return (
      <GuideIllustrationFrame width={160} height={96}>
        <text x={12} y={18} fill={colors.green} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          bid 142.50
        </text>
        <text x={88} y={18} fill={colors.red} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          ask 142.58
        </text>
        <line x1={80} y1={12} x2={80} y2={72} stroke={colors.accent} strokeWidth={1} strokeDasharray="3 3" />
        <rect x={20} y={28} width={52} height={8} rx={2} fill="rgba(70,196,106,.35)" />
        <rect x={88} y={32} width={52} height={8} rx={2} fill="rgba(240,88,77,.35)" />
        <rect x={96} y={44} width={40} height={6} rx={1} fill="rgba(240,88,77,.2)" />
        <text x={80} y={62} textAnchor="middle" fill={colors.accent} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          spread 0.056%
        </text>
        <text x={80} y={74} textAnchor="middle" fill={colors.ink3} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          $10k buy +0.18%
        </text>
      </GuideIllustrationFrame>
    );
  }

  return (
    <GuideIllustrationFrame>
      <line x1={70} y1={12} x2={70} y2={76} stroke={colors.accent} strokeWidth={1} strokeDasharray="3 3" />
      <rect x={24} y={28} width={38} height={10} rx={2} fill="rgba(70,196,106,.35)" />
      <rect x={24} y={42} width={30} height={8} rx={2} fill="rgba(70,196,106,.2)" />
      <rect x={78} y={36} width={38} height={10} rx={2} fill="rgba(240,88,77,.35)" />
      <rect x={86} y={50} width={30} height={8} rx={2} fill="rgba(240,88,77,.2)" />
      <text x={24} y={24} fill={colors.ink3} fontSize={8} fontFamily="IBM Plex Mono, monospace">
        bid
      </text>
      <text x={98} y={24} fill={colors.ink3} fontSize={8} fontFamily="IBM Plex Mono, monospace">
        ask
      </text>
    </GuideIllustrationFrame>
  );
}
