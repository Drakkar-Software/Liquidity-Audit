import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import '../print.css';
import { colors, fonts, statusColor, statusTint, severityColor } from '../theme';
import type { TokenViewModel, PeerRow } from '../types';
import { Screen } from '../components/Screen';
import { PdfPrintHeader } from '../components/PdfPrintHeader';
import { ScoreDial, GradeBadge } from '../components/ScoreDial';
import { IssueChips } from '../components/IssueChips';
import { SectionHeading } from '../components/SectionHeading';
import { exportTokenReportPdf } from '../lib/pdfExport';
import { copyPageUrl } from '../lib/copyPageUrl';
import {
  executiveSummaryText,
  investorSimulatorIntro,
  lostOpportunityText,
} from '../lib/reportCopy';
import { shouldShowImprovements } from '../lib/reportVisibility';
import { fmtSignedUsd, fmtUsdShort } from '../format';
import { pairToSlug } from '../lib/data/loader';
import {
  comparisonColor,
  comparisonTextColor,
  overpaySeverity,
  overpaySeverityBorderColor,
  overpaySeverityColor,
  peerMetricComparison,
} from '../lib/metricSeverity';

export interface TokenReportProps {
  vm: TokenViewModel;
}

/**
 * Token report — "Split Cockpit" layout.
 *
 * Left: persistent command panel (score dial, verdict, issues, delisting, actions).
 * Right: scrolling evidence report. Every detail section is conditional —
 * when its backing data is empty/null the section (and its heading) is omitted,
 * so a healthy pair collapses to just the score + peer comparison with no
 * orphaned headings.
 */
export function TokenReport({ vm }: TokenReportProps) {
  const accent = statusColor(vm.status);

  return (
    <Screen>
      <div className="token-report-print">
        <PdfPrintHeader vm={vm} />
        <div className="token-report-layout">
          <Cockpit vm={vm} accent={accent} />
          <Detail vm={vm} />
        </div>
      </div>
    </Screen>
  );
}

