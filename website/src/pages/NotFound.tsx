import { Link } from 'react-router-dom';
import { colors, fonts } from '../theme';
import { Screen } from '../components/Screen';
import { useNotFoundPageMeta } from '../lib/pageMetaHooks';

export function NotFound() {
  useNotFoundPageMeta();

  return (
    <Screen footer={true}>
      <div className="page-section-centered">
        <h1 style={{ margin: '0 0 12px', font: `600 28px ${fonts.sans}`, color: colors.ink }}>
          Page not found
        </h1>
        <p style={{ margin: '0 0 24px', font: `400 15px ${fonts.sans}`, color: colors.ink2 }}>
          The page you requested does not exist.
        </p>
        <Link
          to="/"
          style={{
            font: `600 13px ${fonts.mono}`,
            color: colors.accentInk,
            background: colors.accent,
            borderRadius: 7,
            padding: '12px 22px',
            textDecoration: 'none',
          }}
        >
          Back to comparison
        </Link>
      </div>
    </Screen>
  );
}
