import { StrictMode } from 'react';
import { renderToString } from 'react-dom/server';
import {
  createStaticHandler,
  createStaticRouter,
  StaticRouterProvider,
  type HydrationState,
} from 'react-router-dom';
import { AppMonitoring } from '../components/AppMonitoring';
import { createAppRoutes } from '../router';

export interface StaticPageRenderResult {
  appHtml: string;
  hydrationData: HydrationState;
}

const { query, dataRoutes } = createStaticHandler(createAppRoutes());

export async function renderStaticPage(pathname: string): Promise<StaticPageRenderResult> {
  const request = new Request(`https://ssr.local${pathname}`);
  const context = await query(request);

  if (context instanceof Response) {
    throw new Error(`Unexpected redirect for prerender path ${pathname}`);
  }

  const router = createStaticRouter(dataRoutes, context);
  const appHtml = renderToString(
    <StrictMode>
      <AppMonitoring>
        <StaticRouterProvider router={router} context={context} />
      </AppMonitoring>
    </StrictMode>,
  );

  const hydrationData: HydrationState = {
    loaderData: context.loaderData,
    actionData: context.actionData,
    errors: context.errors,
  };

  return { appHtml, hydrationData };
}
