import { useEffect, useState, type CSSProperties } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { colors, fonts } from '../theme';
import { ExchangeSelect } from './ExchangeSelect';
import { SiteBrand } from './SiteBrand';

export type NavItem = 'Comparison' | 'Case Studies' | 'Learn' | 'Methodology' | 'About';

const ITEMS: { label: NavItem; path: string }[] = [
  { label: 'Comparison', path: '/' },
  { label: 'Case Studies', path: '/case-studies' },
  { label: 'Learn', path: '/learn' },
  { label: 'Methodology', path: '/methodology' },
  { label: 'About', path: '/about' },
];

export interface NavProps {
  /** Highlighted nav item. */
  active?: NavItem;
  /** Exchange slug, e.g. "mexc". Shown when onExchangeChange is set. */
  exchange?: string;
  onExchangeChange?: (exchange: string) => void;
}

function isNavActive(pathname: string, path: string): boolean {
  if (pathname.startsWith('/pairs/')) {
    return false;
  }
  if (path === '/') {
    return pathname === '/';
  }
  return pathname.startsWith(path);
}

function navLinkStyle(highlighted: boolean): CSSProperties {
  return {
    color: highlighted ? colors.ink : colors.ink2,
    textDecoration: 'none',
    font: `500 12px ${fonts.sans}`,
  };
}

/** The shared top chrome bar (logo + nav links + optional exchange picker). */
export function Nav({ active, exchange, onExchangeChange }: NavProps) {
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuPanelId = 'site-nav-menu-panel';

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!menuOpen) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setMenuOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [menuOpen]);

  const renderNavLinks = (linkClassName?: string) =>
    ITEMS.map((item) => {
      const onReportPage = location.pathname.startsWith('/pairs/');
      const highlighted =
        !onReportPage &&
        (active === item.label || (active == null && isNavActive(location.pathname, item.path)));
      return (
        <Link
          key={item.label}
          to={item.path}
          className={linkClassName}
          style={navLinkStyle(highlighted)}
          onClick={() => setMenuOpen(false)}
        >
          {item.label}
        </Link>
      );
    });

  return (
    <nav className="site-nav" style={{ background: colors.navBg, borderBottom: `1px solid ${colors.line}` }}>
      <div className="site-nav-top">
        <SiteBrand />

        <div className="site-nav-links-desktop">{renderNavLinks()}</div>

        <div className="site-nav-right">
          {exchange && onExchangeChange ? (
            <ExchangeSelect variant="nav" value={exchange} onChange={onExchangeChange} />
          ) : (
            <div className="site-nav-spacer" />
          )}
          <button
            type="button"
            className="site-nav-menu-btn"
            aria-label="Menu"
            aria-expanded={menuOpen}
            aria-controls={menuPanelId}
            onClick={() => setMenuOpen((wasOpen) => !wasOpen)}
          >
            {menuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>

      <div
        id={menuPanelId}
        className={`site-nav-links${menuOpen ? ' is-open' : ''}`}
        role="navigation"
        aria-label="Mobile"
      >
        {renderNavLinks()}
      </div>
    </nav>
  );
}
