import type { TokenViewModel, RankingsViewModel } from '../../types';

// ---------------------------------------------------------------------------
// Poor-health report (the Split Cockpit reference): XYZ/USDT · 42 · D · Poor
// ---------------------------------------------------------------------------
export const xyzViewModel: TokenViewModel = {
  symbol: 'XYZ',
  pair: 'XYZ/USDT',
  exchange: 'Mexc',
  exchangeSlug: 'mexc',
  projectName: 'XYZ Protocol',
  updatedAgo: '2h ago',

  score: 42,
  grade: 'D',
  status: 'Poor',
  statusClass: 'status-poor',
  verdict:
    'XYZ/USDT loses ~2.4% to slippage on a $10k trade — 8× worse than comparable tokens.',
  slippageDisplaySize: 10000,
  issues: [
    { label: 'Good volume', ok: true },
    { label: 'Wide spread', ok: false },
    { label: 'Low depth', ok: false },
    { label: 'High slippage', ok: false },
    { label: 'Quote gaps', ok: false },
  ],

  slippage: [
    { size: 100, pct: 0.3, highlight: false },
    { size: 1000, pct: 0.9, highlight: false },
    { size: 5000, pct: 4.7, highlight: false },
    { size: 10000, pct: 8.2, highlight: true },
    { size: 20000, pct: 15.0, highlight: false },
  ],
  peers: [
    { name: 'Yours', spread: 2.8, depth: 9500, slippageTradeSize: 10000, slippagePct: 8.2, slippage10k: 8.2, isYours: true },
    { name: 'Peer Alpha', spread: 0.6, depth: 85000, slippageTradeSize: 10000, slippagePct: 1.1, slippage10k: 1.1, isYours: false },
    { name: 'Peer Beta', spread: 0.4, depth: 120000, slippageTradeSize: 10000, slippagePct: 0.8, slippage10k: 0.8, isYours: false },
    { name: 'Peer Gamma', spread: 0.7, depth: 92000, slippageTradeSize: 10000, slippagePct: 1.3, slippage10k: 1.3, isYours: false },
    { name: 'Median', spread: 0.5, depth: 100000, slippageTradeSize: 10000, slippagePct: 1.0, slippage10k: 1.0, isYours: false },
  ],
  healthDashboard: [
    { severity: 'Critical', title: 'Spread', impact: '4.6× above average', evidence: '2.8% vs 0.5% avg' },
    { severity: 'Critical', title: 'Depth ±2%', impact: '89% below average', evidence: '$9.5k vs $100k avg' },
    { severity: 'Critical', title: 'Slippage $10k', impact: '8× worse than average', evidence: '8.2% vs 1.0% avg' },
    { severity: 'Moderate', title: 'Volume consistency', impact: 'Hollow volume risk', evidence: 'Vol/depth 12.6×' },
  ],
  delistingRisk: [{ title: 'Low depth' }, { title: 'Low volume' }],
  mmPresence: { detected: false, label: 'Not detected' },
  investorSimulator: [
    { size: 25000, omitted: false, fillRatio: null, overpayPct: 14.1, overpayUsd: 3525, fairPrice: 1.0, avgPrice: 1.141, highlight: false },
    { size: 10000, omitted: false, fillRatio: null, overpayPct: 8.2, overpayUsd: 820, fairPrice: 1.0, avgPrice: 1.082, highlight: true },
    { size: 20000, omitted: true, fillRatio: 0.42, overpayPct: null, overpayUsd: null, fairPrice: 1.0, avgPrice: null, highlight: false },
  ],
  lostOpportunity: { size: 20000, cost: 2800, range: '6–15%' },
  rootCauses: [
    { rank: 1, title: 'Insufficient resting liquidity', evidence: 'Depth ±2% at $9.5k vs $100k peer median', impact: 'Large orders move price 8%+' },
    { rank: 2, title: 'Order book imbalance', evidence: '90% sell-side volume in 24h window', impact: 'Buyers face wider effective spread' },
  ],
  improvements: [
    { metric: 'Spread', current: '2.8%', potential: '0.5%' },
    { metric: 'Depth ±2%', current: '$9.5k', potential: '$100k' },
    { metric: 'Slippage $10k', current: '8.2%', potential: '1.0%' },
  ],
  roadmap: [
    { issue: 'Wide spread', fix: 'Resting orders both sides', cost: 'Low–Med', impact: '−2.3% spread' },
    { issue: 'Low depth', fix: 'Depth injection program', cost: 'Med', impact: '+$90k depth' },
    { issue: 'Quote gaps', fix: 'Continuous quoting', cost: 'Low', impact: '95%+ uptime' },
  ],
  implementationOptions: [
    { id: 'A', title: 'Internal MM', pros: 'Full control', cons: 'Capital + expertise required', url: 'https://github.com/Drakkar-Software/OctoBot-Market-Making' },
    { id: 'B', title: 'External firm', pros: 'Hands-off', cons: '$50–100k retainers', url: 'https://market-making.octobot.cloud/en/blog/crypto-market-makers' },
    { id: 'C', title: 'Automated infrastructure', pros: 'Continuous, configurable', cons: 'Setup + monitoring', url: 'https://market-making.octobot.cloud/' },
  ],
};

