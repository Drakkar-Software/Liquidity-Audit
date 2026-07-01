import { colors } from '../../theme';
import { GuideIllustrationFrame } from './GuideIllustrationFrame';

const GRADE_COLORS = [colors.green, colors.green, colors.amber, colors.red, colors.red];
const GRADE_LABELS = ['A', 'B', 'C', 'D', 'F'];

export function MethodologyGradeStripIllustration() {
  return (
    <GuideIllustrationFrame width={160} height={72}>
      {GRADE_LABELS.map((gradeLabel, gradeIndex) => (
        <g key={gradeLabel}>
          <rect
            x={14 + gradeIndex * 28}
            y={28}
            width={24}
            height={24}
            rx={4}
            fill={`${GRADE_COLORS[gradeIndex]}22`}
            stroke={GRADE_COLORS[gradeIndex]}
            strokeWidth={1}
          />
          <text
            x={26 + gradeIndex * 28}
            y={44}
            textAnchor="middle"
            fill={GRADE_COLORS[gradeIndex]}
            fontSize={11}
            fontFamily="IBM Plex Mono, monospace"
          >
            {gradeLabel}
          </text>
        </g>
      ))}
    </GuideIllustrationFrame>
  );
}
