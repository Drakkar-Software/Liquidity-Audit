import { PillarPage } from '../components/PillarPage';
import { BidAskSpreadIllustration } from '../components/guideIllustrations';

export function BidAskSpread() {
  return (
    <PillarPage
      h1="Bid-ask spread"
      currentPath="/bid-ask-spread"
      intro="Bid ask spread is the gap between the best ask and the best bid on a spot pair. A wider spread means you pay more to cross the book on entry and exit."
      illustrationBeforeLastSection={<BidAskSpreadIllustration variant="analysis" />}
      sections={[
        {
          heading: 'Crypto spread',
          paragraphs: [
            'Crypto spread on a CEX spot pair is usually quoted as a percent of mid price. Stable pairs with deep books tend to show tighter spreads than thin alt pairs.',
            'Spread alone does not tell the full story: a tight top-of-book can still hide thin depth a few levels away.',
          ],
        },
        {
          heading: 'Crypto bid-ask spread analysis',
          paragraphs: [
            'Crypto bid ask spread analysis on Crypto Liquidity Audit reads best bid and best ask from the same snapshot as depth and slippage.',
            'Pair reports show spread percent next to depth bands and simulated buy sizes so you can judge execution cost at a glance.',
          ],
        },
      ]}
      example={{
        illustration: <BidAskSpreadIllustration variant="example" />,
        paragraphs: [
          'Bid 1.0002, ask 1.0008, mid 1.0005. That gap is 0.0006 in price, or 0.060% of mid. You pay it every time you cross the book.',
        ],
      }}
    />
  );
}
