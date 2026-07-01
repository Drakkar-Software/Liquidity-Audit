import { colors } from '../../theme';
import { GuideIllustrationFrame } from './GuideIllustrationFrame';

export interface LiquidityScoreIllustrationProps {
  variant?: 'default' | 'grades' | 'example';
}

const GRADE_LABELS = ['A', 'B', 'C', 'D', 'F'];
const GRADE_STROKES = [colors.green, colors.green, colors.amber, colors.red, colors.red];

export function LiquidityScoreIllustration({ variant = 'default' }: LiquidityScoreIllustrationProps) {
  if (variant === 'example') {
    return (
      <GuideIllustrationFrame width={160} height={96}>
        <circle cx={56} cy={48} r={24} fill="none" stroke={colors.line2} strokeWidth={5} />
        <circle
          cx={56}
          cy={48}
          r={24}
          fill="none"
          stroke={colors.amber}
          strokeWidth={5}
          strokeDasharray="95 151"
          strokeLinecap="round"
          transform="rotate(-90 56 48)"
        />
        <text x={56} y={52} textAnchor="middle" fill={colors.amber} fontSize={16} fontFamily="IBM Plex Mono, monospace">
          68
        </text>
        <text x={56} y={64} textAnchor="middle" fill={colors.ink3} fontSize={6} fontFamily="IBM Plex Mono, monospace">
          /100
        </text>
        <text x={112} y={36} textAnchor="middle" fill={colors.amber} fontSize={14} fontFamily="IBM Plex Mono, monospace">
          C
        </text>
        <text x={112} y={52} textAnchor="middle" fill={colors.ink3} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          spr 0.12%
        </text>
        <text x={112} y={66} textAnchor="middle" fill={colors.ink3} fontSize={7} fontFamily="IBM Plex Mono, monospace">
          $5k +0.31%
        </text>
      </GuideIllustrationFrame>
    );
  }

  if (variant === 'grades') {
    return (
      <GuideIllustrationFrame width={140} height={88}>
        {GRADE_LABELS.map((gradeLabel, gradeIndex) => (
          <rect
            key={gradeLabel}
            x={18 + gradeIndex * 22}
            y={32}
            width={18}
            height={22}
            rx={3}
            fill={colors.panel2}
            stroke={GRADE_STROKES[gradeIndex]}
            strokeWidth={1}
          />
        ))}
        {GRADE_LABELS.map((gradeLabel, gradeIndex) => (
          <text
            key={`${gradeLabel}-label`}
            x={27 + gradeIndex * 22}
            y={47}
            textAnchor="middle"
            fill={colors.ink2}
            fontSize={9}
            fontFamily="IBM Plex Mono, monospace"
          >
            {gradeLabel}
          </text>
        ))}
      </GuideIllustrationFrame>
    );
  }

  return (
    <GuideIllustrationFrame width={140} height={88}>
      <circle cx={70} cy={48} r={28} fill="none" stroke={colors.line2} strokeWidth={6} />
      <circle
        cx={70}
        cy={48}
        r={28}
        fill="none"
        stroke={colors.accent}
        strokeWidth={6}
        strokeDasharray="110 176"
        strokeLinecap="round"
        transform="rotate(-90 70 48)"
      />
      <text x={70} y={52} textAnchor="middle" fill={colors.accent} fontSize={18} fontFamily="IBM Plex Mono, monospace">
        72
      </text>
      <text x={70} y={66} textAnchor="middle" fill={colors.ink3} fontSize={7} fontFamily="IBM Plex Mono, monospace">
        /100
      </text>
    </GuideIllustrationFrame>
  );
}
