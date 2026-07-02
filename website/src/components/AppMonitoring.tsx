import type { ReactNode } from 'react';
import { initPostHogMonitoring, initSentryMonitoring } from '../lib/monitoring';

export interface AppMonitoringProps {
  children: ReactNode;
}

export function AppMonitoring({ children }: AppMonitoringProps) {
  initSentryMonitoring();
  initPostHogMonitoring();
  return children;
}