// ---------------------------------------------------------------------------
// Left cockpit
// ---------------------------------------------------------------------------
function Cockpit({ vm, accent }: { vm: TokenViewModel; accent: string }) {
  const [shareCopied, setShareCopied] = useState(false);
  const [shareFailed, setShareFailed] = useState(false);

  useEffect(() => {
    if (!shareCopied && !shareFailed) {
      return;
    }
    const timeoutId = window.setTimeout(() => {
      setShareCopied(false);
      setShareFailed(false);
    }, 2000);
    return () => window.clearTimeout(timeoutId);
  }, [shareCopied, shareFailed]);

  const handleShareLink = () => {
    void copyPageUrl(window.location.href).then(
      () => {
        setShareFailed(false);
        setShareCopied(true);
      },
      () => {
        setShareCopied(false);
        setShareFailed(true);
      },
    );
  };

  return (
    <div
      className="token-report-cockpit"
      style={{
        background: 'linear-gradient(180deg,#140d0e,#0a0d12)',
        padding: '32px 28px',
        display: 'flex',
        flexDirection: 'column',
        gap: 28,
        alignSelf: 'stretch',
      }}
    >
      {/* pair identity */}
      <div className="token-report-pair-header">
        <div className="token-report-pair-identity">
          <div style={{ font: `600 22px ${fonts.mono}`, color: colors.ink }}>{vm.pair}</div>
          <div style={{ font: `400 12px ${fonts.sans}`, color: colors.ink2 }}>
            {vm.projectName} · {vm.exchange}
          </div>
        </div>
        <div
          className="token-report-pair-meta"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            font: `500 11px ${fonts.mono}`,
            color: colors.ink3,
          }}
        >
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: colors.green }} />
          {vm.updatedAgo}
        </div>
      </div>

      <div className="token-report-hero">
        <div
          className="token-report-score-block"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 22,
            padding: 22,
            border: `1px solid ${colors.line}`,
            borderRadius: 12,
            background: statusTint(vm.status),
          }}
        >
          <div className="print-only token-report-score-compact">
            <div className="token-report-score-points">
              <span className="token-report-score-value" style={{ font: `700 28px/1 ${fonts.mono}`, color: accent }}>
                {vm.score}
              </span>
              <span
                className="token-report-score-denominator"
                style={{ font: `500 10px ${fonts.mono}`, color: colors.ink3, letterSpacing: '.1em' }}
              >
                /100
              </span>
            </div>
            <div className="token-report-grade-group">
              <span className="token-report-grade-letter" style={{ font: `700 28px/1 ${fonts.mono}`, color: accent }}>
                {vm.grade}
              </span>
              <span
                className="token-report-grade-status"
                style={{ font: `600 9px ${fonts.mono}`, letterSpacing: '.1em', color: accent }}
              >
                {vm.status.toUpperCase()}
              </span>
            </div>
          </div>
          <div className="no-print token-report-score-compact">
            <ScoreDial score={vm.score} grade={vm.grade} status={vm.status} color={accent} />
            <GradeBadge grade={vm.grade} status={vm.status} color={accent} />
          </div>
        </div>

        <div className="token-report-verdict">
          <div
            style={{
              font: `500 10px ${fonts.mono}`,
              letterSpacing: '.1em',
              color: colors.ink3,
              marginBottom: 8,
            }}
          >
            SUMMARY
          </div>
          <p className="token-report-verdict-text" style={{ margin: 0, font: `500 17px/1.5 ${fonts.sans}`, color: colors.ink }}>
            {executiveSummaryText(vm)}
          </p>
        </div>
      </div>

      {/* issues */}
      <div className="token-report-issues">
        <IssueChips issues={vm.issues} delistingRisk={vm.delistingRisk} />
      </div>

      {/* delisting notice */}
      {vm.delistingRisk.length > 0 ? (
        <div
          className="token-report-delisting-notice"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            border: '1px solid rgba(224,168,58,.35)',
            background: 'rgba(224,168,58,.07)',
            borderRadius: 7,
            padding: '11px 14px',
          }}
        >
          <span style={{ font: `600 12px ${fonts.mono}`, color: colors.amber }}>⚠</span>
          <span style={{ font: `500 12px ${fonts.sans}`, color: colors.ink }}>
            {vm.exchange} delisting risk due to{' '}
            {vm.delistingRisk.map((d) => d.title.toLowerCase()).join(' and ')}
          </span>
        </div>
      ) : null}

      {/* actions */}
      <div className="no-print token-report-actions" style={{ display: 'flex', gap: 10, marginTop: 'auto' }}>
        <button
          type="button"
          onClick={() => exportTokenReportPdf(vm)}
          style={{
            flex: 1,
            textAlign: 'center',
            font: `600 12px ${fonts.mono}`,
            color: colors.accentInk,
            background: colors.accent,
            borderRadius: 7,
            padding: 12,
            border: 'none',
            cursor: 'pointer',
          }}
        >
          EXPORT PDF
        </button>
        <button
          type="button"
          onClick={handleShareLink}
          style={{
            flex: 1,
            textAlign: 'center',
            font: `600 12px ${fonts.mono}`,
            color: colors.ink2,
            border: `1px solid ${shareFailed ? colors.red : colors.line2}`,
            borderRadius: 7,
            padding: 12,
            cursor: 'pointer',
            background: 'transparent',
          }}
        >
          {shareCopied ? 'COPIED' : shareFailed ? 'COPY FAILED' : 'SHARE LINK'}
        </button>
      </div>
      {shareFailed ? (
        <p
          className="no-print"
          role="status"
          aria-live="polite"
          style={{
            margin: '-18px 0 0',
            font: `400 11px ${fonts.sans}`,
            color: colors.red,
            textAlign: 'center',
          }}
        >
          Clipboard unavailable. Copy the URL from the address bar.
        </p>
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Right detail (scrolling) — each block conditional on its data
// ---------------------------------------------------------------------------
function Detail({ vm }: { vm: TokenViewModel }) {
  return (
    <div
      className="token-report-detail"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 44,
      }}
    >
      {vm.healthDashboard.length > 0 ? <HealthDashboard vm={vm} /> : null}
      {vm.peers.length > 0 ? <PeerChart vm={vm} /> : null}
      {vm.investorSimulator.length > 0 ? <InvestorSimulator vm={vm} /> : null}
      {vm.lostOpportunity ? <LostOpportunity vm={vm} /> : null}
      {vm.rootCauses.length > 0 ? <RootCauses vm={vm} /> : null}
      {shouldShowImprovements(vm) ? <Improvements vm={vm} /> : null}
      {vm.roadmap.length > 0 ? <Roadmap vm={vm} /> : null}
      {vm.implementationOptions.length > 0 ? <ImplementationOptions vm={vm} /> : null}
      <ExploreFurther />
    </div>
  );
}

