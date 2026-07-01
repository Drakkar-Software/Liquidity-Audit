import { describe, expect, it } from 'vitest';
import printCss from '../print.css?raw';

const requiredPrintSelectors = [
  '.health-metric-row',
  '.health-metric-title',
  '.peer-bar-row',
  '.investor-sim-grid',
  '.impl-options-grid',
  '.improvements-grid-head',
  '.improvements-grid-row',
  '.roadmap-grid-head',
  '.roadmap-grid-row',
  '.improvements-scroll',
  '.roadmap-scroll',
  '.improvements-table',
  '.roadmap-table',
  '.skip-link',
  '.print-only.token-report-score-compact',
  '.no-print.token-report-score-compact',
];

describe('print.css layout rules', () => {
  it('defines print grid rules for token-report layout classes', () => {
    expect(printCss).toContain('@media print');

    for (const selector of requiredPrintSelectors) {
      expect(printCss).toContain(selector);
    }

    expect(printCss).toMatch(/\.investor-sim-grid[\s\S]*grid-template-columns:\s*repeat\(3,\s*1fr\)/);
    expect(printCss).toMatch(/\.peer-bar-row[\s\S]*grid-template-columns:\s*90px 1fr 60px/);
  });
});
