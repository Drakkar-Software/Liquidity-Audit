import { PillarPage } from '../components/PillarPage';
import {
  CryptoLiquidityIllustration,
  OrderBookIllustration,
} from '../components/guideIllustrations';

export function CryptoLiquidity() {
  return (
    <PillarPage
      h1="Crypto liquidity"
      currentPath="/crypto-liquidity"
      intro="Crypto liquidity is how much size you can trade on a spot pair without moving the price much. On a CEX, that shows up in the visible order book at one moment."
      illustrationBeforeLastSection={<OrderBookIllustration />}
      sections={[
        {
          heading: 'Liquidity analysis',
          paragraphs: [
            'Liquidity analysis starts with spread, depth near mid price, and how far prices move when you walk the book for a fixed buy size.',
            'Crypto Liquidity Audit runs that read on one snapshot per exchange so you can compare pairs on the same venue.',
          ],
        },
        {
          heading: 'Trading liquidity',
          paragraphs: [
            'Trading liquidity matters when you enter or exit a position. A tight spread and deep book near mid mean lower cost to trade the size you need.',
            'Rankings sort pairs by liquidity score so you can spot thin books before you open a report.',
          ],
        },
        {
          heading: 'Crypto market liquidity analysis',
          paragraphs: [
            'Crypto market liquidity analysis on spot CEX books is limited to what is posted: top bid and ask levels, not hidden liquidity or off-exchange flow.',
            'Use exchange liquidity comparison on the home page, then open a pair report for spread, depth, and slippage from that snapshot.',
          ],
        },
      ]}
      example={{
        illustration: <CryptoLiquidityIllustration variant="example" />,
        paragraphs: [
          'Take SOL/USDT on MEXC: bid 142.50, ask 142.58. Spread is 0.056%, which looks tight at the top. Buy $10,000 through the asks and you still finish 0.18% above mid once you clear the levels behind the best quote.',
        ],
      }}
    />
  );
}
