import { PostHogProvider } from '@posthog/react';
import type posthog from 'posthog-js';
import { useEffect, useState, type ReactNode } from 'react';
import {
  getPostHogClient,
  initPostHogMonitoring,
  initSentryMonitoring,
  isPostHogEnabled,
} from '../lib/monitoring';

export interface AppMonitoringProps {
  children: ReactNode;
}

export function AppMonitoring({ children }: AppMonitoringProps) {
  const [posthogClient, setPosthogClient] = useState<typeof posthog | null>(null);

  useEffect(() => {
    const bootstrapMonitoring = () => {
      initSentryMonitoring();
      initPostHogMonitoring();
      setPosthogClient(getPostHogClient());
    };

    if (typeof window.requestIdleCallback === 'function') {
      const idleCallbackId = window.requestIdleCallback(bootstrapMonitoring);
      return () => window.cancelIdleCallback(idleCallbackId);
    }

    const timeoutId = window.setTimeout(bootstrapMonitoring, 1);
    return () => window.clearTimeout(timeoutId);
  }, []);

  if (!isPostHogEnabled() || !posthogClient) {
    return children;
  }

  return <PostHogProvider client={posthogClient}>{children}</PostHogProvider>;
}