// ---------------------------------------------------------------------------
// Good-health report: SOL/USDT · 92 · A · Good
// ---------------------------------------------------------------------------
export const solViewModel: TokenViewModel = {
  symbol: 'SOL',
  pair: 'SOL/USDT',
  exchange: 'Mexc',
  exchangeSlug: 'mexc',
  projectName: 'Solana',
  updatedAgo: '1h ago',

  score: 92,
  grade: 'A',
  status: 'Good',
  statusClass: 'status-good',
  verdict:
    'SOL/USDT executes near fair price at $10k — in line with comparable tokens.',
  slippageDisplaySize: 10000,
  issues: [
    { label: 'Good volume', ok: true },
    { label: 'Wide spread', ok: true },
    { label: 'Low depth', ok: true },
    { label: 'High slippage', ok: true },
    { label: 'Quote gaps', ok: true },
  ],

  slippage: [],
  peers: [
    { name: 'Yours', spread: 0.04, depth: 3400000, slippagePct: 0.1, isYours: true },
    { name: 'Peer Alpha', spread: 0.05, depth: 2900000, slippagePct: 0.12, isYours: false },
    { name: 'Peer Beta', spread: 0.06, depth: 3100000, slippagePct: 0.14, isYours: false },
    { name: 'Median', spread: 0.05, depth: 3000000, slippagePct: 0.12, isYours: false },
  ],
  healthDashboard: [],
  delistingRisk: [],
  mmPresence: { detected: true, label: 'Active' },
  investorSimulator: [],
  lostOpportunity: null,
  rootCauses: [],
  improvements: [],
  roadmap: [],
  implementationOptions: [],
};

export const mexcRankings: RankingsViewModel = {
  exchange: 'mexc',
  exchangeLabel: 'MEXC',
  updatedLabel: '2026-06-14 20:00 UTC',
  rows: [
    { symbol: 'ETH/USDT', score: 95, vol: '18.0B', rank: 2 },
    { symbol: 'SOL/USDT', score: 92, vol: '2.1B', rank: 1 },
    { symbol: 'LINK/USDT', score: 88, vol: '450M', rank: 6 },
    { symbol: 'ARB/USDT', score: 85, vol: '320M', rank: 4 },
    { symbol: 'UNI/USDT', score: 84, vol: '210M', rank: 7 },
    { symbol: 'OP/USDT', score: 81, vol: '180M', rank: 5 },
    { symbol: 'PEPE/USDT', score: 78, vol: '890M', rank: 3 },
    { symbol: 'XYZ/USDT', score: 42, vol: '1.2M', rank: 8, highlight: true },
  ],
};
