import React from 'react';
import { colors } from '../theme';
import type { IssueTooltipContent } from './issueCopy';

export function renderIssueTooltip(content: IssueTooltipContent): React.ReactNode {
  return (
    <>
      <strong style={{ color: colors.ink, fontWeight: 600 }}>{content.title}</strong>
      <p style={{ margin: '4px 0 0', color: colors.ink2, lineHeight: 1.45, wordBreak: 'normal' }}>
        {content.body}
      </p>
    </>
  );
}
