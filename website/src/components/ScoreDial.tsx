import { colors, fonts } from '../theme';
import type { Status } from '../types';

export interface ScoreDialProps {
  score: number; // 0–100
  grade: string;
  status: Status;
  /** Ring + text color. Defaults caller should pass statusColor(status). */
  color: string;
}

/**
 * The conic-gradient score dial used in the cockpit panel.
 * Ring fills `score`% in `color`, remainder in a neutral track.
 */
export function ScoreDial({ score, color }: ScoreDialProps) {
  return (
    <div
      className="token-report-score-dial"
      style={{
        position: 'relative',
        width: 128,
        height: 128,
        borderRadius: '50%',
        background: `conic-gradient(${color} 0% ${score}%, var(--score-dial-track, #1c232c) ${score}% 100%)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      <div
        className="token-report-score-dial-inner"
        style={{
          position: 'absolute',
          inset: 11,
          borderRadius: '50%',
          background: colors.screen,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <span className="token-report-score-value" style={{ font: `700 44px/1 ${fonts.mono}`, color }}>
          {score}
        </span>
        <span
          className="token-report-score-denominator"
          style={{ font: `500 10px ${fonts.mono}`, color: colors.ink3, letterSpacing: '.1em' }}
        >
          /100
        </span>
      </div>
    </div>
  );
}

/** Grade + status label shown next to the dial. */
export function GradeBadge({ grade, status, color }: { grade: string; status: Status; color: string }) {
  return (
    <div className="token-report-grade-badge">
      <div className="token-report-grade-letter" style={{ font: `700 30px ${fonts.mono}`, color, lineHeight: 1 }}>
        {grade}
      </div>
      <div
        className="token-report-grade-status"
        style={{ font: `600 12px ${fonts.mono}`, letterSpacing: '.1em', color, marginTop: 4 }}
      >
        {status.toUpperCase()}
      </div>
    </div>
  );
}
