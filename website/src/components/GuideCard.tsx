import { Link } from 'react-router-dom';
import type { PillarGuideLink } from '../lib/pillarGuides';
import { GuideIllustration } from './guideIllustrations';

export interface GuideCardProps {
  guide: PillarGuideLink;
}

export function GuideCard({ guide }: GuideCardProps) {
  return (
    <Link to={guide.path} className="guide-card-link">
      <div className="guide-illustration-animated">
        <GuideIllustration illustrationId={guide.illustrationId} />
      </div>
      <div className="guide-card-content">
        <div className="guide-card-title">{guide.title}</div>
        <div className="guide-card-blurb">{guide.cardBlurb}</div>
      </div>
    </Link>
  );
}

export function GuideCardGrid({ guides }: { guides: PillarGuideLink[] }) {
  return (
    <div className="guides-card-grid">
      {guides.map((guide) => (
        <GuideCard key={guide.path} guide={guide} />
      ))}
    </div>
  );
}
