import type { ReactNode } from 'react';

export interface AppMonitoringProps {
  children: ReactNode;
}

export function AppMonitoring({ children }: AppMonitoringProps) {
  return children;
}
