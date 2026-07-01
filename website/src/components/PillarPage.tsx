import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { colors, fonts } from '../theme';
import { Screen } from './Screen';
import { relatedPillarLinks } from '../lib/pillarGuides';
import { GuideCardGrid } from './GuideCard';

export interface PillarSection {
  heading: string;
  paragraphs: ReactNode[];
}

export interface PillarExample {
  paragraphs: ReactNode[];
  illustration: ReactNode;
  heading?: string;
}

export interface PillarPageProps {
  h1: string;
  intro: string;
  sections: PillarSection[];
  currentPath: string;
  illustrationBeforeLastSection?: ReactNode;
  footerNote?: ReactNode;
  example?: PillarExample;
}

export function PillarPage({
  h1,
  intro,
  sections,
  currentPath,
  illustrationBeforeLastSection,
  footerNote,
  example,
}: PillarPageProps) {
  const relatedGuides = relatedPillarLinks(currentPath);

  return (
    <Screen>
      <div className="page-section-narrow">
        <header className="pillar-hero" style={{ marginBottom: 28 }}>
          <h1 style={{ margin: '0 0 10px', font: `600 30px ${fonts.sans}`, color: colors.ink }}>{h1}</h1>
          <p className="pillar-prose" style={{ margin: 0, font: `400 16px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
            {intro}
          </p>
        </header>

        {example ? (
          <section className="pillar-example" style={{ marginBottom: 28 }}>
            <h2
              style={{
                margin: '0 0 10px',
                font: `600 20px ${fonts.sans}`,
                color: colors.ink,
              }}
            >
              {example.heading ?? 'Example'}
            </h2>
            <div className="pillar-example-visual">{example.illustration}</div>
            {example.paragraphs.map((paragraph, paragraphIndex) => (
              <p
                key={`example-${paragraphIndex}`}
                className="pillar-prose"
                style={{
                  margin: '0 0 12px',
                  font: `400 15px/1.6 ${fonts.sans}`,
                  color: colors.ink2,
                }}
              >
                {paragraph}
              </p>
            ))}
          </section>
        ) : null}

        {sections.map((section, sectionIndex) => (
          <div key={section.heading}>
            {sectionIndex === sections.length - 1 && illustrationBeforeLastSection ? (
              <div className="pillar-mid-illustration" style={{ marginBottom: 28 }}>
                {illustrationBeforeLastSection}
              </div>
            ) : null}
            <section className="pillar-section" style={{ marginBottom: 28 }}>
              <h2
                style={{
                  margin: '0 0 10px',
                  font: `600 20px ${fonts.sans}`,
                  color: colors.ink,
                }}
              >
                {section.heading}
              </h2>
              {section.paragraphs.map((paragraph, paragraphIndex) => (
                <p
                  key={`${section.heading}-${paragraphIndex}`}
                  className="pillar-prose"
                  style={{
                    margin: '0 0 12px',
                    font: `400 15px/1.6 ${fonts.sans}`,
                    color: colors.ink2,
                  }}
                >
                  {paragraph}
                </p>
              ))}
            </section>
          </div>
        ))}

        {footerNote ? (
          <p
            className="pillar-prose"
            style={{
              margin: '0 0 28px',
              font: `400 14px/1.6 ${fonts.sans}`,
              color: colors.ink2,
            }}
          >
            {footerNote}
          </p>
        ) : null}

        <div className="pillar-cta">
          <Link
            to="/"
            style={{
              display: 'inline-block',
              font: `600 13px ${fonts.mono}`,
              color: colors.accentInk,
              background: colors.accent,
              borderRadius: 7,
              padding: '12px 22px',
              textDecoration: 'none',
            }}
          >
            Compare liquidity ranking
          </Link>
        </div>

        <div
          className="pillar-related-guides"
          style={{
            borderTop: `1px solid ${colors.line}`,
            paddingTop: 24,
          }}
        >
          <h2
            style={{
              margin: '0 0 12px',
              font: `600 14px ${fonts.sans}`,
              color: colors.ink,
            }}
          >
            Related guides
          </h2>
          <GuideCardGrid guides={relatedGuides} />
        </div>
      </div>
    </Screen>
  );
}
