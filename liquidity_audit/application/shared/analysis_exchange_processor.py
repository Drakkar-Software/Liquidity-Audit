import asyncio
import logging
import typing

import ccxt

import liquidity_audit.application.shared.delisted_listing as delisted_listing
import liquidity_audit.application.shared.fetch_pair_metrics as fetch_pair_metrics
import liquidity_audit.application.shared.time_utils as time_utils
import liquidity_audit.domain.website.website_resolution_worker as website_resolution_worker
import liquidity_audit.domain.analysis.listing_sync as listing_sync
import liquidity_audit.domain.analysis.pair_analysis as pair_analysis
import liquidity_audit.infrastructure.analysis_store as analysis_store
import liquidity_audit.infrastructure.ccxt_client as ccxt_client
import liquidity_audit.config as app_config
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.domain.models as models

_LOGGER = logging.getLogger(__name__)


async def process_exchange(
    exchange_name: str,
    listings: list[models.ListingRecord],
    config: app_config.AppConfig,
    store: analysis_store.AnalysisStore,
    listings_store_instance: listings_store.ListingsStore,
    listings_csv_lock: asyncio.Lock,
    run_started_at: str,
    *,
    website_worker: typing.Optional[website_resolution_worker.WebsiteResolutionWorker] = None,
) -> tuple[
    list[pair_analysis.ExtendedRawMetrics],
    list[dict[str, str]],
    dict[str, dict[str, typing.Any]],
    int,
    int,
]:
    raw_metrics_by_symbol: dict[str, pair_analysis.ExtendedRawMetrics] = {}
    delisting_risk_by_symbol: dict[str, list[str]] = {}
    band_depth_by_symbol: dict[str, typing.Optional[float]] = {}
    pair_analysis_by_symbol: dict[str, dict[str, typing.Any]] = {}
    failures: list[dict[str, str]] = []
    skipped_delisted = 0
    newly_delisted = 0
    pairs_since_checkpoint = 0

    candidates = [
        listing
        for listing in listings
        if listing.exchange == exchange_name
    ]
    if not candidates:
        _LOGGER.info("No listings for exchange %s", exchange_name)
        return [], failures, pair_analysis_by_symbol, newly_delisted, skipped_delisted

    to_analyze = []
    for listing in candidates:
        if listing.delisted_at:
            if delisted_listing.is_within_delisted_retention(
                listing.delisted_at,
                config.analysis.delisted_retention_days,
            ):
                skipped_delisted += 1
            else:
                store.delete_pair_analysis(exchange_name, listing.symbol)
                skipped_delisted += 1
            continue
        to_analyze.append(listing)

    _LOGGER.info(
        "%s: %s to analyze, %s skipped (delisted)",
        exchange_name,
        len(to_analyze),
        skipped_delisted,
    )

    async def checkpoint_save() -> None:
        updated_listings = []
        universe = list(raw_metrics_by_symbol.values())
        for listing in candidates:
            raw_metrics = raw_metrics_by_symbol.get(listing.symbol)
            if raw_metrics is None:
                if listing.delisted_at:
                    updated_listings.append(listing)
                continue
            json_path = store.pair_json_relative_path(exchange_name, listing.symbol)
            score_100, _, _ = pair_analysis.compute_score_100(raw_metrics, universe)
            listing_sync.apply_analysis_scalars_to_listing(
                listing,
                raw_metrics,
                json_path,
                run_started_at,
                delisting_risk_by_symbol.get(listing.symbol),
                score_100=score_100,
            )
            updated_listings.append(listing)
        if updated_listings:
            async with listings_csv_lock:
                listings_store_instance.append_or_update(updated_listings)

    async with ccxt_client.exchange_client(
        exchange_name,
        ccxt_options=config.ccxt_options,
    ) as exchange_client:
        for listing in to_analyze:
            try:
                fetched_at = time_utils.utc_now_iso()
                raw_metrics, delisting_risk_labels, band_depth_quote = (
                    await fetch_pair_metrics.fetch_pair_raw_metrics(
                        exchange_client,
                        listing,
                        config,
                        fetched_at,
                    )
                )
                if delisted_listing.clear_delisted_if_relisted(listing):
                    _LOGGER.info("Relisted %s %s", exchange_name, listing.symbol)
                raw_metrics_by_symbol[listing.symbol] = raw_metrics
                delisting_risk_by_symbol[listing.symbol] = delisting_risk_labels
                band_depth_by_symbol[listing.symbol] = band_depth_quote
                json_path = store.pair_json_relative_path(exchange_name, listing.symbol)
                listing_sync.apply_analysis_scalars_to_listing(
                    listing,
                    raw_metrics,
                    json_path,
                    run_started_at,
                    delisting_risk_labels,
                    score_100=round(raw_metrics.liquidity_score * 100),
                )
                if website_worker is not None:
                    website_worker.try_enqueue(listing)
                pairs_since_checkpoint += 1
                if pairs_since_checkpoint >= config.analysis.checkpoint_every_n_pairs:
                    await checkpoint_save()
                    pairs_since_checkpoint = 0
            except ccxt.BadSymbol as error:
                if delisted_listing.mark_delisted(listing, time_utils.utc_now_iso()):
                    newly_delisted += 1
                    _LOGGER.warning(
                        "Delisted %s %s: %s",
                        exchange_name,
                        listing.symbol,
                        error,
                    )
            except Exception:
                _LOGGER.exception(
                    "Failed to analyze %s %s",
                    exchange_name,
                    listing.symbol,
                )
                failures.append({
                    "exchange": exchange_name,
                    "symbol": listing.symbol,
                    "error": "analysis failed",
                })

    universe = list(raw_metrics_by_symbol.values())
    exchange_averages = pair_analysis.compute_exchange_averages(
        universe,
        config.analysis.rankings_min_volume_quote,
    )
    for listing in candidates:
        raw_metrics = raw_metrics_by_symbol.get(listing.symbol)
        if raw_metrics is None:
            continue
        delisting_risk_labels = delisting_risk_by_symbol.get(listing.symbol, [])
        delisting_risk_cards = fetch_pair_metrics.build_delisting_risk_cards_for_listing(
            listing,
            raw_metrics,
            delisting_risk_labels,
            config,
            band_depth_by_symbol.get(listing.symbol),
        )
        pair_analysis_payload = pair_analysis.build_pair_analysis(
            raw_metrics,
            universe,
            exchange_averages,
            config.health_labels,
            delisting_risk_cards=delisting_risk_cards,
        )
        pair_analysis_by_symbol[listing.symbol] = pair_analysis_payload
        store.save_pair_analysis(exchange_name, listing.symbol, pair_analysis_payload)
        json_path = store.pair_json_relative_path(exchange_name, listing.symbol)
        listing_sync.apply_analysis_scalars_to_listing(
            listing,
            raw_metrics,
            json_path,
            run_started_at,
            delisting_risk_labels,
            score_100=pair_analysis_payload["analysis"]["score_100"],
        )

    rankings = pair_analysis.build_rankings(
        universe,
        config.analysis.rankings_min_volume_quote,
    )
    store.save_exchange_rankings(exchange_name, {
        "exchange": exchange_name,
        "updated_at": time_utils.utc_now_iso(),
        "pairs": rankings,
    })

    async with listings_csv_lock:
        listings_store_instance.append_or_update(candidates)
    return universe, failures, pair_analysis_by_symbol, newly_delisted, skipped_delisted
