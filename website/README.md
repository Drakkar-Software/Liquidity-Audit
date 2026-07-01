# Crypto Liquidity Audit — React / TypeScript website

A React + TypeScript SPA for the Crypto Liquidity Audit product: the Split Cockpit token
report plus comparison, methodology, learn, about, and case studies pages. Styling
is **inline styles** driven by a shared token module — no CSS framework.

## Testing

```bash
cd Liquidity-Audit/website
npm run test          # Vitest unit + component tests
npm run test:watch    # Vitest watch mode
```

## Run it (local dev)

```bash
cd Liquidity-Audit/website
npm install
npm run sync:data   # copy ../data/analysis/ → public/data/analysis/
npm run dev         # http://localhost:5173
```

`sync:data` copies CLI output from `../data/analysis/` into
`public/data/analysis/`. Run it after each local `cli.py` analysis run. The copied
data is gitignored.

Local dev uses `/data/analysis` by default (bundled via `public/`). Optional override:

```bash
VITE_ANALYSIS_DATA_BASE=/custom/path npm run dev
```

## Production (Cloudflare Workers + R2)

Production JSON is served from a **public Cloudflare R2 bucket**, not bundled in
the static site. A GitHub Actions workflow runs `cli.py` every 12 hours and syncs
`data/analysis/` to R2; pushes to **Liquidity-Audit** `master` build and deploy the SPA behind a
**Cloudflare Worker** (static assets + pair-route OG injection).

Worker name: **`crypto-liquidity-audit`** (set in [`wrangler.jsonc`](wrangler.jsonc)).
Production URL: `https://crypto-liquidity-audit.<your-subdomain>.workers.dev`

### Build and deploy

Production builds require `VITE_SITE_URL` (public site origin, no trailing slash),
`VITE_ANALYSIS_DATA_BASE` (public R2 URL, no trailing slash), `VITE_POSTHOG_KEY`, and
`VITE_SENTRY_DSN`:

```bash
cp .env.production.example .env.production
# edit VITE_SITE_URL, VITE_ANALYSIS_DATA_BASE, VITE_POSTHOG_KEY, and VITE_SENTRY_DSN
npm run build
npm run deploy
```

`vite.config.ts` fails the build if any required variable is unset in production mode.
`npm run build` also writes `dist/sitemap.xml` and `dist/robots.txt`.

### SEO and social previews

- **Static shell:** [`index.html`](index.html) ships default description, Open Graph, Twitter Card, and `WebSite` JSON-LD (URLs filled at build from `VITE_SITE_URL`).
- **Client routes:** [`usePageMeta`](src/lib/usePageMeta.ts) updates title, description, canonical, OG/Twitter tags, and per-route JSON-LD (`WebPage`, `BreadcrumbList`, pair reports).
- **Shared pair links:** the Cloudflare Worker ([`worker/index.ts`](worker/index.ts)) injects OG + JSON-LD for `/pairs/*` document requests (`run_worker_first` in [`wrangler.jsonc`](wrangler.jsonc)). Runtime vars `SITE_URL` and `ANALYSIS_DATA_BASE` are set at deploy (same values as the Vite env vars). `SITE_URL` must match the public origin (e.g. `https://crypto-liquidity-audit.octobot.workers.dev`); if unset, the Worker falls back to the request origin.

| Route | JSON-LD |
|-------|---------|
| `/` | `WebSite` + `SearchAction` |
| Static pages | `WebPage` + `BreadcrumbList` |
| `/pairs/:exchange/:slug` | `WebPage` + `BreadcrumbList` (verdict as description) |

Assets: [`public/favicon.svg`](public/favicon.svg), [`public/og-default.png`](public/og-default.png), [`public/site.webmanifest`](public/site.webmanifest).

Pair report OG title and description are derived from analysis JSON (score, grade, failed issues, verdict). The default preview image is `og-default.png`.

Production-like local preview (Wrangler, port 8787):

```bash
npm run preview:worker
```

### R2 CORS (one-time Cloudflare setup)

On the **public analysis bucket**, allow GET/HEAD from your Worker and custom domains:

