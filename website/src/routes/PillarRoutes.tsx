import { CryptoLiquidity } from '../pages/CryptoLiquidity';
import { OrderBookAnalysis } from '../pages/OrderBookAnalysis';
import { BidAskSpread } from '../pages/BidAskSpread';
import { LiquidityScore } from '../pages/LiquidityScore';
import { useStaticPageMeta } from '../lib/pageMetaHooks';

export function CryptoLiquidityRoute() {
  useStaticPageMeta('cryptoLiquidity', '/crypto-liquidity', 'Crypto liquidity');
  return <CryptoLiquidity />;
}

export function OrderBookAnalysisRoute() {
  useStaticPageMeta('orderBookAnalysis', '/order-book-analysis', 'Order book analysis');
  return <OrderBookAnalysis />;
}

export function BidAskSpreadRoute() {
  useStaticPageMeta('bidAskSpread', '/bid-ask-spread', 'Bid ask spread');
  return <BidAskSpread />;
}

export function LiquidityScoreRoute() {
  useStaticPageMeta('liquidityScore', '/liquidity-score', 'Liquidity score');
  return <LiquidityScore />;
}
