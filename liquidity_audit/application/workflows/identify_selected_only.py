import logging

import liquidity_audit.application.shared.daily_selection as daily_selection_shared
import liquidity_audit.application.shared.logging_summaries as logging_summaries
import liquidity_audit.config as app_config
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.domain.models as models

_LOGGER = logging.getLogger(__name__)


async def run(config: app_config.AppConfig) -> models.DailyRunResult:
    _LOGGER.info(
        "Identify-selected-only mode: selecting projects from CSV without network",
    )
    store = listings_store.ListingsStore(config.listings_csv_path)
    if not store.load_all():
        _LOGGER.info("No listings in CSV for project selection")
        return models.DailyRunResult(
            run_summary=models.RunSummary(
                new_listings_total=0,
                new_low_health_count=0,
                selections_proposed_total=0,
                selections_proposed_new=0,
                selections_proposed_existing=0,
                failed_enrichments_count=0,
            ),
            daily_selections=[],
            new_listings=[],
            failed_enrichments=[],
        )

    daily_selections = daily_selection_shared.select_and_record_daily_selections(
        store,
        config,
        set(),
    )
    run_summary = models.RunSummary(
        new_listings_total=0,
        new_low_health_count=0,
        selections_proposed_total=len(daily_selections),
        selections_proposed_new=0,
        selections_proposed_existing=len(daily_selections),
        failed_enrichments_count=0,
    )
    logging_summaries.log_daily_selections_summary(
        daily_selections,
        config.daily_selection.max_per_day,
    )
    _LOGGER.info(
        "Identify-selected-only complete: %s project(s) recorded",
        len(daily_selections),
    )
    return models.DailyRunResult(
        run_summary=run_summary,
        daily_selections=daily_selections,
        new_listings=[],
        failed_enrichments=[],
    )
