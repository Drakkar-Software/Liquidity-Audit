import asyncio
import logging
import typing

import liquidity_audit.application.shared.analysis_exchange_processor as analysis_exchange_processor
import liquidity_audit.application.shared.time_utils as time_utils
import liquidity_audit.domain.website.website_resolution_worker as website_resolution_worker
import liquidity_audit.infrastructure.analysis_store as analysis_store
import liquidity_audit.config as app_config
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.infrastructure.market_cap_fetch as market_cap_fetch

_LOGGER = logging.getLogger(__name__)


async def run(
    config: app_config.AppConfig,
    *,
    website_worker: typing.Optional[website_resolution_worker.WebsiteResolutionWorker] = None,
    listings_csv_lock: typing.Optional[asyncio.Lock] = None,
) -> None:
    run_started_at = time_utils.utc_now_iso()
    _LOGGER.info("Starting analysis run")

    listings_store_instance = listings_store.ListingsStore(config.listings_csv_path)
    all_listings = list(listings_store_instance.load_all().values())
    configured_exchanges = set(config.exchanges)
    listings = [
        listing for listing in all_listings if listing.exchange in configured_exchanges
    ]
    _LOGGER.info("Loaded %s listing(s) for analysis", len(listings))

    store = analysis_store.AnalysisStore(config.analysis.output_dir)
    if listings_csv_lock is None:
        listings_csv_lock = asyncio.Lock()
    all_failures: list[dict[str, str]] = []
    total_analyzed = 0
    total_newly_delisted = 0
    total_skipped_delisted = 0

    market_cap_task = asyncio.create_task(
        market_cap_fetch.fetch_market_cap_by_symbol_for_listings(config, listings),
    )
    try:
        exchange_results = await asyncio.gather(
            *[
                analysis_exchange_processor.process_exchange(
                    exchange_name,
                    listings,
                    config,
                    store,
                    listings_store_instance,
                    listings_csv_lock,
                    run_started_at,
                    website_worker=website_worker,
                    market_cap_task=market_cap_task,
                )
                for exchange_name in config.exchanges
            ]
        )
    finally:
        await market_cap_task
    for (
        universe,
        failures,
        _pair_analyses,
        newly_delisted,
        skipped_delisted,
    ) in exchange_results:
        all_failures.extend(failures)
        total_analyzed += len(universe)
        total_newly_delisted += newly_delisted
        total_skipped_delisted += skipped_delisted

    store.save_manifest({
        "run_started_at": run_started_at,
        "run_completed_at": time_utils.utc_now_iso(),
        "exchanges": list(config.exchanges),
        "pairs_analyzed": total_analyzed,
        "pairs_delisted": total_newly_delisted,
        "pairs_delisted_skipped": total_skipped_delisted,
        "pairs_failed": all_failures,
    })
    _LOGGER.info(
        "Analysis complete: %s pair(s) in universe, "
        "%s newly delisted, %s delisted skipped, %s failed",
        total_analyzed,
        total_newly_delisted,
        total_skipped_delisted,
        len(all_failures),
    )
