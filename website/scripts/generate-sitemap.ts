import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { loadEnv } from 'vite';
import { EXCHANGES } from '../src/lib/data/exchanges';
import { pairToSlug } from '../src/lib/data/loader';
import { STATIC_MARKETING_PATHS } from '../src/lib/staticPrerenderPages';
import { normalizeSiteUrl } from '../src/lib/siteMeta';

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const websiteRoot = path.resolve(scriptDirectory, '..');
const distDirectory = path.resolve(websiteRoot, 'dist');

const STATIC_PATHS = ['/', ...STATIC_MARKETING_PATHS];

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

interface RankingsPayload {
  exchange: string;
  pairs: { symbol: string }[];
}

async function fetchRankingsUrls(analysisDataBase: string): Promise<string[]> {
  const pairPaths: string[] = [];
  for (const exchange of EXCHANGES) {
    const rankingsUrl = `${analysisDataBase.replace(/\/$/, '')}/rankings/${exchange}.json`;
    let response: Response;
    try {
      response = await fetch(rankingsUrl);
    } catch {
      continue;
    }
    if (!response.ok) {
      continue;
    }
    const payload = (await response.json()) as RankingsPayload;
    for (const row of payload.pairs) {
      pairPaths.push(`/pairs/${exchange}/${pairToSlug(row.symbol)}`);
    }
  }
  return pairPaths;
}

function buildSitemapXml(siteUrl: string, paths: string[]): string {
  const origin = normalizeSiteUrl(siteUrl);
  const urlEntries = paths
    .map((routePath) => {
      const loc = routePath === '/' ? `${origin}/` : `${origin}${routePath}`;
      return `  <url><loc>${loc}</loc></url>`;
    })
    .join('\n');
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urlEntries}\n</urlset>\n`;
}

function buildRobotsTxt(siteUrl: string): string {
  const origin = normalizeSiteUrl(siteUrl);
  return `User-agent: *\nAllow: /\nSitemap: ${origin}/sitemap.xml\n`;
}

async function main(): Promise<void> {
  const fileEnv = loadWebsiteEnv();
  const siteUrl = resolveEnvValue(fileEnv, 'VITE_SITE_URL');
  if (!siteUrl) {
    throw new Error(
      'VITE_SITE_URL must be set to generate sitemap.xml and robots.txt (shell env or .env / .env.production)',
    );
  }

  const paths = [...STATIC_PATHS];
  const analysisDataBase = resolveEnvValue(fileEnv, 'VITE_ANALYSIS_DATA_BASE');
  if (analysisDataBase) {
    const pairPaths = await fetchRankingsUrls(analysisDataBase);
    paths.push(...pairPaths);
  }

  const uniquePaths = [...new Set(paths)];
  await fs.mkdir(distDirectory, { recursive: true });
  await fs.writeFile(path.join(distDirectory, 'sitemap.xml'), buildSitemapXml(siteUrl, uniquePaths), 'utf8');
  await fs.writeFile(path.join(distDirectory, 'robots.txt'), buildRobotsTxt(siteUrl), 'utf8');
  console.log(`Wrote sitemap.xml and robots.txt (${uniquePaths.length} URLs) to ${distDirectory}`);
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error(message);
  process.exit(1);
});
