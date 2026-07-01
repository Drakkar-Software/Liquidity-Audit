import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadEnv } from 'vite';
import { assemblePrerenderedHtml } from '../src/prerender/assemblePrerenderedHtml';
import { renderStaticPage } from '../src/prerender/renderStaticPage';
import { STATIC_PRERENDER_PAGES } from '../src/lib/staticPrerenderPages';
import { buildHomePageMeta, buildStaticPageMeta, injectMetaTags, normalizeSiteUrl } from '../src/lib/siteMeta';

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const websiteRoot = path.resolve(scriptDirectory, '..');
const distDirectory = path.resolve(websiteRoot, 'dist');

function loadWebsiteEnv(): Record<string, string> {
  const mode = process.env.NODE_ENV === 'development' ? 'development' : 'production';
  return loadEnv(mode, websiteRoot, '');
}

function resolveEnvValue(fileEnv: Record<string, string>, key: string): string | undefined {
  const fromProcess = process.env[key]?.trim();
  if (fromProcess) {
    return fromProcess;
  }
  return fileEnv[key]?.trim();
}

async function main(): Promise<void> {
  const fileEnv = loadWebsiteEnv();
  const siteUrl = resolveEnvValue(fileEnv, 'VITE_SITE_URL');
  if (!siteUrl) {
    throw new Error(
      'VITE_SITE_URL must be set to prerender static pages (shell env or .env / .env.production)',
    );
  }

  const shellHtml = await fs.readFile(path.join(distDirectory, 'index.html'), 'utf8');
  const normalizedSiteUrl = normalizeSiteUrl(siteUrl);

  for (const page of STATIC_PRERENDER_PAGES) {
    const { appHtml, hydrationData } = await renderStaticPage(page.path);
    const pageMeta = buildStaticPageMeta(
      normalizedSiteUrl,
      page.pageKey,
      page.path,
      page.label,
      page.faqs ? { faqs: page.faqs } : undefined,
    );
    const htmlWithMeta = injectMetaTags(shellHtml, pageMeta);
    const prerenderedHtml = assemblePrerenderedHtml(htmlWithMeta, appHtml, hydrationData);

    const outputDirectory = path.join(distDirectory, page.path.slice(1));
    await fs.mkdir(outputDirectory, { recursive: true });
    await fs.writeFile(path.join(outputDirectory, 'index.html'), prerenderedHtml, 'utf8');
  }

  console.log(`Prerendered ${STATIC_PRERENDER_PAGES.length} static pages into ${distDirectory}`);

  const { appHtml: homeAppHtml, hydrationData: homeHydrationData } = await renderStaticPage('/');
  const homeHtmlWithMeta = injectMetaTags(shellHtml, buildHomePageMeta(normalizedSiteUrl));
  const prerenderedHomeHtml = assemblePrerenderedHtml(homeHtmlWithMeta, homeAppHtml, homeHydrationData);
  await fs.writeFile(path.join(distDirectory, 'index.html'), prerenderedHomeHtml, 'utf8');
  console.log('Prerendered home (static shell) to dist/index.html');
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exit(1);
});
