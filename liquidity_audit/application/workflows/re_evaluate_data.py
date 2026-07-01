import logging

import liquidity_audit.application.shared.reanalyze_stored_raw as reanalyze_stored_raw
import liquidity_audit.infrastructure.analysis_store as analysis_store
import liquidity_audit.application.shared.time_utils as time_utils
import liquidity_audit.config as app_config
import liquidity_audit.domain.analysis.delisting_risk as delisting_risk
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.domain.health.evaluation as health_evaluation

_LOGGER = logging.getLogger(__name__)


async def run(config: app_config.AppConfig) -> None:
    run_started_at = time_utils.utc_now_iso()
    _LOGGER.info("Re-evaluating stored listing health metrics from CSV")

    reanalyzed_keys, reanalyze_stats = await reanalyze_stored_raw.reanalyze_from_stored_raw(config)

    store = listings_store.ListingsStore(config.listings_csv_path)
    records = store.load_all()
    if not records and not reanalyzed_keys:
        _LOGGER.info("No listings in CSV to re-evaluate")
        return

    now = time_utils.utc_now_iso()
    updated_records = []

    for record in records.values():
        if record.key() in reanalyzed_keys:
            continue

        health = health_evaluation.evaluate_health_from_stored_metrics(
            record.bid_levels,
            record.ask_levels,
            record.bid_depth_quote,
            record.ask_depth_quote,
            record.bid_larger_depth_quote,
            record.ask_larger_depth_quote,
            record.bid_total_depth_quote,
            record.ask_total_depth_quote,
            record.volume_quote,
            record.bid_ask_spread_ratio,
            config.health_rules,
            config.unhealthy_values,
            config.health_labels,
            config.min_liquidity_score,
            config.order_book_limit,
        )
        record.is_low_health = health.is_low_health
        record.liquidity_score = health.liquidity_score
        record.health_label_primary = health.health_label_primary or None
        record.health_labels_other = health.health_labels_other or None
        record.last_checked_at = now

        thresholds = config.delisting_risk.thresholds_for(record.exchange)
        band_depth_quote = delisting_risk.resolve_band_depth_quote_for_listing(
            record,
            thresholds.depth_band_pct,
        )
        record.delisting_risk = delisting_risk.evaluate_delisting_risk_from_stored(
            record.volume_quote,
            band_depth_quote,
            thresholds,
        )
        updated_records.append(record)

    if updated_records:
        store.append_or_update(updated_records)

    low_health_count = sum(
        1 for record in records.values() if record.is_low_health
    )

    analysis_store.AnalysisStore(config.analysis.output_dir).save_manifest({
        "mode": "re_evaluate_data",
        "run_started_at": reanalyze_stats.get("run_started_at", run_started_at),
        "run_completed_at": time_utils.utc_now_iso(),
        "exchanges": list(config.exchanges),
        "pairs_reanalyzed": reanalyze_stats.get("pairs_reanalyzed", 0),
        "pairs_skipped_no_json": reanalyze_stats.get("pairs_skipped_no_json", 0),
        "pairs_skipped_delisted": reanalyze_stats.get("pairs_skipped_delisted", 0),
        "csv_only_updated": len(updated_records),
        "low_health_count": low_health_count,
    })
    _LOGGER.info(
        "Re-evaluation complete: %s reanalyzed from JSON, %s CSV-only update(s), %s low-health",
        reanalyze_stats.get("pairs_reanalyzed", 0),
        len(updated_records),
        low_health_count,
    )
