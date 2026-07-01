import { usePostHog } from '@posthog/react';
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { isPostHogEnabled } from '../lib/monitoring';

export function PostHogPageView(): null {
  const location = useLocation();
  const posthog = usePostHog();

  useEffect(() => {
    if (!isPostHogEnabled() || !posthog) {
      return;
    }

    posthog.capture('$pageview', {
      $current_url: window.location.href,
    });
  }, [location.pathname, posthog]);

  return null;
}
