import { METHODOLOGY_FAQS } from './methodologyFaqs';
import type { FaqItem } from './siteMeta';
import type { StaticPageKey } from './pageMetaHooks';

export interface StaticPrerenderPage {
  path: string;
  pageKey: StaticPageKey;
  label: string;
  faqs?: FaqItem[];
}

export const STATIC_PRERENDER_PAGES: StaticPrerenderPage[] = [
  { path: '/methodology', pageKey: 'methodology', label: 'Methodology', faqs: METHODOLOGY_FAQS },
  { path: '/crypto-liquidity', pageKey: 'cryptoLiquidity', label: 'Crypto liquidity' },
  { path: '/order-book-analysis', pageKey: 'orderBookAnalysis', label: 'Order book analysis' },
  { path: '/bid-ask-spread', pageKey: 'bidAskSpread', label: 'Bid ask spread' },
  { path: '/liquidity-score', pageKey: 'liquidityScore', label: 'Liquidity score' },
  { path: '/about', pageKey: 'about', label: 'About' },
  { path: '/learn', pageKey: 'learn', label: 'Learn' },
  { path: '/case-studies', pageKey: 'caseStudies', label: 'Case studies' },
];

export const STATIC_MARKETING_PATHS = STATIC_PRERENDER_PAGES.map((page) => page.path);
