import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { getPostHogClient, isPostHogEnabled } from '../lib/monitoring';

export function PostHogPageView(): null {
  const location = useLocation();

  useEffect(() => {
    const posthog = getPostHogClient();
    if (!isPostHogEnabled() || !posthog) {
      return;
    }

    posthog.capture('$pageview', {
      $current_url: window.location.href,
    });
  }, [location.pathname]);

  return null;
}
