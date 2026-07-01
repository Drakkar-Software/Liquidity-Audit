import { SiteTextLink } from '../components/SiteTextLink';
import { colors, fonts } from '../theme';
import { Screen } from '../components/Screen';
import { Eyebrow } from '../components/SectionHeading';
import {
  MethodologyBookSchematicIllustration,
  MethodologyGradeStripIllustration,
  MethodologyStepFlowIllustration,
} from '../components/guideIllustrations';

const FORMULAS: { metric: string; def: string }[] = [
  { metric: 'Spread %', def: '(best ask − best bid) / mid price × 100' },
  {
    metric: 'Depth ±2%',
    def: 'Sum of bid + ask quote liquidity within 2% of mid; labeled "visible book only" when the band is not fully spanned',
  },
  {
    metric: 'Slippage',
    def: 'Simulated market buy walking the ask book at $100, $1k, $5k, $10k, $25k; omitted if < 95% fillable',
  },
  { metric: 'Display slippage', def: 'First fillable size in order $10k → $1k → $100' },
  {
    metric: 'Volume consistency',
    def: '24h quote volume / tight depth; flagged when ratio > 10× unless spread/depth/slippage already healthy',
  },
];

const LIMITATIONS = [
  'Independent analysis. Not investment advice.',
  'Visible CEX spot book only; single snapshot per run',
  'No wash-trading or volume-quality detection',
  'Thin ask liquidity can make large buys unfillable even when bid depth looks healthy',
];

