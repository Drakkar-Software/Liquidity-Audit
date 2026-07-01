import { colors, fonts } from '../theme';

const SKELETON_ROW_COUNT = 8;
const QUICK_LINK_SKELETON_COUNT = 4;

const skeletonBarStyle = {
  display: 'block',
  height: 10,
  borderRadius: 4,
  background: colors.panel2,
} as const;

export function QuickLinksSkeleton() {
  return (
    <div
      data-testid="quick-links-skeleton"
      style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 22, flexWrap: 'wrap' }}
      aria-hidden="true"
    >
      <span style={{ font: `500 11px ${fonts.sans}`, color: colors.ink3, alignSelf: 'center' }}>
        Quick links:
      </span>
      {Array.from({ length: QUICK_LINK_SKELETON_COUNT }, (_, index) => (
        <span
          key={index}
          style={{
            width: 72,
            height: 30,
            borderRadius: 20,
            background: colors.panel2,
            border: `1px solid ${colors.line}`,
          }}
        />
      ))}
    </div>
  );
}

export function RankingsTableSkeleton() {
  return (
    <div data-testid="rankings-table-skeleton" aria-busy="true">
      <span
        role="status"
        style={{
          position: 'absolute',
          width: 1,
          height: 1,
          padding: 0,
          margin: -1,
          overflow: 'hidden',
          clip: 'rect(0,0,0,0)',
          whiteSpace: 'nowrap',
          border: 0,
        }}
      >
        Loading rankings…
      </span>
      <p style={{ margin: '0 0 12px', font: `400 12px ${fonts.sans}`, color: colors.ink3 }}>
        Top 20 spot pairs by liquidity score (24h volume ≥ $1k).{' '}
        <span
          aria-hidden="true"
          style={{ ...skeletonBarStyle, display: 'inline-block', width: 120, verticalAlign: 'middle' }}
        />
      </p>

      <div className="rankings-scroll" style={{ borderColor: colors.line }}>
        <div className="rankings-table">
          <div
            className="rankings-grid"
            style={{
              background: colors.tableHead,
              borderBottom: `1px solid ${colors.line}`,
              font: `500 10px ${fonts.mono}`,
              letterSpacing: '.08em',
              color: colors.ink3,
            }}
          >
            <span style={{ padding: '10px 16px' }}>#</span>
            <span style={{ padding: '10px 16px' }}>PROJECT</span>
            <span style={{ padding: '10px 16px', textAlign: 'right' }}>SCORE</span>
            <span style={{ padding: '10px 16px', textAlign: 'right' }}>24H VOL</span>
          </div>
          {Array.from({ length: SKELETON_ROW_COUNT }, (_, rowIndex) => (
            <div
              key={rowIndex}
              className="rankings-grid"
              aria-hidden="true"
              style={{
                borderBottom: rowIndex < SKELETON_ROW_COUNT - 1 ? `1px solid ${colors.line}` : 'none',
                padding: '10px 16px',
                alignItems: 'center',
              }}
            >
              <span style={{ ...skeletonBarStyle, width: 16 }} />
              <span style={{ ...skeletonBarStyle, width: '70%', maxWidth: 140 }} />
              <span style={{ ...skeletonBarStyle, width: 28, marginLeft: 'auto' }} />
              <span style={{ ...skeletonBarStyle, width: 40, marginLeft: 'auto' }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
