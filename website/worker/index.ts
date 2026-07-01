import {
  buildPairMeta,
  injectMetaTags,
  parsePairPath,
  resolveWorkerSiteUrl,
  type PairAnalysisMetaSource,
} from '../src/lib/siteMeta';

export interface WorkerEnv {
  ASSETS: Fetcher;
  SITE_URL: string;
  ANALYSIS_DATA_BASE: string;
}

async function fetchPairPayload(
  analysisDataBase: string,
  exchange: string,
  slug: string,
): Promise<PairAnalysisMetaSource | null> {
  const dataBase = analysisDataBase.replace(/\/$/, '');
  const pairUrl = `${dataBase}/pairs/${exchange}/${slug}.json`;
  let response: Response;
  try {
    response = await fetch(pairUrl);
  } catch {
    return null;
  }
  if (!response.ok) {
    return null;
  }
  try {
    return (await response.json()) as PairAnalysisMetaSource;
  } catch {
    return null;
  }
}

export default {
  async fetch(request: Request, env: WorkerEnv): Promise<Response> {
    const url = new URL(request.url);
    const pairPath = parsePairPath(url.pathname);

    if (pairPath && request.method === 'GET') {
      const siteUrl = resolveWorkerSiteUrl(env.SITE_URL, url.origin);
      const payload = await fetchPairPayload(env.ANALYSIS_DATA_BASE, pairPath.exchange, pairPath.slug);
      if (payload && siteUrl) {
        const pair = payload.symbol ?? pairPath.slug.replace('_', '/');
        const pageMeta = buildPairMeta(siteUrl, pairPath.exchange, pairPath.slug, pair, payload);
        const shellResponse = await env.ASSETS.fetch(new URL('/', url.origin).toString());
        if (shellResponse.ok) {
          const shellHtml = await shellResponse.text();
          return new Response(injectMetaTags(shellHtml, pageMeta), {
            headers: {
              'Content-Type': 'text/html; charset=utf-8',
              'Cache-Control': 'public, max-age=300',
            },
          });
        }
      }
    }

    return env.ASSETS.fetch(request);
  },
};
