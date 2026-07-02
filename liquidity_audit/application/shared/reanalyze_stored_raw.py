import logging

import liquidity_audit.application.shared.delisted_listing as delisted_listing
import liquidity_audit.application.shared.time_utils as time_utils
import liquidity_audit.domain.analysis.delisting_risk as delisting_risk
import liquidity_audit.domain.analysis.listing_sync as listing_sync
import liquidity_audit.domain.analysis.pair_analysis as pair_analysis
import liquidity_audit.infrastructure.analysis_store as analysis_store
import liquidity_audit.config as app_config
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.domain.models as models

_LOGGER = logging.getLogger(__name__)


async def reanalyze_from_stored_raw(
    config: app_config.AppConfig,
) -> tuple[set[tuple[str, str]], dict[str, int]]:
    run_started_at = time_utils.utc_now_iso()
    _LOGGER.info("Reanalyzing stored raw metrics (no exchange fetch)")

    listings_store_instance = listings_store.ListingsStore(config.listings_csv_path)
    all_listings = list(listings_store_instance.load_all().values())
    configured_exchanges = set(config.exchanges)
    listings = [
        listing for listing in all_listings if listing.exchange in configured_exchanges
    ]

    store = analysis_store.AnalysisStore(config.analysis.output_dir)
    reanalyzed_keys: set[tuple[str, str]] = set()
    pairs_reanalyzed = 0
    pairs_skipped_no_json = 0
    pairs_skipped_delisted = 0
    updated_listings: list[models.ListingRecord] = []

    for exchange_name in config.exchanges:
        candidates = [
            listing
            for listing in listings
            if listing.exchange == exchange_name
        ]
        if not candidates:
            continue

        raw_metrics_by_symbol: dict[str, pair_analysis.ExtendedRawMetrics] = {}
        for listing in candidates:
            if listing.delisted_at:
                if delisted_listing.is_within_delisted_retention(
                    listing.delisted_at,
                    config.analysis.delisted_retention_days,
                ):
                    pairs_skipped_delisted += 1
                    continue
                store.delete_pair_analysis(exchange_name, listing.symbol)
                pairs_skipped_delisted += 1
                continue

            existing = store.load_pair_analysis(exchange_name, listing.symbol)
            if existing is None or "raw" not in existing:
                pairs_skipped_no_json += 1
                continue

            raw_metrics_by_symbol[listing.symbol] = pair_analysis.ExtendedRawMetrics(
                **existing["raw"],
            )

        universe = list(raw_metrics_by_symbol.values())
        if not universe:
            _LOGGER.info("%s: no stored raw metrics to reanalyze", exchange_name)
            continue

        exchange_averages = pair_analysis.compute_exchange_averages(
            universe,
            config.analysis.rankings_min_volume_quote,
        )
        for listing in candidates:
            raw_metrics = raw_metrics_by_symbol.get(listing.symbol)
            if raw_metrics is None:
                continue
            thresholds = config.delisting_risk.thresholds_for(listing.exchange)
            band_depth_quote = delisting_risk.resolve_band_depth_quote_for_threshold(
                raw_metrics,
                thresholds.depth_band_pct,
            )
            delisting_risk_labels = delisting_risk.evaluate_delisting_risk_from_stored(
                raw_metrics.volume_quote,
                band_depth_quote,
                thresholds,
            )
            delisting_risk_cards = delisting_risk.build_delisting_risk_cards(
                delisting_risk_labels,
                raw_metrics.volume_quote,
                band_depth_quote,
                thresholds,
            )
            pair_analysis_payload = pair_analysis.build_pair_analysis(
                raw_metrics,
                universe,
                exchange_averages,
                config.health_labels,
                delisting_risk_cards=delisting_risk_cards,
            )
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
            updated_listings.append(listing)
            reanalyzed_keys.add((exchange_name, listing.symbol))
            pairs_reanalyzed += 1

        rankings = pair_analysis.build_rankings(
            universe,
            config.analysis.rankings_min_volume_quote,
        )
        store.save_exchange_rankings(exchange_name, {
            "exchange": exchange_name,
            "updated_at": time_utils.utc_now_iso(),
            "rankings_min_volume_quote": config.analysis.rankings_min_volume_quote,
            "pairs": rankings,
        })
        _LOGGER.info(
            "%s: reanalyzed %s pair(s) from stored raw",
            exchange_name,
            len(universe),
        )

    if updated_listings:
        listings_store_instance.append_or_update(updated_listings)

    stats = {
        "pairs_reanalyzed": pairs_reanalyzed,
        "pairs_skipped_no_json": pairs_skipped_no_json,
        "pairs_skipped_delisted": pairs_skipped_delisted,
        "run_started_at": run_started_at,
    }
    _LOGGER.info(
        "Reanalyze from stored raw complete: %s pair(s) updated, "
        "%s skipped (no JSON), %s skipped (delisted)",
        pairs_reanalyzed,
        pairs_skipped_no_json,
        pairs_skipped_delisted,
    )
    return reanalyzed_keys, stats
