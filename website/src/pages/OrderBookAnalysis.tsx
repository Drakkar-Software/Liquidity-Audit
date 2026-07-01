import type { ReactNode } from 'react';
import { PillarPage } from '../components/PillarPage';
import { OrderBookIllustration } from '../components/guideIllustrations';
import { SiteTextLink } from '../components/SiteTextLink';

export function OrderBookAnalysis() {
  return (
    <PillarPage
      h1="Order book analysis"
      currentPath="/order-book-analysis"
      intro="Order book analysis reads the visible bids and asks on a spot pair at one time. You see best prices, size on each level, and how far from mid the book still has quotes."
      illustrationBeforeLastSection={<OrderBookIllustration variant="depth" />}
      sections={[
        {
          heading: 'Crypto order book',
          paragraphs: [
            'A crypto order book on a CEX lists resting limit orders. The best bid and best ask set the spread; deeper levels show where larger market orders would start to move price.',
            'Crypto Liquidity Audit pulls the top 50 bid and ask levels for each run.',
          ],
        },
        {
          heading: 'Order book depth',
          paragraphs: [
            'Order book depth is quote volume within a band around mid price, often ±2% for reports. Thin depth means a modest buy can lift the ask through several levels.',
            'Depth is labeled visible book only when the band is not fully spanned on one side.',
          ],
        },
        {
          heading: 'Order book liquidity analysis',
          paragraphs: [orderBookLiquidityParagraph()],
        },
      ]}
      example={{
        illustration: <OrderBookIllustration variant="example" />,
        paragraphs: [
          'Mid is 100.025. Best bid 100.00 carries 45k USDT; best ask 100.05 has 38k. Out to ±2%, the visible book shows $312k on bids and $284k on asks.',
        ],
      }}
    />
  );
}

function orderBookLiquidityParagraph(): ReactNode {
  return (
    <>
      Order book liquidity analysis combines spread, depth bands, and simulated slippage for standard buy
      sizes on that snapshot. It is one point in time on the visible CEX spot book, not a forecast. See{' '}
      <SiteTextLink to="/methodology">Methodology</SiteTextLink> for formulas or open a pair from the
      rankings.
    </>
  );
}