export function Methodology() {
  return (
    <Screen active="Methodology">
      <div className="page-section-narrow">
        <h1 style={{ margin: '0 0 8px', font: `600 30px ${fonts.sans}`, color: colors.ink }}>
          Methodology
        </h1>
        <p style={{ margin: '0 0 28px', font: `400 15px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
          Every report is built from a single point-in-time snapshot of the visible spot order book.
          We publish exactly how each number is produced.
        </p>

        <section className="guide-section-with-visual" style={{ marginBottom: 28 }}>
          <div>
            <h2 style={{ margin: '0 0 12px', font: `600 20px ${fonts.sans}`, color: colors.ink }}>
              How to check token liquidity
            </h2>
            <ol
              style={{
                margin: '0 0 12px',
                paddingLeft: 22,
                font: `400 15px/1.7 ${fonts.sans}`,
                color: colors.ink2,
              }}
            >
              <li>Pick an exchange on the home page.</li>
              <li>Search the pair symbol (for example TOKEN/USDT).</li>
              <li>
                Open the report to see spread, depth, slippage, and the{' '}
                <SiteTextLink to="/liquidity-score">liquidity score</SiteTextLink>.
              </li>
            </ol>
            <p style={{ margin: 0, font: `400 14px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
              <SiteTextLink to="/">Try the rankings tool</SiteTextLink> to compare pairs on the same exchange.
            </p>
          </div>
          <div className="guide-section-visual">
            <MethodologyStepFlowIllustration />
          </div>
        </section>

        <section className="guide-section-with-visual" style={{ marginBottom: 28 }}>
          <div>
            <h2 style={{ margin: '0 0 12px', font: `600 20px ${fonts.sans}`, color: colors.ink }}>
              Liquidity score
            </h2>
            <p style={{ margin: 0, font: `400 15px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
              The liquidity score is a 0–100 number with an A–F grade from one visible snapshot. Half
              comes from book shape; half from peer comparison when enough similar pairs exist on the
              same exchange. See SCORE &amp; GRADES below and the{' '}
              <SiteTextLink to="/liquidity-score">liquidity score</SiteTextLink> guide for a short overview.
            </p>
          </div>
          <div className="guide-section-visual">
            <MethodologyGradeStripIllustration />
          </div>
        </section>

        <section className="guide-section-with-visual" style={{ marginBottom: 28 }}>
          <div>
            <h2 style={{ margin: '0 0 12px', font: `600 20px ${fonts.sans}`, color: colors.ink }}>
              Order book liquidity analysis
            </h2>
            <p style={{ margin: 0, font: `400 15px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
              Order book liquidity analysis here means spread, depth within price bands, and simulated
              slippage for standard buy sizes on the visible CEX spot book. It is one snapshot, not
              hidden liquidity or DEX flow. See <SiteTextLink to="/order-book-analysis">order book analysis</SiteTextLink>{' '}
              for definitions of depth and the visible book limit.
            </p>
          </div>
          <div className="guide-section-visual">
            <MethodologyBookSchematicIllustration />
          </div>
        </section>

        <Eyebrow>METRIC FORMULAS</Eyebrow>
        <div
          style={{
            border: `1px solid ${colors.line}`,
            borderRadius: 8,
            overflow: 'hidden',
            marginBottom: 28,
          }}
        >
          <div
            className="methodology-formula-header"
            style={{
              background: colors.tableHead,
              borderBottom: `1px solid ${colors.line}`,
              font: `500 10px ${fonts.mono}`,
              letterSpacing: '.08em',
              color: colors.ink3,
            }}
          >
            <span style={{ padding: '10px 16px' }}>METRIC</span>
            <span style={{ padding: '10px 16px' }}>DEFINITION</span>
          </div>
          {FORMULAS.map((f, i) => (
            <div
              key={f.metric}
              className="methodology-formula-row"
              style={{
                borderBottom: i < FORMULAS.length - 1 ? `1px solid ${colors.line}` : 'none',
              }}
            >
              <span style={{ padding: '12px 16px', font: `600 13px ${fonts.sans}`, color: colors.ink }}>
                {f.metric}
              </span>
              <span style={{ padding: '12px 16px', font: `400 13px/1.5 ${fonts.sans}`, color: colors.ink2 }}>
                {f.def}
              </span>
            </div>
          ))}
        </div>

        <div className="grid-two" style={{ gap: 24, marginBottom: 28 }}>
          <div>
            <Eyebrow>SCORE &amp; GRADES</Eyebrow>
            <p style={{ margin: '0 0 12px', font: `400 13px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
              0–100 blends two halves: internal book shape (average of four 0–1 sub-scores —
              order-book level coverage, tight depth ±1%, wider depth ±10% (weaker bid/ask side),
              and spread tightness) and peer-relative performance (spread, depth ±2%, slippage vs
              the median of up to 3 same-volume-tier peers, with a 95% deadband). When no peers
              qualify, only the internal half is used. The headline score floors at 100 when the
              pair is healthy, all issue chips pass, and every health-dashboard row is Low severity.
            </p>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 5,
                font: `500 12px ${fonts.mono}`,
                color: colors.ink2,
              }}
            >
              <span>
                <span style={{ color: colors.green }}>A ≥ 85</span> ·{' '}
                <span style={{ color: colors.green }}>B ≥ 70</span> ·{' '}
                <span style={{ color: colors.amber }}>C ≥ 55</span> ·{' '}
                <span style={{ color: colors.red }}>D ≥ 40</span> ·{' '}
                <span style={{ color: colors.red }}>F &lt; 40</span>
              </span>
              <span style={{ color: colors.ink3, fontFamily: fonts.sans }}>
                Status: Poor (low health or &lt;40) · Good (≥70 and healthy) · Fair (else)
              </span>
            </div>
          </div>
          <div>
            <Eyebrow>BENCHMARKS &amp; PEERS</Eyebrow>
            <p style={{ margin: '0 0 8px', font: `400 13px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
              <span style={{ color: colors.ink }}>Exchange average:</span> median spread, depth ±2%
              and slippage across same-exchange pairs with ≥ $1k 24h volume. Used for the health
              dashboard only.
            </p>
            <p style={{ margin: 0, font: `400 13px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
              <span style={{ color: colors.ink }}>Peers:</span> up to 3 symbols, same exchange and
              quote currency, 24h volume within 5× of target, ranked by liquidity score.
            </p>
          </div>
        </div>

        <div className="grid-two" style={{ gap: 24 }}>
          <div>
            <Eyebrow>SNAPSHOT POLICY</Eyebrow>
            <p style={{ margin: 0, font: `400 13px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
              One point-in-time visible order book per run (top 50 bid/ask levels) plus 24h ticker.
              Reports show <span style={{ fontFamily: fonts.mono, color: colors.ink }}>fetched … ago</span>;
              pairs re-analyzed on every daily run. Depth bands: ±2% (reports) and ±10% (scoring).
            </p>
          </div>
          <div>
            <Eyebrow>LIMITATIONS</Eyebrow>
            <ul
              style={{
                margin: 0,
                paddingLeft: 18,
                font: `400 13px/1.7 ${fonts.sans}`,
                color: colors.ink2,
              }}
            >
              {LIMITATIONS.map((l) => (
                <li key={l}>{l}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </Screen>
  );
}
