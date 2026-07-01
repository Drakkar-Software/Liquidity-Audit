import { Link } from 'react-router-dom';
import { colors, fonts } from '../theme';

export interface SiteBrandProps {
  asLink?: boolean;
}

function SiteBrandMark() {
  return (
    <>
      <div
        style={{
          width: 9,
          height: 9,
          borderRadius: 2,
          background: colors.accent,
          boxShadow: `0 0 10px ${colors.accent}`,
        }}
      />
      <span style={{ font: `600 13px ${fonts.mono}`, letterSpacing: '.04em', color: colors.ink }}>
        CRYPTO LIQUIDITY<span style={{ color: colors.accent }}>AUDIT</span>
      </span>
    </>
  );
}

/** Shared site logo and wordmark used in nav and footer. */
export function SiteBrand({ asLink = true }: SiteBrandProps) {
  const brandStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    textDecoration: 'none',
  } as const;

  if (asLink) {
    return (
      <Link to="/" style={brandStyle}>
        <SiteBrandMark />
      </Link>
    );
  }

  return (
    <div style={brandStyle}>
      <SiteBrandMark />
    </div>
  );
}
