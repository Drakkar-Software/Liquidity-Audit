import asyncio
import logging

import liquidity_audit.application.workflows.run_analysis as run_analysis_workflow
import liquidity_audit.domain.website.website_resolution_worker as website_resolution_worker
import liquidity_audit.application.shared.daily_selection as daily_selection_shared
import liquidity_audit.application.shared.exchange_processor as exchange_processor
import liquidity_audit.application.shared.logging_summaries as logging_summaries
import liquidity_audit.config as app_config
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.domain.models as models

_LOGGER = logging.getLogger(__name__)


async def run(
    config: app_config.AppConfig,
    identify_only: bool = False,
) -> models.DailyRunResult | None:
    _LOGGER.info("Starting liquidity audit sync run")
    if identify_only:
        _LOGGER.info("Identify-only mode: skipping analysis and selection steps")
    store = listings_store.ListingsStore(config.listings_csv_path)
    known_keys = store.load_known_keys()
    _LOGGER.info("Loaded %s known listing(s) from CSV", len(known_keys))

    known_keys_snapshot = set(known_keys)
    exchange_results = await asyncio.gather(
        *[
            exchange_processor.process_exchange(
                exchange_name,
                known_keys_snapshot,
                config,
                identify_only,
            )
            for exchange_name in config.exchanges
        ]
    )

    new_listings: list[models.ListingRecord] = []
    all_failed_enrichments: list[models.FailedListingEnrichment] = []
    for exchange_new_listings, failed_enrichments in exchange_results:
        new_listings.extend(exchange_new_listings)
        all_failed_enrichments.extend(failed_enrichments)

    if new_listings:
        store.append_or_update(new_listings)
        _LOGGER.info("Saved %s new listing(s)", len(new_listings))
    else:
        _LOGGER.info("No new listings to save")

    daily_selections: list[models.DailyProjectSelection] = []
    run_summary: models.RunSummary | None = None

    if not identify_only:
        new_listing_keys = {listing.key() for listing in new_listings}
        listings_csv_lock = asyncio.Lock()
        website_worker = await website_resolution_worker.WebsiteResolutionWorker.create_and_start(
            store,
            config,
            new_listing_keys,
            listings_csv_lock,
        )
        for listing in new_listings:
            website_worker.try_enqueue(listing)
        try:
            await run_analysis_workflow.run(
                config,
                website_worker=website_worker,
                listings_csv_lock=listings_csv_lock,
            )
        finally:
            websites_resolved_count = await website_worker.shutdown()
        new_low_health_listings = daily_selection_shared.new_low_health_listings_from_store(
            store,
            new_listing_keys,
        )
        daily_selections = daily_selection_shared.select_and_record_daily_selections(
            store,
            config,
            new_listing_keys,
        )
        selections_proposed_new = sum(
            1 for selection in daily_selections if selection.is_new_listing
        )
        run_summary = models.RunSummary(
            new_listings_total=len(new_listings),
            new_low_health_count=len(new_low_health_listings),
            selections_proposed_total=len(daily_selections),
            selections_proposed_new=selections_proposed_new,
            selections_proposed_existing=len(daily_selections) - selections_proposed_new,
            failed_enrichments_count=len(all_failed_enrichments),
            websites_resolved_count=websites_resolved_count,
        )
        logging_summaries.log_daily_selections_summary(
            daily_selections,
            config.daily_selection.max_per_day,
        )

    if all_failed_enrichments:
        _LOGGER.error(
            "Failed to register %s listing(s) across all exchanges",
            len(all_failed_enrichments),
        )
        logging_summaries.log_failed_enrichments(all_failed_enrichments)

    logging_summaries.log_new_listings_run_summary(new_listings, all_failed_enrichments)

    _LOGGER.info(
        "Run complete: %s new listing(s), %s failed registration(s)",
        len(new_listings),
        len(all_failed_enrichments),
    )

    if identify_only or run_summary is None:
        return None

    return models.DailyRunResult(
        run_summary=run_summary,
        daily_selections=daily_selections,
        new_listings=new_listings,
        failed_enrichments=all_failed_enrichments,
    )
