# liquidity-audit

Python package and CLI for syncing exchange listing liquidity data to CSV and analysis JSON.

Requires Python 3.13+.

## Install

```sh
pip install --prefer-binary -r requirements.txt
pip install -e .
```

For tests (includes `mock`):

```sh
pip install -r dev_requirements.txt
```

## CLI

Copy `config.example.json` to `config.json`.

```sh
python cli.py --config config.json run
```

### Commands

| Command | Description |
|---------|-------------|
| `run` | Full pipeline: discover listings and analyze health |
| `run --identify-only` | Discover and save new listings only; skips analysis |
| `re-evaluate-data` | Refresh health metrics from CSV and rebuild analysis JSON from cached raw blocks |

## Package

Import from `liquidity_audit`:

- `liquidity_audit.config.load_config` — configuration
- `liquidity_audit.application.workflows.daily_run` — discovery and analysis
- `liquidity_audit.infrastructure.listings_store` — `listings.csv`
- `liquidity_audit.infrastructure.analysis_store` — per-pair JSON under `data/analysis/`

## State files

Default paths are under `data/` (see `config.example.json`).

### `listings.csv`

One row per exchange listing. Columns (see `liquidity_audit.infrastructure.listings_store.CSV_COLUMNS`):

- **Identity:** `exchange`, `symbol`, `full_name`
- **Health:** `bid_levels`, `ask_levels`, depth/spread/volume fields, `liquidity_score`, `is_low_health`, `health_label_primary`, `health_labels_other`, `delisting_risk`
- **Analysis scalars:** `score_100`, `spread_pct`, `depth_2pct_quote`, `bid_volume_quote`, `ask_volume_quote`, `max_fillable_buy_quote`, `slippage_10k_pct`, `analysis_json_path`
- **Timestamps:** `first_seen_at`, `last_checked_at`, `last_analyzed_at`, `delisted_at`

### `data/analysis/`

- `manifest.json` — run metadata
- `rankings/{exchange}.json` — per-exchange rankings
- `pairs/{exchange}/{BASE}_{QUOTE}.json` — per-pair analysis payloads

## Website

Public Crypto Liquidity Audit SPA (React + TypeScript). See [`website/README.md`](website/README.md) for full docs.

```sh
cd website
npm install
npm run sync:data   # copy ../data/analysis/ → public/data/analysis/
npm run dev         # http://localhost:5173
```

## Tests

```sh
pip install --prefer-binary -r requirements.txt -r dev_requirements.txt
pip install -e .
python -m pytest tests/ -v
```

Scoring benchmark golden files: set `UPDATE_SCORING_GOLDEN=1` to regenerate; those tests are skipped by default.

## CI

[`.github/workflows/tests.yml`](.github/workflows/tests.yml) runs on push to `master` and on pull requests:

1. **Python tests:** `pip install -r requirements.txt -r dev_requirements.txt`, `pip install -e .`, `python -m pytest tests/ -v`
2. **Website tests:** `npm ci`, `npm run test`, production `npm run build` in `website/`
3. **Deploy website** (push to `master` only): build and deploy `website/` to Cloudflare Workers via Wrangler

[`.github/workflows/update-analysis-data.yml`](.github/workflows/update-analysis-data.yml) runs on `workflow_dispatch` (optional cron commented in file):

1. `pip install -r requirements.txt`
2. Restore `listings.csv` from R2 state bucket
3. `python cli.py --config config.json run`
4. Upload `data/analysis/*.json` to R2 analysis bucket and `listings.csv` to R2 state bucket

Required GitHub secrets: `CLOUDFLARE_ACCOUNT_ID`, `R2_ANALYSIS_BUCKET`, `R2_STATE_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`.
