import type { FaqItem } from './siteMeta';

export const METHODOLOGY_FAQS: FaqItem[] = [
  {
    question: 'What is a liquidity score?',
    answer:
      'The liquidity score is a 0–100 grade from one visible spot order-book snapshot. It blends book shape and peer comparison on the same exchange.',
  },
  {
    question: 'How do you measure liquidity?',
    answer:
      'We read spread, depth within price bands, simulated slippage for standard buy sizes, and volume consistency from the visible CEX spot book.',
  },
  {
    question: 'How to check token liquidity?',
    answer:
      'Pick an exchange, search the pair, and open the report. You get spread, depth, slippage, and the liquidity score from that snapshot.',
  },
  {
    question: 'What is order book liquidity analysis?',
    answer:
      'It is a read of the visible bid and ask levels at one moment: best prices, depth near mid, and how much size you can buy before prices move.',
  },
];
