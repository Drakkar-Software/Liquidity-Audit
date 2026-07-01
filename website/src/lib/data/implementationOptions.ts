import type { ImplementationOption } from '../../types';

export const IMPLEMENTATION_OPTIONS: ImplementationOption[] = [
  {
    id: 'A',
    title: 'Internal MM',
    pros: 'Full control',
    cons: 'Capital + expertise required',
    url: 'https://github.com/Drakkar-Software/OctoBot-Market-Making',
  },
  {
    id: 'B',
    title: 'External firm',
    pros: 'Hands-off',
    cons: '$50–100k retainers',
    url: 'https://market-making.octobot.cloud/en/blog/crypto-market-makers',
  },
  {
    id: 'C',
    title: 'Automated infrastructure',
    pros: 'Continuous, configurable',
    cons: 'Setup + monitoring',
    url: 'https://market-making.octobot.cloud/',
  },
];

export const IMPLEMENTATION_OPTIONS_SCORE_THRESHOLD = 60;

export function shouldShowImplementationOptions(score: number | null | undefined, roadmapLength: number): boolean {
  if (roadmapLength > 0) {
    return true;
  }
  if (score == null) {
    return false;
  }
  return score < IMPLEMENTATION_OPTIONS_SCORE_THRESHOLD;
}
