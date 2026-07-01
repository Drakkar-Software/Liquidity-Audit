import typing

import liquidity_audit.domain.analysis.pair_analysis as pair_analysis
import liquidity_audit.domain.models as models


def apply_analysis_scalars_to_listing(
    listing: models.ListingRecord,
    raw_metrics: pair_analysis.ExtendedRawMetrics,
    analysis_json_path: str,
    analyzed_at: str,
    delisting_risk_labels: typing.Optional[list[str]] = None,
    score_100: typing.Optional[int] = None,
) -> None:
    listing.bid_levels = raw_metrics.bid_levels
    listing.ask_levels = raw_metrics.ask_levels
    listing.bid_depth_quote = raw_metrics.bid_depth_1pct_quote
    listing.ask_depth_quote = raw_metrics.ask_depth_1pct_quote
    listing.bid_larger_depth_quote = raw_metrics.bid_larger_depth_quote
    listing.ask_larger_depth_quote = raw_metrics.ask_larger_depth_quote
    listing.bid_total_depth_quote = None
    listing.ask_total_depth_quote = None
    listing.volume_quote = raw_metrics.volume_quote
    listing.bid_ask_spread_ratio = (
        raw_metrics.spread_pct / 100 if raw_metrics.spread_pct is not None else None
    )
    listing.liquidity_score = raw_metrics.liquidity_score
    listing.is_low_health = raw_metrics.is_low_health
    listing.health_label_primary = raw_metrics.health_label_primary or None
    listing.health_labels_other = raw_metrics.health_labels_other or None
    listing.last_analyzed_at = analyzed_at
    listing.last_checked_at = analyzed_at
    listing.score_100 = (
        score_100
        if score_100 is not None
        else round(raw_metrics.liquidity_score * 100)
    )
    listing.spread_pct = raw_metrics.spread_pct
    listing.depth_2pct_quote = raw_metrics.depth_2pct_quote
    listing.bid_volume_quote = raw_metrics.bid_volume_quote
    listing.ask_volume_quote = raw_metrics.ask_volume_quote
    listing.max_fillable_buy_quote = raw_metrics.max_fillable_buy_quote
    listing.slippage_10k_pct = pair_analysis.resolve_slippage_display(raw_metrics.slippage)[1]
    listing.analysis_json_path = analysis_json_path
    if delisting_risk_labels is not None:
        listing.delisting_risk = delisting_risk_labels