function HealthDashboard({ vm }: { vm: TokenViewModel }) {
  return (
    <div>
      <SectionHeading title="Health dashboard" sub={`vs ${vm.exchange} average`} />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {vm.healthDashboard.map((m) => {
          const c = severityColor(m.severity);
          return (
            <div
              key={m.title}
              className="token-report-panel health-metric-row"
              style={{
                border: `1px solid ${colors.line}`,
                borderLeft: `3px solid ${c}`,
                borderRadius: 7,
                background: colors.panel,
                padding: '16px 18px',
              }}
            >
              <span className="health-metric-title" style={{ font: `600 13px ${fonts.sans}`, color: colors.ink }}>
                {m.title}
              </span>
              <span style={{ font: `400 12px ${fonts.sans}`, color: colors.ink2 }}>
                {m.impact} ·{' '}
                <span style={{ fontFamily: fonts.mono, color: colors.ink3 }}>{m.evidence}</span>
              </span>
              <span
                style={{
                  font: `600 9px ${fonts.mono}`,
                  letterSpacing: '.1em',
                  color: c,
                }}
              >
                {m.severity.toUpperCase()}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function isPeerLink(peer: PeerRow): boolean {
  return !peer.isYours && peer.name !== 'Median';
}

function PeerNameLabel({
  peer,
  vm,
  labelColor,
}: {
  peer: PeerRow;
  vm: TokenViewModel;
  labelColor: (peerRow: PeerRow) => string;
}) {
  const [hovered, setHovered] = useState(false);
  const labelStyle: React.CSSProperties = {
    font: `${peer.isYours || peer.name === 'Median' ? 600 : 500} 12px ${fonts.mono}`,
    color: hovered ? colors.accent : labelColor(peer),
  };
  const text = peer.isYours ? vm.pair : peer.name;

  if (!isPeerLink(peer)) {
    return <span style={labelStyle}>{text}</span>;
  }

  return (
    <Link
      to={`/pairs/${vm.exchangeSlug}/${pairToSlug(peer.name)}`}
      style={{
        ...labelStyle,
        textDecoration: 'none',
        cursor: 'pointer',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {text}
    </Link>
  );
}

function PeerChart({ vm }: { vm: TokenViewModel }) {
  const maxDepth = Math.max(...vm.peers.map((p) => p.depth));
  const medianPeer = vm.peers.find((p) => p.name === 'Median');

  const yoursDepthComparison =
    medianPeer != null
      ? peerMetricComparison(
          vm.peers.find((p) => p.isYours)?.depth ?? 0,
          medianPeer.depth,
          'depth',
        )
      : 'neutral';

  const barColor = (p: PeerRow): string => {
    if (p.isYours) {
      return comparisonColor(yoursDepthComparison);
    }
    if (p.name === 'Median') {
      return colors.accent;
    }
    return '#2f3a45';
  };

  const labelColor = (p: PeerRow): string => {
    if (p.isYours) {
      return comparisonTextColor(yoursDepthComparison);
    }
    if (p.name === 'Median') {
      return colors.accent;
    }
    return colors.ink2;
  };

  const valueColor = (p: PeerRow): string => {
    if (p.isYours) {
      return comparisonTextColor(yoursDepthComparison);
    }
    return colors.ink2;
  };

  return (
    <div>
      <SectionHeading title="Peer comparison" sub="· depth ±2%" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {vm.peers.map((p) => (
          <div
            key={p.name}
            className="peer-bar-row"
          >
            <PeerNameLabel peer={p} vm={vm} labelColor={labelColor} />
            <div className="token-report-peer-track" style={{ height: 18, background: '#141a22', borderRadius: 3, overflow: 'hidden' }}>
              <div
                style={{
                  width: `${Math.max(2, (p.depth / maxDepth) * 100)}%`,
                  height: '100%',
                  background: barColor(p),
                  opacity: p.name === 'Median' ? 0.55 : 1,
                }}
              />
            </div>
            <span
              style={{
                font: `${p.isYours || p.name === 'Median' ? 600 : 500} 12px ${fonts.mono}`,
                color: p.name === 'Median' ? colors.ink2 : valueColor(p),
                textAlign: 'right',
              }}
            >
              {fmtUsdShort(p.depth)}
            </span>
          </div>
        ))}
      </div>
      <div style={{ font: `400 11px ${fonts.sans}`, color: colors.ink3, marginTop: 16 }}>
        Peers on {vm.exchange}: similar volume tier and quote currency.{' '}
        <Link
          to="/methodology"
          style={{
            font: `500 11px ${fonts.sans}`,
            color: colors.accent,
            textDecoration: 'none',
          }}
        >
          Methodology
        </Link>
      </div>
    </div>
  );
}

function InvestorSimulator({ vm }: { vm: TokenViewModel }) {
  return (
    <div className="token-report-investor-page">
      <SectionHeading title="Investor simulator" />
      <p
        style={{
          margin: '0 0 20px',
          font: `400 14px/1.6 ${fonts.sans}`,
          color: colors.ink2,
          maxWidth: 640,
        }}
      >
        {investorSimulatorIntro(vm)}
      </p>
      <div className="investor-sim-grid">
        {vm.investorSimulator.map((s) => {
          const isHighlight = s.highlight;
          const severity = s.omitted ? null : overpaySeverity(s.overpayPct);
          const severityBorderColor =
            severity != null ? overpaySeverityBorderColor(severity) : colors.ink3;

          return (
            <div
              key={s.size}
              className="token-report-panel"
              style={{
                position: 'relative',
                border: `1px solid ${isHighlight ? colors.accent : colors.line}`,
                borderLeft: `3px solid ${severityBorderColor}`,
                borderRadius: 8,
                background: isHighlight ? 'rgba(54,214,195,.06)' : colors.panel,
                padding: 20,
              }}
            >
              {isHighlight ? (
                <div
                  style={{
                    position: 'absolute',
                    top: -8,
                    right: 12,
                    font: `600 9px ${fonts.mono}`,
                    letterSpacing: '.1em',
                    color: colors.accentInk,
                    background: colors.accent,
                    borderRadius: 4,
                    padding: '2px 7px',
                  }}
                >
                  PRIMARY
                </div>
              ) : null}
              <div
                style={{
                  font: `600 14px ${fonts.mono}`,
                  color: s.omitted ? colors.ink3 : colors.ink,
                }}
              >
                {fmtUsdShort(s.size).replace('.0', '')} buy
              </div>
              {s.omitted ? (
                <>
                  <div style={{ font: `600 15px ${fonts.mono}`, color: colors.amber, margin: '8px 0 4px' }}>
                    Cannot simulate
                  </div>
                  <div style={{ font: `400 12px ${fonts.sans}`, color: colors.ink2 }}>
                    Only {Math.round((s.fillRatio ?? 0) * 100)}% fillable on visible book
                  </div>
                </>
              ) : (
                <>
                  <div
                    style={{
                      font: `700 22px ${fonts.mono}`,
                      color: overpaySeverityColor(severity ?? 'poor'),
                      margin: '8px 0 2px',
                    }}
                  >
                    {fmtSignedUsd(s.overpayUsd ?? 0)}
                  </div>
                  <div style={{ font: `400 12px ${fonts.sans}`, color: colors.ink2 }}>
                    {s.overpayPct}% overpay vs liquid peer
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function LostOpportunity({ vm }: { vm: TokenViewModel }) {
  const copy = lostOpportunityText(vm);

  return (
    <div
      className="token-report-panel"
      style={{
        border: `1px solid ${colors.line}`,
        borderRadius: 8,
        background: colors.panel,
        padding: '26px 28px',
      }}
    >
      {copy.noteOnly != null ? (
        <p style={{ margin: 0, font: `400 14px/1.6 ${fonts.sans}`, color: colors.ink2 }}>{copy.noteOnly}</p>
      ) : copy.isPositive ? (
        <p style={{ margin: 0, font: `400 14px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
          <span style={{ color: colors.ink, fontWeight: 600 }}>{copy.lead}</span>{' '}
          <span style={{ color: colors.green }}>{copy.body}</span>
        </p>
      ) : (
        <p style={{ margin: 0, font: `400 14px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
          <span style={{ color: colors.ink, fontWeight: 600 }}>{copy.lead}</span>{' '}
          {copy.body}{' '}
          <span style={{ fontFamily: fonts.mono, color: colors.amber }}>{copy.range}</span> to slippage
          and spread. A common reason allocators pass.
        </p>
      )}
    </div>
  );
}

function RootCauses({ vm }: { vm: TokenViewModel }) {
  return (
    <div>
      <SectionHeading title="Root cause" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {vm.rootCauses.map((rc) => (
          <div
            key={rc.rank}
            className="token-report-panel"
            style={{
              display: 'flex',
              gap: 20,
              border: `1px solid ${colors.line}`,
              borderRadius: 8,
              background: colors.panel,
              padding: '20px 22px',
            }}
          >
            <span style={{ font: `700 20px ${fonts.mono}`, color: colors.accent, lineHeight: 1 }}>
              #{rc.rank}
            </span>
            <div>
              <div style={{ font: `600 14px ${fonts.sans}`, color: colors.ink, marginBottom: 4 }}>
                {rc.title}
              </div>
              <div style={{ font: `400 13px/1.5 ${fonts.sans}`, color: colors.ink2 }}>
                {rc.evidence}. <span style={{ color: colors.ink3 }}>Impact: {rc.impact}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Improvements({ vm }: { vm: TokenViewModel }) {
  return (
    <div>
      <SectionHeading title="Improvement potential" />
      <div className="token-report-table improvements-scroll" style={{ border: `1px solid ${colors.line}`, borderRadius: 8 }}>
        <div className="improvements-table">
        <div
          className="token-report-table-head improvements-grid-head"
          style={{
            background: colors.tableHead,
            borderBottom: `1px solid ${colors.line}`,
            font: `500 10px ${fonts.mono}`,
            letterSpacing: '.08em',
            color: colors.ink3,
          }}
        >
          <span style={{ padding: '10px 16px' }}>METRIC</span>
          <span style={{ padding: '10px 16px', textAlign: 'right' }}>CURRENT</span>
          <span style={{ padding: '10px 16px', textAlign: 'right' }}>POTENTIAL (PEER MEDIAN)</span>
        </div>
        {vm.improvements.map((im, i) => (
          <div
            key={im.metric}
            className="improvements-grid-row"
            style={{
              borderBottom: i < vm.improvements.length - 1 ? `1px solid ${colors.line}` : 'none',
              font: `500 13px ${fonts.mono}`,
            }}
          >
            <span style={{ padding: '11px 16px', color: colors.ink }}>{im.metric}</span>
            <span style={{ padding: '11px 16px', textAlign: 'right', color: colors.red }}>
              {im.current}
            </span>
            <span style={{ padding: '11px 16px', textAlign: 'right', color: colors.green }}>
              {im.potential}
            </span>
          </div>
        ))}
        </div>
      </div>
    </div>
  );
}

function Roadmap({ vm }: { vm: TokenViewModel }) {
  return (
    <div>
      <SectionHeading title="Improvement roadmap" />
      <div className="token-report-table roadmap-scroll" style={{ border: `1px solid ${colors.line}`, borderRadius: 8 }}>
        <div className="roadmap-table">
        <div
          className="token-report-table-head roadmap-grid-head"
          style={{
            background: colors.tableHead,
            borderBottom: `1px solid ${colors.line}`,
            font: `500 10px ${fonts.mono}`,
            letterSpacing: '.08em',
            color: colors.ink3,
          }}
        >
          <span style={{ padding: '10px 16px' }}>ISSUE</span>
          <span style={{ padding: '10px 16px' }}>FIX</span>
          <span style={{ padding: '10px 16px' }}>EST. COST</span>
          <span style={{ padding: '10px 16px', textAlign: 'right' }}>EXPECTED IMPACT</span>
        </div>
        {vm.roadmap.map((r, i) => (
          <div
            key={r.issue}
            className="roadmap-grid-row"
            style={{
              borderBottom: i < vm.roadmap.length - 1 ? `1px solid ${colors.line}` : 'none',
              font: `500 12px ${fonts.sans}`,
              color: colors.ink2,
            }}
          >
            <span style={{ padding: '11px 16px', color: colors.ink }}>{r.issue}</span>
            <span style={{ padding: '11px 16px' }}>{r.fix}</span>
            <span style={{ padding: '11px 16px', fontFamily: fonts.mono }}>{r.cost}</span>
            <span
              style={{
                padding: '11px 16px',
                textAlign: 'right',
                fontFamily: fonts.mono,
                color: colors.green,
              }}
            >
              {r.impact}
            </span>
          </div>
        ))}
        </div>
      </div>
    </div>
  );
}

function ImplementationOptions({ vm }: { vm: TokenViewModel }) {
  return (
    <div>
      <SectionHeading title="Implementation options" />
      <div className="impl-options-grid">
        {vm.implementationOptions.map((o) => (
          <a
            key={o.id}
            className="token-report-panel"
            href={o.url}
            target="_blank"
            rel="noopener"
            style={{
              textDecoration: 'none',
              border: `1px solid ${colors.line}`,
              borderRadius: 8,
              background: colors.panel,
              padding: 20,
            }}
          >
            <div style={{ font: `600 13px ${fonts.mono}`, color: colors.accent, marginBottom: 10 }}>
              {o.id}: {o.title}
            </div>
            <div style={{ font: `400 12px/1.5 ${fonts.sans}`, color: colors.ink2 }}>
              <span style={{ color: colors.green }}>Pros:</span> {o.pros}
            </div>
            <div
              style={{ font: `400 12px/1.5 ${fonts.sans}`, color: colors.ink2, marginBottom: 10 }}
            >
              <span style={{ color: colors.red }}>Cons:</span> {o.cons}
            </div>
            <div style={{ font: `500 11px ${fonts.mono}`, color: colors.accent }}>Learn more →</div>
          </a>
        ))}
      </div>
    </div>
  );
}

function ExploreFurther() {
  const links = [
    { label: 'Case studies', to: '/case-studies' },
    { label: 'Learn', to: '/learn' },
    { label: 'Methodology', to: '/methodology' },
  ];
  return (
    <div
      className="no-print explore-further"
      style={{
        display: 'flex',
        gap: 10,
        borderTop: `1px solid ${colors.line}`,
        paddingTop: 28,
        marginTop: 4,
      }}
    >
      <span style={{ font: `500 12px ${fonts.sans}`, color: colors.ink3 }}>Explore further:</span>
      {links.map((link, index) => (
        <React.Fragment key={link.to}>
          <Link
            to={link.to}
            style={{
              font: `500 12px ${fonts.sans}`,
              color: colors.accent,
              textDecoration: 'none',
            }}
          >
            {link.label}
          </Link>
          {index < links.length - 1 ? <span style={{ color: colors.ink3 }}>·</span> : null}
        </React.Fragment>
      ))}
    </div>
  );
}
