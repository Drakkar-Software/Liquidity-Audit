import { PillarPage } from '../components/PillarPage';
import { LiquidityScoreIllustration } from '../components/guideIllustrations';
import { SiteTextLink } from '../components/SiteTextLink';

export function LiquidityScore() {
  return (
    <PillarPage
      h1="Liquidity score"
      currentPath="/liquidity-score"
      intro="Liquidity score is a 0–100 summary of how tradable a spot pair looks on one order-book snapshot. It blends book shape with peer comparison on the same exchange."
      illustrationBeforeLastSection={<LiquidityScoreIllustration variant="grades" />}
      sections={[
        {
          heading: 'Liquidity score for crypto pairs',
          paragraphs: [
            'On crypto spot pairs, liquidity score crypto rankings sort pairs on each exchange so you can scan thin books before opening a report.',
            'The headline number comes with a letter grade from A to F and issue chips that flag spread, depth, or slippage problems.',
          ],
        },
        {
          heading: 'What goes into the number',
          paragraphs: [
            <>
              Half of the score reflects internal book shape: level coverage, tight and wide depth bands,
              and spread tightness. The other half compares spread, depth, and slippage to similar peers
              when enough qualify. See <SiteTextLink to="/methodology">Methodology</SiteTextLink> for the
              full breakdown.
            </>,
          ],
        },
      ]}
      example={{
        illustration: <LiquidityScoreIllustration variant="example" />,
        paragraphs: [
          'One pair scores 68/100, grade C. Spread is 0.12%, but a $5,000 buy still slips 0.31%. The headline number reflects both.',
        ],
      }}
    />
  );
}
