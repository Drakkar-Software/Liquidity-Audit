import type { HydrationState } from 'react-router-dom';

const ROOT_PLACEHOLDER = '<div id="root"></div>';

function serializeHydrationData(hydrationData: HydrationState): string {
  return JSON.stringify(hydrationData).replace(/</g, '\\u003c');
}

export function injectRootHtml(shellHtml: string, appHtml: string): string {
  if (!shellHtml.includes(ROOT_PLACEHOLDER)) {
    throw new Error('Prerender shell is missing <div id="root"></div>');
  }
  return shellHtml.replace(ROOT_PLACEHOLDER, `<div id="root">${appHtml}</div>`);
}

export function injectHydrationScript(html: string, hydrationData: HydrationState): string {
  const hydrationScript = `<script>window.__staticRouterHydrationData=${serializeHydrationData(hydrationData)};</script>`;
  if (!html.includes('</body>')) {
    throw new Error('Prerender HTML is missing </body>');
  }
  return html.replace('</body>', `${hydrationScript}\n  </body>`);
}

export function assemblePrerenderedHtml(
  shellHtml: string,
  appHtml: string,
  hydrationData: HydrationState,
): string {
  return injectHydrationScript(injectRootHtml(shellHtml, appHtml), hydrationData);
}
