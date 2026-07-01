import typing

import liquidity_audit.config as app_config
import liquidity_audit.domain.analysis.delisting_risk as delisting_risk
import liquidity_audit.domain.analysis.pair_analysis as pair_analysis
import liquidity_audit.domain.health.evaluation as health_evaluation
import liquidity_audit.domain.models as models


async def fetch_pair_raw_metrics(
    exchange_client,
    listing: models.ListingRecord,
    config: app_config.AppConfig,
    fetched_at: str,
) -> tuple[pair_analysis.ExtendedRawMetrics, list[str], typing.Optional[float]]:
    order_book = await exchange_client.fetch_order_book(
        listing.symbol,
        limit=config.order_book_limit,
    )
    ticker = await exchange_client.fetch_ticker(listing.symbol)
    health = health_evaluation.evaluate_health(
        order_book,
        ticker,
        config.health_rules,
        config.unhealthy_values,
        config.health_labels,
        config.min_liquidity_score,
        config.order_book_limit,
    )
    thresholds = config.delisting_risk.thresholds_for(listing.exchange)
    delisting_risk_labels, band_depth_quote = delisting_risk.evaluate_delisting_risk_with_metrics(
        health.volume_quote,
        order_book,
        ticker,
        thresholds,
    )
    raw_metrics = pair_analysis.build_extended_raw_metrics(
        listing.exchange,
        listing.symbol,
        listing.full_name,
        order_book,
        ticker,
        health,
        fetched_at,
    )
    return raw_metrics, delisting_risk_labels, band_depth_quote


def build_delisting_risk_cards_for_listing(
    listing: models.ListingRecord,
    raw_metrics: pair_analysis.ExtendedRawMetrics,
    delisting_risk_labels: list[str],
    config: app_config.AppConfig,
    band_depth_quote: typing.Optional[float] = None,
) -> list[dict[str, str]]:
    thresholds = config.delisting_risk.thresholds_for(listing.exchange)
    if band_depth_quote is None:
        band_depth_quote = delisting_risk.resolve_band_depth_quote_for_threshold(
            raw_metrics,
            thresholds.depth_band_pct,
        )
    return delisting_risk.build_delisting_risk_cards(
        delisting_risk_labels,
        raw_metrics.volume_quote,
        band_depth_quote,
        thresholds,
    )