```json
[
  {
    "AllowedOrigins": [
      "https://crypto-liquidity-audit.<your-subdomain>.workers.dev",
      "https://<your-custom-domain>"
    ],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

Without CORS, browser `fetch()` from the Worker to R2 will fail.

### GitHub secrets (deploy + data refresh)

| Secret | Purpose |
|--------|---------|
| `VITE_SITE_URL` | Public site origin for canonical URLs, OG, sitemap, and Worker vars |
| `VITE_ANALYSIS_DATA_BASE` | Public R2 base URL for JSON |
| `VITE_POSTHOG_KEY` | PostHog EU Cloud project token for production analytics |
| `VITE_SENTRY_DSN` | Sentry DSN for production error reporting |
| `CLOUDFLARE_API_TOKEN` | Worker deploy via Wrangler (Workers Scripts: Edit) |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account |
| `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | Cron upload to R2 |
| `R2_ANALYSIS_BUCKET` / `R2_STATE_BUCKET` | Public + private bucket names |
| `MATTERMOST_WEBHOOK_URL` | Runtime env for `cli.py` Mattermost notifications |

Worker name is configured in `wrangler.jsonc`, not via a GitHub secret.

### Analytics and errors

- **PostHog** (EU Cloud): autocapture, SPA pageviews, pageleave. Ingest `https://eu.i.posthog.com`; set `VITE_POSTHOG_KEY` at build time.
- **Sentry** (DE ingest, errors only): uncaught exceptions and `AppErrorBoundary` reports. Set `VITE_SENTRY_DSN` at build time. No performance tracing or session replay.

Both SDKs no-op during Vitest (`MODE=test`). In production builds, both env vars must be set.

## Routes

| Path | Page |
|------|------|
| `/` | Comparison (home) — rankings, search, exchange filter |
| `/pairs/:exchange/:symbolSlug` | Token report (e.g. `/pairs/mexc/SOL_USDT`) |
| `/methodology` | Metric formulas and scoring |
| `/about` | Principles and contact |
| `/learn` | Glossary |
| `/case-studies` | Before/after narratives |

## File structure

```
wrangler.jsonc          Worker config (static assets, SPA routing)
public/data/analysis/   Local dev JSON only (gitignored)

scripts/                sync-analysis-data.ts

src/
  lib/
    data/               Fetch, adapt, static options, samples
      loader.ts         fetchRankings, fetchPairAnalysis, slug helpers
      adapter.ts        pairAnalysisToToken, rankingsToViewModel
      implementationOptions.ts
      exchanges.ts
      samples.ts        Reference view models (tests/dev only)
    usePageMeta.ts       Document title, description, OG, canonical, JSON-LD
    siteMeta.ts          Shared SEO copy, JSON-LD builders, worker meta injection
    monitoring/          PostHog + Sentry init (env-gated)

  routes/               Route wrappers with loading/error states
  components/           Nav, Footer, Screen, ScoreDial, IssueChips, …
  pages/                One component per screen
  types.ts              TokenViewModel + section interfaces (Layer 3)
  format.ts             fmtUsd / fmtVolShort / …
  theme.ts              Color + font tokens
  router.tsx            Route table + page layout
  main.tsx              BrowserRouter entry
```

## Data flow

**Local dev:**

```
CLI → Liquidity-Audit/data/analysis/
   → npm run sync:data
   → public/data/analysis/
   → fetch (loader.ts)
   → adapter.ts → TokenViewModel / RankingsViewModel
   → pages
```

**Production:**

```
CLI (GH cron) → R2 analysis bucket
Worker SPA → fetch VITE_ANALYSIS_DATA_BASE/rankings|pairs/...
   → adapter.ts → pages
```

See [`../../Projects-Finder/design_specs/03-data-contract.md`](../../Projects-Finder/design_specs/03-data-contract.md) for the full backend →
view-model field mapping.

## Conditional section hiding

`<TokenReport>` omits each detail section when its backing data is empty/null:

| Section | Hidden when |
|---|---|
| Health dashboard | `healthDashboard` empty |
| Peer comparison | `peers` empty |
| Investor simulator | `investorSimulator` empty |
| Lost opportunity | `lostOpportunity` is `null` |
| Root cause | `rootCauses` empty |
| Improvement potential | `improvements` empty |
| Improvement roadmap | `roadmap` empty |
| Implementation options | `implementationOptions` empty |
| Delisting notice + chip | `delistingRisk` empty |

Implementation options appear when `score < 60` or the roadmap is non-empty.
