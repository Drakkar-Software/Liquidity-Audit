import { colors, fonts } from '../theme';
import { Screen } from '../components/Screen';

interface MetricDelta {
  label: string;
  from: string;
  to: string;
}

interface CaseStudy {
  name: string;
  heading: string;
  scoreFrom: number;
  scoreTo: number;
  metrics: MetricDelta[];
  quote: string;
}

const CASES: CaseStudy[] = [
  {
    name: 'Project A · 90 days',
    heading: '90-day crypto liquidity recovery',
    scoreFrom: 38,
    scoreTo: 81,
    metrics: [
      { label: 'SPREAD', from: '3.1%', to: '0.4%' },
      { label: 'DEPTH', from: '$8k', to: '$110k' },
      { label: 'SLIP$10K', from: '9.4%', to: '0.9%' },
    ],
    quote:
      '"The report gave us a number our exchange contact actually respected. We knew exactly which gaps to close first."',
  },
  {
    name: 'Project B · 60 days',
    heading: '60-day spread and depth improvement',
    scoreFrom: 45,
    scoreTo: 74,
    metrics: [
      { label: 'SPREAD', from: '1.9%', to: '0.5%' },
      { label: 'DEPTH', from: '$14k', to: '$95k' },
      { label: 'SLIP$10K', from: '5.2%', to: '1.1%' },
    ],
    quote:
      '"Continuous quoting fixed the quote-gap flag within weeks. The peer comparison made the target obvious."',
  },
];

export function CaseStudies() {
  return (
    <Screen active="Case Studies">
      <div className="page-section">
        <h1 style={{ margin: '0 0 8px', font: `600 30px ${fonts.sans}`, color: colors.ink }}>
          Crypto liquidity case studies
        </h1>
        <p
          style={{
            margin: '0 0 28px',
            font: `400 15px/1.6 ${fonts.sans}`,
            color: colors.ink2,
          }}
        >
          How pairs moved after addressing the issues a report surfaced. Anonymized examples of what
          teams often see after acting on a report.
        </p>

        <div className="grid-two" style={{ gap: 16 }}>
          {CASES.map((c) => (
            <div
              key={c.name}
              style={{
                border: `1px solid ${colors.line}`,
                borderRadius: 10,
                background: colors.panel,
                padding: 22,
              }}
            >
              <h2
                style={{
                  margin: '0 0 18px',
                  font: `600 16px ${fonts.sans}`,
                  color: colors.ink,
                }}
              >
                {c.heading}
              </h2>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 18,
                }}
              >
                <span style={{ font: `600 14px ${fonts.mono}`, color: colors.ink2 }}>{c.name}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ font: `700 22px ${fonts.mono}`, color: colors.red }}>
                    {c.scoreFrom}
                  </span>
                  <span style={{ color: colors.ink3 }}>→</span>
                  <span style={{ font: `700 22px ${fonts.mono}`, color: colors.green }}>
                    {c.scoreTo}
                  </span>
                </div>
              </div>

              <div className="grid-three" style={{ marginBottom: 18 }}>
                {c.metrics.map((m) => (
                  <div
                    key={m.label}
                    style={{ border: `1px solid ${colors.line}`, borderRadius: 6, padding: '11px 12px' }}
                  >
                    <div style={{ font: `500 10px ${fonts.mono}`, color: colors.ink3 }}>{m.label}</div>
                    <div style={{ font: `600 13px ${fonts.mono}`, color: colors.ink }}>
                      <span style={{ color: colors.red }}>{m.from}</span>
                      {' → '}
                      <span style={{ color: colors.green }}>{m.to}</span>
                    </div>
                  </div>
                ))}
              </div>

              <p
                style={{
                  margin: 0,
                  font: `400 14px/1.6 ${fonts.sans}`,
                  color: colors.ink2,
                  fontStyle: 'italic',
                }}
              >
                {c.quote}
              </p>
            </div>
          ))}
        </div>
      </div>
    </Screen>
  );
}
