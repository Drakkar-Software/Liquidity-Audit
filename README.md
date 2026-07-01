# liquidity-audit

Public Python library for syncing exchange listing state to CSV and analysis JSON.

## Install

```powershell
pip install -e .
```

From the private [Projects-Finder](https://github.com/) app:

```text
-e ../Liquidity-Audit
```

## CLI

Copy `config.example.json` to `config.json`. Copy `.env.template` to `.env` and set `MATTERMOST_WEBHOOK_URL` (required for `cli.py run`). The CLI loads `.env` on startup; shell exports take precedence over file values.

```powershell
python cli.py --config config.json run
```

Posts a Mattermost summary after a full run: run stats plus each daily selected pair (exchange, symbol, health). `run --identify-only` skips Mattermost. `identify-selected-only` logs the payload without posting.

Other commands: `re-evaluate-data`, `identify-selected-only`.

## Package

Import from `liquidity_audit`:

- `liquidity_audit.config.load_config` — sync configuration
- `liquidity_audit.application.workflows.daily_run` — discovery, analysis, selection
- `liquidity_audit.infrastructure.listings_store` — `listings.csv`
- `liquidity_audit.infrastructure.selected_history_store` — `selected_history.csv`
- `liquidity_audit.infrastructure.analysis_store` — per-pair JSON
- `liquidity_audit.infrastructure.mattermost_notifier` — sync run Mattermost payloads

## State files

### `listings.csv` (29 columns)

`exchange`, `symbol`, `full_name`, health metrics, analysis scalars, timestamps, `delisted_at`.

No `website`, `coingecko_id`, or email columns.

### `selected_history.csv`

Daily project selection audit trail. Column `selected_at` (formerly `contacted_at`).

## Tests

```powershell
$env:PYTHONPATH="..\ccxt\python"
..\OctoBot\venv13\Scripts\python.exe -m pytest tests/ -q
```

Run from this directory (`Liquidity-Audit/`).

## CI

[`.github/workflows/update-analysis-data.yml`](.github/workflows/update-analysis-data.yml) runs on `workflow_dispatch` (optional cron commented in file):

1. `pip install -r requirements.txt` (`octobot-ccxt` from PyPI)
2. Restore `listings.csv` and `selected_history.csv` from R2 state bucket
3. `python cli.py --config config.json run` (posts Mattermost summary)
4. Upload `data/analysis/*.json` to R2 analysis bucket and state CSVs to R2 state bucket

Required GitHub secrets: `CLOUDFLARE_ACCOUNT_ID`, `R2_ANALYSIS_BUCKET`, `R2_STATE_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `MATTERMOST_WEBHOOK_URL`.

No dependency on the private Projects-Finder repo.
