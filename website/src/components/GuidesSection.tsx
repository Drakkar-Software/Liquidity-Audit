import { fonts, colors } from '../theme';
import { PILLAR_GUIDE_LINKS } from '../lib/pillarGuides';
import { GuideCardGrid } from './GuideCard';

export function GuidesSection() {
  return (
    <section>
      <h2 style={{ margin: '0 0 8px', font: `600 16px ${fonts.sans}`, color: colors.ink }}>Guides</h2>
      <p style={{ margin: '0 0 18px', font: `400 13px/1.6 ${fonts.sans}`, color: colors.ink2 }}>
        Short reads on spread, depth, and scoring. Each guide links back to the rankings tool.
      </p>
      <GuideCardGrid guides={PILLAR_GUIDE_LINKS} />
    </section>
  );
}
