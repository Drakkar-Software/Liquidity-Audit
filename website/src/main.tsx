import { StrictMode } from 'react';
import { createRoot, hydrateRoot } from 'react-dom/client';
import { createBrowserRouter, RouterProvider, type HydrationState } from 'react-router-dom';
import { AppMonitoring } from './components/AppMonitoring';
import { initPostHogMonitoring, initSentryMonitoring } from './lib/monitoring';
import { createAppRoutes } from './router';
import './responsive.css';

initSentryMonitoring();
initPostHogMonitoring();

declare global {
  interface Window {
    __staticRouterHydrationData?: HydrationState;
  }
}

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Missing #root');
}

const hydrationData = window.__staticRouterHydrationData;
const router = createBrowserRouter(
  createAppRoutes(),
  hydrationData ? { hydrationData } : undefined,
);

const app = (
  <StrictMode>
    <AppMonitoring>
      <RouterProvider router={router} />
    </AppMonitoring>
  </StrictMode>
);

if (hydrationData && rootElement.hasChildNodes()) {
  hydrateRoot(rootElement, app);
} else {
  createRoot(rootElement).render(app);
}
