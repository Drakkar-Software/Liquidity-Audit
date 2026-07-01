import { Link } from 'react-router-dom';
import { colors, fonts } from '../theme';
import { AUDIT_LINKS, MARKET_MAKING_LINKS, PILLAR_GUIDE_LINKS } from '../lib/pillarGuides';
import { SiteBrand } from './SiteBrand';
import { SiteTextLink } from './SiteTextLink';

/** Shared bottom chrome bar. */
export function Footer() {
  return (
    <footer
      className="footer-bar"
      style={{
        padding: '24px',
        borderTop: `1px solid ${colors.line}`,
        background: colors.navBg,
        font: `400 11px ${fonts.sans}`,
        color: colors.ink3,
      }}
    >
      <div className="footer-columns">
        <div className="footer-brand">
          <SiteBrand />
          <p className="footer-disclaimer">Independent analysis · Not financial advice</p>
        </div>
        <div>
          <p className="footer-column-title">Guides</p>
          <ul className="footer-link-list">
            {PILLAR_GUIDE_LINKS.map((guide) => (
              <li key={guide.path}>
                <Link to={guide.path} className="site-text-link">
                  {guide.title}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="footer-column-title">Audit</p>
          <ul className="footer-link-list">
            {AUDIT_LINKS.map((link) => (
              <li key={link.path}>
                <Link to={link.path} className="site-text-link">
                  {link.title}
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="footer-column-title">Market making</p>
          <ul className="footer-link-list">
            {MARKET_MAKING_LINKS.map((link) => (
              <li key={link.href}>
                <SiteTextLink external href={link.href}>
                  {link.title}
                </SiteTextLink>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </footer>
  );
}
