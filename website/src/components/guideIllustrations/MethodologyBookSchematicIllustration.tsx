import { colors } from '../../theme';
import { GuideIllustrationFrame } from './GuideIllustrationFrame';

export function MethodologyBookSchematicIllustration() {
  return (
    <GuideIllustrationFrame width={160} height={72}>
      <line x1={80} y1={16} x2={80} y2={56} stroke={colors.accent} strokeWidth={1} strokeDasharray="2 2" />
      <rect x={22} y={30} width={50} height={6} rx={1} fill="rgba(70,196,106,.35)" />
      <rect x={18} y={40} width={40} height={5} rx={1} fill="rgba(70,196,106,.2)" />
      <rect x={88} y={26} width={50} height={6} rx={1} fill="rgba(240,88,77,.35)" />
      <rect x={102} y={36} width={40} height={5} rx={1} fill="rgba(240,88,77,.2)" />
      <text x={22} y={24} fill={colors.ink3} fontSize={7} fontFamily="IBM Plex Mono, monospace">
        spread
      </text>
      <text x={88} y={22} fill={colors.ink3} fontSize={7} fontFamily="IBM Plex Mono, monospace">
        depth
      </text>
    </GuideIllustrationFrame>
  );
}
