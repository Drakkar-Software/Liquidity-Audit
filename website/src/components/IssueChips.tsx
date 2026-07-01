import React from 'react';
import { colors, fonts } from '../theme';
import type { Issue, DelistingFactor } from '../types';
import { Tooltip } from './Tooltip';
import {
  ALL_CHECKS_PASSED_TOOLTIP,
  DELISTING_RISK_CHIP_TEXT,
  DELISTING_RISK_TOOLTIP,
  getIssueChipDisplay,
} from '../lib/issueCopy';
import { renderIssueTooltip } from '../lib/issueTooltipContent';

export interface IssueChipsProps {
  issues: Issue[];
  delistingRisk: DelistingFactor[];
}

const baseChip: React.CSSProperties = {
  font: `500 11px ${fonts.mono}`,
  borderRadius: 5,
  padding: '5px 9px',
};

const okChip: React.CSSProperties = {
  ...baseChip,
  color: colors.green,
  background: 'rgba(70,196,106,.1)',
  border: '1px solid rgba(70,196,106,.3)',
};

const badChip: React.CSSProperties = {
  ...baseChip,
  color: colors.red,
  background: 'rgba(240,88,77,.09)',
  border: '1px solid rgba(240,88,77,.3)',
};

const delistChip: React.CSSProperties = {
  font: `600 11px ${fonts.mono}`,
  color: '#1a1206',
  background: colors.amber,
  borderRadius: 5,
  padding: '5px 9px',
};

/**
 * Issue summary chips. When every check passes and there's no delisting risk,
 * collapses to a single "All checks passed" chip (per copy rules).
 */
export function IssueChips({ issues, delistingRisk }: IssueChipsProps) {
  const allPassed =
    issues.length > 0 && issues.every((issue) => issue.ok) && delistingRisk.length === 0;

  if (allPassed) {
    return (
      <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>
        <Tooltip content={renderIssueTooltip(ALL_CHECKS_PASSED_TOOLTIP)}>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              font: `500 11px ${fonts.mono}`,
              color: colors.green,
              background: 'rgba(70,196,106,.12)',
              border: '1px solid rgba(70,196,106,.35)',
              borderRadius: 5,
              padding: '6px 12px',
            }}
          >
            ✓ All checks passed
          </span>
        </Tooltip>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap' }}>
      {issues.map((issue) => {
        const { text, tooltip } = getIssueChipDisplay(issue.label, issue.ok);
        return (
          <Tooltip
            key={issue.label}
            content={tooltip ? renderIssueTooltip(tooltip) : null}
          >
            <span style={issue.ok ? okChip : badChip}>
              {issue.ok ? '✓' : '✕'} {text}
            </span>
          </Tooltip>
        );
      })}
      {delistingRisk.length > 0 ? (
        <Tooltip content={renderIssueTooltip(DELISTING_RISK_TOOLTIP)}>
          <span style={delistChip}>⚠ {DELISTING_RISK_CHIP_TEXT}</span>
        </Tooltip>
      ) : null}
    </div>
  );
}
