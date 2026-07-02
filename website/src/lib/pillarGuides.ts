export const OCTOBOT_MARKET_MAKING_URL = 'https://market-making.octobot.cloud/';

export const CRYPTO_MARKET_MAKING_BLOG_URL =
  'https://market-making.octobot.cloud/en/blog/crypto-market-makers';

export const OPEN_SOURCE_MARKET_MAKING_BLOG_URL =
  'https://market-making.octobot.cloud/en/blog/hummingbot-vs-octobot';

export const LIQUIDITY_AUDIT_GITHUB_URL =
  'https://github.com/Drakkar-Software/Liquidity-Audit';

export type GuideIllustrationId = 'cryptoLiquidity' | 'orderBook' | 'bidAskSpread' | 'liquidityScore';

export interface PillarGuideLink {
  path: string;
  title: string;
  cardBlurb: string;
  keyword: string;
  illustrationId: GuideIllustrationId;
}

export const PILLAR_GUIDE_LINKS: PillarGuideLink[] = [
  {
    path: '/crypto-liquidity',
    title: 'Crypto liquidity',
    cardBlurb: 'How spot books absorb size on CEX pairs',
    keyword: 'crypto liquidity',
    illustrationId: 'cryptoLiquidity',
  },
  {
    path: '/order-book-analysis',
    title: 'Order book analysis',
    cardBlurb: 'Read bids, asks, and depth from one snapshot',
    keyword: 'order book analysis',
    illustrationId: 'orderBook',
  },
  {
    path: '/bid-ask-spread',
    title: 'Bid-ask spread',
    cardBlurb: 'What the gap between bid and ask costs you',
    keyword: 'bid ask spread',
    illustrationId: 'bidAskSpread',
  },
  {
    path: '/liquidity-score',
    title: 'Liquidity score',
    cardBlurb: 'How the 0–100 grade summarizes tradability',
    keyword: 'liquidity score',
    illustrationId: 'liquidityScore',
  },
];

export interface AuditLink {
  path: string;
  title: string;
}

export const AUDIT_LINKS: AuditLink[] = [
  { path: '/', title: 'Rankings' },
  { path: '/methodology', title: 'Methodology' },
  { path: '/about', title: 'About' },
  { path: '/learn', title: 'Learn' },
  { path: '/case-studies', title: 'Case studies' },
];

export interface MarketMakingLink {
  href: string;
  title: string;
}

export const MARKET_MAKING_LINKS: MarketMakingLink[] = [
  { href: CRYPTO_MARKET_MAKING_BLOG_URL, title: 'Crypto market making' },
  { href: OPEN_SOURCE_MARKET_MAKING_BLOG_URL, title: 'Open source market making' },
];

export function relatedPillarLinks(currentPath: string): PillarGuideLink[] {
  return PILLAR_GUIDE_LINKS.filter((guide) => guide.path !== currentPath);
}
