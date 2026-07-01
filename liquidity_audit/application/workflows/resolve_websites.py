import asyncio
import logging

import liquidity_audit.application.shared.progress as progress
import liquidity_audit.config as app_config
import liquidity_audit.domain.website.website_resolution as website_resolution
import liquidity_audit.infrastructure.ccxt_client as ccxt_client
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.infrastructure.selected_history_store as selected_history_store
import liquidity_audit.infrastructure.website_finder as website_finder

_LOGGER = logging.getLogger(__name__)


async def resolve_websites_for_selection_candidates(
    store: listings_store.ListingsStore,
    config: app_config.AppConfig,
    new_listing_keys: set[tuple[str, str]],
) -> int:
    all_records = store.load_all()
    history_store = selected_history_store.SelectedHistoryStore(
        config.daily_selection.history_csv_path,
    )
    recent_selection_by_key = history_store.load_recent_by_key()
    cooldown_days = config.daily_selection.cooldown_days

    resolution_pool = [
        record for record in all_records.values()
        if website_resolution.should_resolve_website(
            record,
            new_listing_keys,
            recent_selection_by_key,
            cooldown_days,
        )
    ]
    _LOGGER.info(
        "Loaded %s listing(s), %s need CoinGecko website resolution",
        len(all_records),
        len(resolution_pool),
    )
    if not resolution_pool:
        _LOGGER.info("No selection candidates need CoinGecko website resolution")
        return 0

    _LOGGER.info(
        "Resolving websites for %s selection candidate(s) via CoinGecko",
        len(resolution_pool),
    )
    website_finder_instance = website_finder.WebsiteFinder()
    coingecko_client = ccxt_client.create_exchange(
        "coingecko",
        ccxt_options=config.ccxt_options,
        options=config.coingecko_options,
    )
    coingecko_lock = asyncio.Lock()
    updated_records: list = []

    try:
        _LOGGER.info("Loading CoinGecko index for batch website resolution")
        await website_finder_instance.load_coingecko_index(coingecko_client)
        total_to_resolve = len(resolution_pool)
        _LOGGER.info(
            "CoinGecko index loaded, resolving %s listing(s)",
            total_to_resolve,
        )
        for listing_index, listing in enumerate(resolution_pool, start=1):
            if not listing.base:
                base, _quote = listings_store.parse_base_quote_from_symbol(listing.symbol)
                listing.base = base
            async with coingecko_lock:
                resolution = await website_finder_instance.resolve_website(
                    coingecko_client,
                    listing.full_name,
                    listing.base,
                )
            website_resolution.apply_resolution_to_listing(listing, resolution)
            updated_records.append(listing)
            progress.maybe_log_enrichment_progress(
                "CoinGecko website",
                listing_index,
                total_to_resolve,
            )
            _LOGGER.info(
                "Website resolution for %s %s: website=%s status=%s",
                listing.exchange,
                listing.symbol,
                listing.website or "none",
                listing.website_resolution_status or "resolved",
            )
    finally:
        await coingecko_client.close()

    if updated_records:
        _LOGGER.info(
            "Saving %s resolved listing(s) to listings.csv",
            len(updated_records),
        )
        store.append_or_update(updated_records)
    return len(updated_records)


async def run(config: app_config.AppConfig) -> int:
    _LOGGER.info("Updating websites for selection candidates via CoinGecko")
    store = listings_store.ListingsStore(config.listings_csv_path)
    resolved_count = await resolve_websites_for_selection_candidates(
        store,
        config,
        set(),
    )
    _LOGGER.info("Website update complete: %s listing(s) resolved", resolved_count)
    return resolved_count
