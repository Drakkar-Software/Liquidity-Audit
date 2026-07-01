import { colors, fonts } from '../theme';
import { Screen } from '../components/Screen';
import { Eyebrow } from '../components/SectionHeading';
import { GuidesSection } from '../components/GuidesSection';
import { SiteTextLink } from '../components/SiteTextLink';

const GLOSSARY: { term: string; def: string }[] = [
  {
    term: 'Spread',
    def: 'The gap between the best bid and best ask, expressed as a percentage of mid price. A tighter spread means lower immediate trading cost.',
  },
  {
    term: 'Depth ±2%',
    def: 'Total quote liquidity (USDT) resting within 2% of mid on both sides of the book. More depth usually means less price impact on medium-sized orders.',
  },
  {
    term: 'Slippage',
    def: 'Extra cost vs mid price when executing a market buy against the visible ask book. Reports simulate several trade sizes and highlight the largest fillable size among $10k, $1k, and $100.',
  },
  {
    term: 'Liquidity score and grade',
    def: 'A 0–100 score: half from order-book shape (level count, depth at ±2% and ±10% vs 24h volume, spread) and half from spread, depth, and slippage vs the median of up to 3 same-volume-tier peers. Mapped to letter grades A–F and a status of Good, Fair, or Poor.',
  },
  {
    term: 'Volume consistency',
    def: 'Compares 24h reported volume to visible tight depth. A very high ratio can signal hollow volume: activity that does not match resting liquidity.',
  },
  {
    term: 'Peer median',
    def: 'The median spread, depth, and slippage of up to three peer tokens on the same exchange with similar 24h volume. Used as the benchmark in improvement potential.',
  },
  {
    term: 'Investor simulator',
    def: 'Shows the dollar and percentage cost of market buys at the largest available trade sizes: what a larger buyer would pay above fair price on the current book.',
  },
  {
    term: 'Lost opportunity',
    def: 'Estimated execution cost at the primary display trade size (same adaptive size as slippage in the summary), plus the range of slippage across fillable sizes.',
  },
];

const PITFALLS: { title: string; body: string }[] = [
  {
    title: 'Hollow volume',
    body: 'Healthy 24h volume but only a few hundred dollars of visible depth. The vol/depth ratio flags this on the health dashboard.',
  },
  {
    title: 'Thin asks, tight spread',
    body: 'Best bid/ask spread can look fine while a $1k+ market buy still pays double-digit slippage because ask liquidity is stacked far from mid.',
  },
  {
    title: 'One-sided flow',
    body: 'Extreme buy or sell skew in 24h volume (e.g. 99% buys) often pairs with an imbalanced book and worse effective prices for entrants.',
  },
  {
    title: 'Unfillable size',
    body: 'A $10k buy may not fill from visible asks; the simulator shows “Cannot simulate” and slippage at that size is omitted from headline metrics.',
  },
];

export function Learn() {
  return (
    <Screen active="Learn">
      <div className="page-section-narrow">
        <h1 style={{ margin: '0 0 8px', font: `600 30px ${fonts.sans}`, color: colors.ink }}>
          Learn
        </h1>
        <p style={{ margin: '0 0 28px', font: `400 15px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
          Terms used on token liquidity reports. See{' '}
          <SiteTextLink to="/methodology">methodology</SiteTextLink> for how metrics are computed.
        </p>

        <Eyebrow>GLOSSARY</Eyebrow>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            border: `1px solid ${colors.line}`,
            borderRadius: 8,
            overflow: 'hidden',
          }}
        >
          {GLOSSARY.map((glossaryEntry, entryIndex) => (
            <div
              key={glossaryEntry.term}
              className="learn-term-row"
              style={{
                padding: '18px 20px',
                background: colors.panel,
                borderBottom:
                  entryIndex < GLOSSARY.length - 1 ? `1px solid ${colors.line}` : 'none',
              }}
            >
              <div style={{ font: `600 15px ${fonts.mono}`, color: colors.accent }}>
                {glossaryEntry.term}
              </div>
              <div style={{ font: `400 14px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
                {glossaryEntry.def}
              </div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 32 }}>
          <Eyebrow>COMMON PITFALLS</Eyebrow>
          <ul
            style={{
              margin: 0,
              paddingLeft: 18,
              font: `400 14px/1.7 ${fonts.sans}`,
              color: colors.ink2,
            }}
          >
            {PITFALLS.map((pitfall) => (
              <li key={pitfall.title} style={{ marginBottom: 8 }}>
                <strong style={{ color: colors.ink }}>{pitfall.title}:</strong> {pitfall.body}
              </li>
            ))}
          </ul>
        </div>

        <div style={{ marginTop: 32 }}>
          <GuidesSection />
        </div>
      </div>
    </Screen>
  );
}
