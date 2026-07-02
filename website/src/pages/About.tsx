import type { ReactNode } from 'react';
import { colors, fonts } from '../theme';
import { Screen } from '../components/Screen';
import { SiteTextLink } from '../components/SiteTextLink';
import { LIQUIDITY_AUDIT_GITHUB_URL } from '../lib/pillarGuides';

const PRINCIPLES: { title: string; body: ReactNode }[] = [
  {
    title: 'Transparency',
    body: (
      <>
        Published methodology, a visible snapshot timestamp on every report, and the{' '}
        <SiteTextLink external href={LIQUIDITY_AUDIT_GITHUB_URL}>
          open-source audit pipeline
        </SiteTextLink>{' '}
        that produces the analysis JSON shown on this site.
      </>
    ),
  },
  {
    title: 'Exchange-native benchmarks',
    body: 'Medians and peers on the same venue, matched by volume tier and quote currency.',
  },
  {
    title: 'Evidence before advice',
    body: 'Improvement sections appear only when the data supports a clear gap.',
  },
];

export function About() {
  return (
    <Screen active="About">
      <div className="page-section-narrow">
        <h1 style={{ margin: '0 0 10px', font: `600 30px ${fonts.sans}`, color: colors.ink }}>
          Independent crypto liquidity analysis
        </h1>
        <p
          style={{
            margin: '0 0 30px',
            font: `400 16px/1.6 ${fonts.sans}`,
            color: colors.ink2,
          }}
        >
          Crypto Liquidity Audit reads one order-book snapshot and turns it into a report with the numbers
          behind each grade. We don&apos;t sell listings or make markets in what we measure, so the
          analysis stays independent.
        </p>

        <section style={{ marginBottom: 30 }}>
          <h2
            style={{
              margin: '0 0 14px',
              font: `600 20px ${fonts.sans}`,
              color: colors.ink,
            }}
          >
            How we score crypto spot pairs
          </h2>
          <div className="grid-three" style={{ gap: 12 }}>
          {PRINCIPLES.map((p) => (
            <div
              key={p.title}
              style={{
                border: `1px solid ${colors.line}`,
                borderRadius: 8,
                background: colors.panel,
                padding: 18,
              }}
            >
              <div style={{ font: `600 14px ${fonts.sans}`, color: colors.ink, marginBottom: 6 }}>
                {p.title}
              </div>
              <div style={{ font: `400 13px/1.5 ${fonts.sans}`, color: colors.ink2 }}>{p.body}</div>
            </div>
          ))}
          </div>
        </section>

        <section
          style={{
            border: `1px solid ${colors.line}`,
            borderRadius: 8,
            background: colors.panel,
            padding: 22,
            marginBottom: 30,
          }}
        >
          <h2
            style={{
              margin: '0 0 10px',
              font: `600 20px ${fonts.sans}`,
              color: colors.ink,
            }}
          >
            Supported crypto exchanges
          </h2>
          <p style={{ margin: 0, font: `400 14px/1.7 ${fonts.sans}`, color: colors.ink2 }}>
            Rankings and reports currently cover MEXC and BitMart, the exchanges most requested so
            far. Want another venue added?{' '}
            <a
              href="mailto:contact@octobot.cloud"
              style={{ color: colors.accent, textDecoration: 'none' }}
            >
              Contact us
            </a>{' '}
            and tell us which exchange you need.
          </p>
        </section>

        <div className="grid-about-wide">
          <section
            style={{
              border: `1px solid ${colors.line}`,
              borderRadius: 8,
              background: colors.panel,
              padding: 22,
            }}
          >
            <h2
              style={{
                margin: '0 0 10px',
                font: `600 20px ${fonts.sans}`,
                color: colors.ink,
              }}
            >
              Who builds Crypto Liquidity Audit
            </h2>
            <p style={{ margin: 0, font: `400 14px/1.7 ${fonts.sans}`, color: colors.ink2 }}>
              Built by practitioners at{' '}
              <a
                href="https://github.com/Drakkar-Software"
                target="_blank"
                rel="noopener"
                style={{ color: colors.accent, textDecoration: 'none' }}
              >
                Drakkar Software
              </a>
              , the team behind{' '}
              <a
                href="https://market-making.octobot.cloud/"
                target="_blank"
                rel="noopener"
                style={{ color: colors.accent, textDecoration: 'none' }}
              >
                OctoBot Market Making
              </a>{' '}
              infrastructure. Reports remain independent analysis; any implementation options on
              low-scoring reports are clearly separated from the report itself.
            </p>
          </section>
          <div
            style={{
              border: `1px solid ${colors.accent}`,
              borderRadius: 8,
              background: 'rgba(54,214,195,.05)',
              padding: 22,
            }}
          >
            <div style={{ font: `600 16px ${fonts.sans}`, color: colors.ink, marginBottom: 8 }}>
              Get in touch
            </div>
            <p style={{ margin: '0 0 14px', font: `400 13px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
              Questions about a report or your pair&apos;s liquidity?
            </p>
            <a
              href="mailto:contact@octobot.cloud"
              style={{
                display: 'block',
                font: `600 12px ${fonts.mono}`,
                color: colors.accentInk,
                background: colors.accent,
                borderRadius: 6,
                padding: '11px 0',
                textAlign: 'center',
                textDecoration: 'none',
              }}
            >
              Contact the team →
            </a>
          </div>
        </div>
      </div>
    </Screen>
  );
}
