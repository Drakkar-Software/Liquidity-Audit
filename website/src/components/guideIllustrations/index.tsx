import type { ComponentType } from 'react';
import type { GuideIllustrationId } from '../../lib/pillarGuides';
import { BidAskSpreadIllustration } from './BidAskSpreadIllustration';
import { CryptoLiquidityIllustration } from './CryptoLiquidityIllustration';
import { LiquidityScoreIllustration } from './LiquidityScoreIllustration';
import { OrderBookIllustration } from './OrderBookIllustration';

type GuideIllustrationComponentProps = { variant?: 'default' | 'example' };

const ILLUSTRATION_BY_ID: Record<GuideIllustrationId, ComponentType<GuideIllustrationComponentProps>> = {
  cryptoLiquidity: CryptoLiquidityIllustration,
  orderBook: OrderBookIllustration,
  bidAskSpread: BidAskSpreadIllustration,
  liquidityScore: LiquidityScoreIllustration,
};

export function GuideIllustration({ illustrationId }: { illustrationId: GuideIllustrationId }) {
  const IllustrationComponent = ILLUSTRATION_BY_ID[illustrationId];
  return <IllustrationComponent />;
}

export { BidAskSpreadIllustration } from './BidAskSpreadIllustration';
export { CryptoLiquidityIllustration } from './CryptoLiquidityIllustration';
export { LiquidityScoreIllustration } from './LiquidityScoreIllustration';
export { MethodologyBookSchematicIllustration } from './MethodologyBookSchematicIllustration';
export { MethodologyGradeStripIllustration } from './MethodologyGradeStripIllustration';
export { MethodologyStepFlowIllustration } from './MethodologyStepFlowIllustration';
export { OrderBookIllustration } from './OrderBookIllustration';
