import logging
import typing

import liquidity_audit.config as app_config
import liquidity_audit.domain.health.order_book as health_order_book
import liquidity_audit.domain.models as models

_LOGGER = logging.getLogger(__name__)

LABEL_LOW_DEPTH = "low depth"
LABEL_LOW_VOLUME = "low volume"


def _format_usd_short(value: float) -> str:
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1000:
        return f"${value / 1000:.1f}k"
    return f"${value:.0f}"


def compute_band_depth_quote(
    order_book: dict,
    ticker: dict,
    depth_band_pct: float,
) -> typing.Optional[float]:
    sorted_bids_list = health_order_book.sorted_bids(order_book.get("bids", []))
    sorted_asks_list = health_order_book.sorted_asks(order_book.get("asks", []))
    mid_price = health_order_book.compute_mid_price(sorted_bids_list, sorted_asks_list, ticker)
    if mid_price is None:
        return None

    bid_depth_quote = health_order_book.compute_band_depth_quote(
        sorted_bids_list,
        mid_price,
        depth_band_pct,
        True,
    )
    ask_depth_quote = health_order_book.compute_band_depth_quote(
        sorted_asks_list,
        mid_price,
        depth_band_pct,
        False,
    )
    return bid_depth_quote + ask_depth_quote


def evaluate_delisting_risk_from_stored(
    volume_quote: typing.Optional[float],
    band_depth_quote: typing.Optional[float],
    thresholds: app_config.DelistingRiskExchangeThresholds,
) -> list[str]:
    labels: list[str] = []

    if band_depth_quote is None:
        _LOGGER.warning(
            "Cannot evaluate delisting depth: band depth unavailable for stored metrics",
        )
    elif band_depth_quote < thresholds.min_depth_quote_usdt:
        labels.append(LABEL_LOW_DEPTH)

    if volume_quote is None or volume_quote < thresholds.min_volume_quote_usdt:
        labels.append(LABEL_LOW_VOLUME)

    return labels


def evaluate_delisting_risk(
    volume_quote: typing.Optional[float],
    order_book: dict,
    ticker: dict,
    thresholds: app_config.DelistingRiskExchangeThresholds,
) -> list[str]:
    band_depth_quote = compute_band_depth_quote(
        order_book,
        ticker,
        thresholds.depth_band_pct,
    )
    if band_depth_quote is None:
        _LOGGER.warning(
            "Cannot compute delisting depth: missing mid price or empty order book",
        )
    return evaluate_delisting_risk_from_stored(
        volume_quote,
        band_depth_quote,
        thresholds,
    )


def evaluate_delisting_risk_with_metrics(
    volume_quote: typing.Optional[float],
    order_book: dict,
    ticker: dict,
    thresholds: app_config.DelistingRiskExchangeThresholds,
) -> tuple[list[str], typing.Optional[float]]:
    band_depth_quote = compute_band_depth_quote(
        order_book,
        ticker,
        thresholds.depth_band_pct,
    )
    labels = evaluate_delisting_risk_from_stored(
        volume_quote,
        band_depth_quote,
        thresholds,
    )
    return labels, band_depth_quote


def resolve_band_depth_quote_for_threshold(
    raw_metrics: typing.Any,
    depth_band_pct: float,
) -> typing.Optional[float]:
    if hasattr(raw_metrics, "depth_1pct_quote"):
        depth_1pct_quote = raw_metrics.depth_1pct_quote
        depth_2pct_quote = raw_metrics.depth_2pct_quote
        depth_10pct_quote = raw_metrics.depth_10pct_quote
    else:
        depth_1pct_quote = raw_metrics.get("depth_1pct_quote")
        depth_2pct_quote = raw_metrics.get("depth_2pct_quote")
        depth_10pct_quote = raw_metrics.get("depth_10pct_quote")

    if depth_band_pct <= 0.0100001:
        return depth_1pct_quote
    if depth_band_pct <= 0.0200001:
        return depth_2pct_quote
    return depth_10pct_quote


def resolve_band_depth_quote_for_listing(
    listing: models.ListingRecord,
    depth_band_pct: float,
) -> typing.Optional[float]:
    if depth_band_pct <= 0.0200001 and listing.depth_2pct_quote is not None:
        return listing.depth_2pct_quote
    if listing.bid_depth_quote is not None and listing.ask_depth_quote is not None:
        return listing.bid_depth_quote + listing.ask_depth_quote
    return listing.depth_2pct_quote


def build_delisting_risk_cards(
    labels: list[str],
    volume_quote: typing.Optional[float],
    band_depth_quote: typing.Optional[float],
    thresholds: app_config.DelistingRiskExchangeThresholds,
) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    band_label = f"±{thresholds.depth_band_pct * 100:g}%"

    if LABEL_LOW_DEPTH in labels:
        if band_depth_quote is None:
            depth_evidence = f"Depth at {band_label} unavailable at snapshot"
        else:
            depth_evidence = (
                f"{_format_usd_short(band_depth_quote)} at {band_label} vs "
                f"{_format_usd_short(thresholds.min_depth_quote_usdt)} minimum"
            )
        cards.append({
            "severity": "Critical",
            "title": "Low depth",
            "impact": "Below exchange delisting threshold",
            "evidence": depth_evidence,
        })

    if LABEL_LOW_VOLUME in labels:
        if volume_quote is None:
            volume_evidence = "24h volume unavailable at snapshot"
        else:
            volume_evidence = (
                f"{_format_usd_short(volume_quote)} vs "
                f"{_format_usd_short(thresholds.min_volume_quote_usdt)} minimum"
            )
        cards.append({
            "severity": "Critical",
            "title": "Low volume",
            "impact": "Below exchange delisting threshold",
            "evidence": volume_evidence,
        })

    return cards
