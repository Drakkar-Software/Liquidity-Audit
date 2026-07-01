import { colors } from '../../theme';
import { GuideIllustrationFrame } from './GuideIllustrationFrame';

export interface OrderBookIllustrationProps {
  variant?: 'default' | 'depth' | 'example';
}

export function OrderBookIllustration({ variant = 'default' }: OrderBookIllustrationProps) {
  if (variant === 'example') {
    return (
      <GuideIllustrationFrame width={160} height={96}>
        <text x={12} y={16} fill={colors.ink3} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          mid 100.025
        </text>
        <rect x={12} y={22} width={68} height={6} rx={1} fill="rgba(70,196,106,.4)" />
        <text x={14} y={27} fill={colors.ink2} fontSize={6} fontFamily="IBM Plex Mono, monospace">
          100.00 · 45k
        </text>
        <rect x={12} y={32} width={52} height={5} rx={1} fill="rgba(70,196,106,.25)" />
        <text x={14} y={36} fill={colors.ink3} fontSize={6} fontFamily="IBM Plex Mono, monospace">
          99.98 · 22k
        </text>
        <rect x={80} y={26} width={68} height={6} rx={1} fill="rgba(240,88,77,.4)" />
        <text x={82} y={31} fill={colors.ink2} fontSize={6} fontFamily="IBM Plex Mono, monospace">
          100.05 · 38k
        </text>
        <rect x={34} y={48} width={92} height={28} rx={3} fill="rgba(54,214,195,.1)" stroke={colors.accent} strokeWidth={1} />
        <text x={80} y={66} textAnchor="middle" fill={colors.accent} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          ±2% $312k / $284k
        </text>
      </GuideIllustrationFrame>
    );
  }

  if (variant === 'depth') {
    return (
      <GuideIllustrationFrame>
        <rect x={34} y={22} width={72} height={40} rx={3} fill="rgba(54,214,195,.12)" stroke={colors.accent} strokeWidth={1} />
        <line x1={70} y1={22} x2={70} y2={62} stroke={colors.accent} strokeWidth={1} strokeDasharray="2 2" />
        <rect x={38} y={34} width={28} height={5} rx={1} fill="rgba(70,196,106,.45)" />
        <rect x={74} y={38} width={28} height={5} rx={1} fill="rgba(240,88,77,.45)" />
        <text x={70} y={76} textAnchor="middle" fill={colors.ink3} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          depth band
        </text>
      </GuideIllustrationFrame>
    );
  }

  return (
    <GuideIllustrationFrame>
      <rect x={48} y={18} width={44} height={52} rx={3} fill="rgba(54,214,195,.08)" stroke={colors.accent} strokeWidth={1} />
      <rect x={20} y={30} width={24} height={6} rx={1} fill="rgba(70,196,106,.4)" />
      <rect x={16} y={40} width={32} height={5} rx={1} fill="rgba(70,196,106,.25)" />
      <rect x={12} y={49} width={36} height={5} rx={1} fill="rgba(70,196,106,.15)" />
      <rect x={96} y={34} width={24} height={6} rx={1} fill="rgba(240,88,77,.4)" />
      <rect x={92} y={44} width={32} height={5} rx={1} fill="rgba(240,88,77,.25)" />
      <rect x={88} y={53} width={36} height={5} rx={1} fill="rgba(240,88,77,.15)" />
      <text x={70} y={84} textAnchor="middle" fill={colors.ink3} fontSize={7} fontFamily="IBM Plex Mono, monospace">
        ±2% depth
      </text>
    </GuideIllustrationFrame>
  );
}
