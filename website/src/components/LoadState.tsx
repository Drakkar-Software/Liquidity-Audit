import { Link } from 'react-router-dom';
import { colors, fonts } from '../theme';
import { Screen } from '../components/Screen';

interface LoadErrorProps {
  message: string;
}

export function LoadError({ message }: LoadErrorProps) {
  return (
    <Screen footer={true}>
      <div className="page-section-centered" role="alert">
        <h1 style={{ margin: '0 0 12px', font: `600 22px ${fonts.sans}`, color: colors.ink }}>
          Analysis unavailable
        </h1>
        <p style={{ margin: '0 0 24px', font: `400 14px ${fonts.sans}`, color: colors.ink2 }}>
          {message}
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

export function LoadingScreen({ label }: { label: string }) {
  return (
    <Screen footer={true}>
      <div className="page-section-centered" role="status" aria-live="polite">
        <p style={{ margin: 0, font: `500 14px ${fonts.mono}`, color: colors.ink2 }}>{label}</p>
      </div>
    </Screen>
  );
}
