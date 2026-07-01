import typing

import liquidity_audit.config as app_config
import liquidity_audit.domain.health.order_book as health_order_book
import liquidity_audit.domain.models as models

# Ported from a_octobot_wrapper kw_constants (market-making depth/spread scoring)
DEPTH_SCORE_THRESHOLDS = [
    ([0.01, 1.0], [1.0, 1.0]),
    ([0.003, 0.01], [0.5, 1.0]),
    ([0.0, 0.003], [0.0, 0.5]),
]

SPREAD_SCORE_THRESHOLDS = [
    ([0.0, 0.002], [1.0, 1.0]),
    ([0.002, 0.008], [0.5, 1.0]),
    ([0.008, 1.0], [0.0, 0.0]),
]

LABEL_FEW_ORDERS = "few_orders"
LABEL_SHALLOW_LIQUIDITY = "shallow_liquidity"
LABEL_WIDE_SPREAD = "wide_spread"
LABEL_UNDER_DEPTH_FOR_VOLUME = "under_depth_for_volume"
LABEL_FRAGMENTED_TIGHT_DEPTH = "fragmented_tight_depth"
LABEL_SHALLOW_TOTAL_DEPTH = "shallow_total_depth"
LABEL_LOW_LIQUIDITY_SCORE = "low_liquidity_score"


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _score_from_thresholds(ratio: float, thresholds: list) -> float:
    for threshold_ratios, values in thresholds:
        ratio_low, ratio_high = threshold_ratios
        if ratio_low <= ratio <= ratio_high:
            if ratio_high == 0:
                return values[0]
            return values[0] + (ratio / ratio_high * (values[1] - values[0]))
    return 0.0


def depth_score_from_ratio(depth_ratio: float) -> float:
    perfect_band_low = DEPTH_SCORE_THRESHOLDS[0][0][0]
    if depth_ratio >= perfect_band_low:
        return 1.0
    return _score_from_thresholds(depth_ratio, DEPTH_SCORE_THRESHOLDS)


def spread_score_from_ratio(spread_ratio: float) -> float:
    return _score_from_thresholds(spread_ratio, SPREAD_SCORE_THRESHOLDS)


def compute_orders_score(
    bid_levels: int,
    ask_levels: int,
    health_rules: app_config.HealthRules,
    order_book_limit: typing.Optional[int] = None,
) -> float:
    if (
        order_book_limit is not None
        and order_book_limit > 0
        and bid_levels >= order_book_limit
        and ask_levels >= order_book_limit
    ):
        return 1.0
    bid_score = _clamp(bid_levels / health_rules.min_buy_orders, 0.0, 1.0)
    ask_score = _clamp(ask_levels / health_rules.min_sell_orders, 0.0, 1.0)
    return (bid_score + ask_score) / 2


def compute_depth_pillar_score(
    bid_depth_quote: float,
    ask_depth_quote: float,
    volume_quote: typing.Optional[float],
) -> float:
    bid_score = compute_depth_side_score(bid_depth_quote, volume_quote)
    ask_score = compute_depth_side_score(ask_depth_quote, volume_quote)
    return min(bid_score, ask_score)


def compute_depth_side_score(
    band_depth_quote: float,
    volume_quote: typing.Optional[float],
) -> float:
    if volume_quote is None:
        return 0.0
    depth_ratio = band_depth_quote / volume_quote
    return depth_score_from_ratio(depth_ratio)


def compute_spread_score(
    sorted_bids_list: list,
    sorted_asks_list: list,
    mid_price: float,
) -> float:
    bid_ask_spread_ratio = health_order_book.compute_bid_ask_spread_ratio(
        sorted_bids_list, sorted_asks_list, mid_price,
    )
    if bid_ask_spread_ratio is None:
        return 0.0
    return spread_score_from_ratio(bid_ask_spread_ratio)


def compute_liquidity_score(
    orders_score: float,
    depth_tight_score: float,
    depth_larger_score: float,
    spread_score: float,
) -> float:
    return (orders_score + depth_tight_score + depth_larger_score + spread_score) / 4


def _depth_volume_ratio_fails_minimum(
    band_depth_quote: float,
    volume_quote: typing.Optional[float],
    min_depth_volume_ratio: float,
) -> bool:
    if volume_quote is None or volume_quote <= 0:
        return False
    return (band_depth_quote / volume_quote) < min_depth_volume_ratio


def _fails_few_orders(
    bid_levels: int,
    ask_levels: int,
    min_bid_levels: int,
    min_ask_levels: int,
) -> bool:
    return bid_levels < min_bid_levels or ask_levels < min_ask_levels


def _fails_shallow_liquidity(
    bid_larger_depth_quote: float,
    ask_larger_depth_quote: float,
    min_bid_larger_depth_quote_usdt: float,
    min_ask_larger_depth_quote_usdt: float,
) -> bool:
    return (
        bid_larger_depth_quote < min_bid_larger_depth_quote_usdt
        or ask_larger_depth_quote < min_ask_larger_depth_quote_usdt
    )


def _fails_wide_spread(
    bid_ask_spread_ratio: float,
    max_bid_ask_spread_pct: float,
) -> bool:
    return bid_ask_spread_ratio > max_bid_ask_spread_pct


def _fails_fragmented_tight_depth(
    bid_depth_quote: float,
    ask_depth_quote: float,
    min_bid_depth_quote_usdt: float,
    min_ask_depth_quote_usdt: float,
) -> bool:
    return (
        bid_depth_quote < min_bid_depth_quote_usdt
        or ask_depth_quote < min_ask_depth_quote_usdt
    )


def _fails_shallow_total_depth(
    bid_total_depth_quote: float,
    ask_total_depth_quote: float,
    min_bid_total_depth_quote_usdt: float,
    min_ask_total_depth_quote_usdt: float,
) -> bool:
    return (
        bid_total_depth_quote < min_bid_total_depth_quote_usdt
        or ask_total_depth_quote < min_ask_total_depth_quote_usdt
    )


def _fails_under_depth_for_volume(
    bid_depth_quote: float,
    ask_depth_quote: float,
    bid_larger_depth_quote: float,
    ask_larger_depth_quote: float,
    volume_quote: typing.Optional[float],
    thresholds: app_config.UnderDepthForVolumeLabelThresholds,
) -> bool:
    if volume_quote is None or volume_quote <= 0:
        return False
    return (
        _depth_volume_ratio_fails_minimum(
            bid_depth_quote, volume_quote, thresholds.min_bid_depth_volume_ratio,
        )
        or _depth_volume_ratio_fails_minimum(
            ask_depth_quote, volume_quote, thresholds.min_ask_depth_volume_ratio,
        )
        or _depth_volume_ratio_fails_minimum(
            bid_larger_depth_quote,
            volume_quote,
            thresholds.min_bid_larger_depth_volume_ratio,
        )
        or _depth_volume_ratio_fails_minimum(
            ask_larger_depth_quote,
            volume_quote,
            thresholds.min_ask_larger_depth_volume_ratio,
        )
    )


def qualifies_for_health_label(
    label_id: str,
    bid_levels: typing.Optional[int],
    ask_levels: typing.Optional[int],
    bid_depth_quote: typing.Optional[float],
    ask_depth_quote: typing.Optional[float],
    bid_larger_depth_quote: typing.Optional[float],
    ask_larger_depth_quote: typing.Optional[float],
    bid_total_depth_quote: typing.Optional[float],
    ask_total_depth_quote: typing.Optional[float],
    volume_quote: typing.Optional[float],
    bid_ask_spread_ratio: typing.Optional[float],
    liquidity_score: float,
    health_labels: app_config.HealthLabelsConfig,
    min_liquidity_score: float,
) -> bool:
    if label_id == LABEL_FEW_ORDERS:
        if bid_levels is None or ask_levels is None:
            return False
        return _fails_few_orders(
            bid_levels,
            ask_levels,
            health_labels.few_orders.min_bid_levels,
            health_labels.few_orders.min_ask_levels,
        )
    if label_id == LABEL_SHALLOW_LIQUIDITY:
        if bid_larger_depth_quote is None or ask_larger_depth_quote is None:
            return False
        return _fails_shallow_liquidity(
            bid_larger_depth_quote,
            ask_larger_depth_quote,
            health_labels.shallow_liquidity.min_bid_larger_depth_quote_usdt,
            health_labels.shallow_liquidity.min_ask_larger_depth_quote_usdt,
        )
    if label_id == LABEL_WIDE_SPREAD:
        if bid_ask_spread_ratio is None:
            return False
        return _fails_wide_spread(
            bid_ask_spread_ratio,
            health_labels.wide_spread.max_bid_ask_spread_pct,
        )
    if label_id == LABEL_UNDER_DEPTH_FOR_VOLUME:
        if (
            bid_depth_quote is None
            or ask_depth_quote is None
            or bid_larger_depth_quote is None
            or ask_larger_depth_quote is None
        ):
            return False
        return _fails_under_depth_for_volume(
            bid_depth_quote,
            ask_depth_quote,
            bid_larger_depth_quote,
            ask_larger_depth_quote,
            volume_quote,
            health_labels.under_depth_for_volume,
        )
    if label_id == LABEL_FRAGMENTED_TIGHT_DEPTH:
        if bid_depth_quote is None or ask_depth_quote is None:
            return False
        return _fails_fragmented_tight_depth(
            bid_depth_quote,
            ask_depth_quote,
            health_labels.fragmented_tight_depth.min_bid_depth_quote_usdt,
            health_labels.fragmented_tight_depth.min_ask_depth_quote_usdt,
        )
    if label_id == LABEL_SHALLOW_TOTAL_DEPTH:
        if bid_total_depth_quote is None or ask_total_depth_quote is None:
            return False
        return _fails_shallow_total_depth(
            bid_total_depth_quote,
            ask_total_depth_quote,
            health_labels.shallow_total_depth.min_bid_total_depth_quote_usdt,
            health_labels.shallow_total_depth.min_ask_total_depth_quote_usdt,
        )
    if label_id == LABEL_LOW_LIQUIDITY_SCORE:
        return liquidity_score < min_liquidity_score
    raise ValueError(f"unknown health label id: {label_id}")


def collect_qualifying_health_labels(
    bid_levels: typing.Optional[int],
    ask_levels: typing.Optional[int],
    bid_depth_quote: typing.Optional[float],
    ask_depth_quote: typing.Optional[float],
    bid_larger_depth_quote: typing.Optional[float],
    ask_larger_depth_quote: typing.Optional[float],
    bid_total_depth_quote: typing.Optional[float],
    ask_total_depth_quote: typing.Optional[float],
    volume_quote: typing.Optional[float],
    bid_ask_spread_ratio: typing.Optional[float],
    liquidity_score: float,
    health_labels: app_config.HealthLabelsConfig,
    min_liquidity_score: float,
) -> list[str]:
    if bid_levels is None:
        return []
    qualifying_labels = []
    for label_id in health_labels.priority:
        if qualifies_for_health_label(
            label_id,
            bid_levels,
            ask_levels,
            bid_depth_quote,
            ask_depth_quote,
            bid_larger_depth_quote,
            ask_larger_depth_quote,
            bid_total_depth_quote,
            ask_total_depth_quote,
            volume_quote,
            bid_ask_spread_ratio,
            liquidity_score,
            health_labels,
            min_liquidity_score,
        ):
            qualifying_labels.append(label_id)
    return qualifying_labels


def assign_health_labels(
    qualifying_labels: list[str],
    priority: list[str],
) -> tuple[str, list[str]]:
    ordered_labels = [
        label_id for label_id in priority if label_id in qualifying_labels
    ]
    if not ordered_labels:
        return "", []
    return ordered_labels[0], ordered_labels[1:]


def resolve_health_labels(
    bid_levels: typing.Optional[int],
    ask_levels: typing.Optional[int],
    bid_depth_quote: typing.Optional[float],
    ask_depth_quote: typing.Optional[float],
    bid_larger_depth_quote: typing.Optional[float],
    ask_larger_depth_quote: typing.Optional[float],
    bid_total_depth_quote: typing.Optional[float],
    ask_total_depth_quote: typing.Optional[float],
    volume_quote: typing.Optional[float],
    bid_ask_spread_ratio: typing.Optional[float],
    liquidity_score: float,
    health_labels: app_config.HealthLabelsConfig,
    min_liquidity_score: float,
) -> tuple[str, list[str]]:
    qualifying_labels = collect_qualifying_health_labels(
        bid_levels,
        ask_levels,
        bid_depth_quote,
        ask_depth_quote,
        bid_larger_depth_quote,
        ask_larger_depth_quote,
        bid_total_depth_quote,
        ask_total_depth_quote,
        volume_quote,
        bid_ask_spread_ratio,
        liquidity_score,
        health_labels,
        min_liquidity_score,
    )
    return assign_health_labels(qualifying_labels, health_labels.priority)


def has_unhealthy_red_flag(
    bid_levels: typing.Optional[int],
    ask_levels: typing.Optional[int],
    bid_depth_quote: typing.Optional[float],
    ask_depth_quote: typing.Optional[float],
    bid_larger_depth_quote: typing.Optional[float],
    ask_larger_depth_quote: typing.Optional[float],
    volume_quote: typing.Optional[float],
    bid_ask_spread_ratio: typing.Optional[float],
    unhealthy_values: app_config.UnhealthyValues,
) -> bool:
    if (
        bid_levels is None
        or ask_levels is None
        or bid_depth_quote is None
        or ask_depth_quote is None
        or bid_larger_depth_quote is None
        or ask_larger_depth_quote is None
        or bid_ask_spread_ratio is None
    ):
        return True

    if _fails_few_orders(
        bid_levels,
        ask_levels,
        unhealthy_values.min_bid_levels,
        unhealthy_values.min_ask_levels,
    ):
        return True
    if _fails_fragmented_tight_depth(
        bid_depth_quote,
        ask_depth_quote,
        unhealthy_values.min_bid_depth_quote_usdt,
        unhealthy_values.min_ask_depth_quote_usdt,
    ):
        return True
    if _fails_shallow_liquidity(
        bid_larger_depth_quote,
        ask_larger_depth_quote,
        unhealthy_values.min_bid_larger_depth_quote_usdt,
        unhealthy_values.min_ask_larger_depth_quote_usdt,
    ):
        return True
    if _fails_wide_spread(
        bid_ask_spread_ratio,
        unhealthy_values.max_bid_ask_spread_pct,
    ):
        return True
    if _fails_under_depth_for_volume(
        bid_depth_quote,
        ask_depth_quote,
        bid_larger_depth_quote,
        ask_larger_depth_quote,
        volume_quote,
        app_config.UnderDepthForVolumeLabelThresholds(
            min_bid_depth_volume_ratio=unhealthy_values.min_bid_depth_volume_ratio,
            min_ask_depth_volume_ratio=unhealthy_values.min_ask_depth_volume_ratio,
            min_bid_larger_depth_volume_ratio=unhealthy_values.min_bid_larger_depth_volume_ratio,
            min_ask_larger_depth_volume_ratio=unhealthy_values.min_ask_larger_depth_volume_ratio,
        ),
    ):
        return True
    return False


def resolve_is_low_health(
    has_red_flag: bool,
    liquidity_score: float,
    min_liquidity_score: float,
) -> bool:
    if has_red_flag:
        return True
    return liquidity_score < min_liquidity_score


def _compute_liquidity_score_from_metrics(
    bid_levels: int,
    ask_levels: int,
    bid_depth_quote: float,
    ask_depth_quote: float,
    bid_larger_depth_quote: float,
    ask_larger_depth_quote: float,
    volume_quote: typing.Optional[float],
    bid_ask_spread_ratio: typing.Optional[float],
    health_rules: app_config.HealthRules,
    order_book_limit: typing.Optional[int] = None,
) -> float:
    orders_score = compute_orders_score(
        bid_levels,
        ask_levels,
        health_rules,
        order_book_limit,
    )
    depth_tight_score = compute_depth_pillar_score(
        bid_depth_quote,
        ask_depth_quote,
        volume_quote,
    )
    depth_larger_score = compute_depth_pillar_score(
        bid_larger_depth_quote,
        ask_larger_depth_quote,
        volume_quote,
    )
    spread_score = (
        0.0
        if bid_ask_spread_ratio is None
        else spread_score_from_ratio(bid_ask_spread_ratio)
    )
    return compute_liquidity_score(
        orders_score,
        depth_tight_score,
        depth_larger_score,
        spread_score,
    )


def evaluate_health(
    order_book: dict,
    ticker: dict,
    health_rules: app_config.HealthRules,
    unhealthy_values: app_config.UnhealthyValues,
    health_labels: app_config.HealthLabelsConfig,
    min_liquidity_score: float,
    order_book_limit: typing.Optional[int] = None,
) -> models.HealthResult:
    sorted_bids_list = health_order_book.sorted_bids(order_book.get("bids", []))
    sorted_asks_list = health_order_book.sorted_asks(order_book.get("asks", []))
    bid_levels = len(sorted_bids_list)
    ask_levels = len(sorted_asks_list)
    bid_total_depth_quote = health_order_book.compute_total_depth_quote(sorted_bids_list)
    ask_total_depth_quote = health_order_book.compute_total_depth_quote(sorted_asks_list)
    volume_quote = health_order_book.parse_volume_quote(ticker)

    mid_price = health_order_book.compute_mid_price(sorted_bids_list, sorted_asks_list, ticker)
    if mid_price is None:
        label_primary, labels_other = resolve_health_labels(
            bid_levels,
            ask_levels,
            0.0,
            0.0,
            0.0,
            0.0,
            bid_total_depth_quote,
            ask_total_depth_quote,
            volume_quote,
            None,
            0.0,
            health_labels,
            min_liquidity_score,
        )
        return models.HealthResult(
            bid_levels=bid_levels,
            ask_levels=ask_levels,
            bid_depth_quote=0.0,
            ask_depth_quote=0.0,
            bid_larger_depth_quote=0.0,
            ask_larger_depth_quote=0.0,
            bid_total_depth_quote=bid_total_depth_quote,
            ask_total_depth_quote=ask_total_depth_quote,
            volume_quote=volume_quote,
            bid_ask_spread_ratio=None,
            liquidity_score=0.0,
            is_low_health=True,
            health_label_primary=label_primary,
            health_labels_other=labels_other,
        )

    bid_depth_quote = health_order_book.compute_band_depth_quote(
        sorted_bids_list, mid_price, health_rules.depth_band_pct, are_bids=True,
    )
    ask_depth_quote = health_order_book.compute_band_depth_quote(
        sorted_asks_list, mid_price, health_rules.depth_band_pct, are_bids=False,
    )
    bid_larger_depth_quote = health_order_book.compute_band_depth_quote(
        sorted_bids_list, mid_price, health_rules.larger_depth_band_pct, are_bids=True,
    )
    ask_larger_depth_quote = health_order_book.compute_band_depth_quote(
        sorted_asks_list, mid_price, health_rules.larger_depth_band_pct, are_bids=False,
    )
    bid_ask_spread_ratio = health_order_book.compute_bid_ask_spread_ratio(
        sorted_bids_list, sorted_asks_list, mid_price,
    )

    liquidity_score = _compute_liquidity_score_from_metrics(
        bid_levels,
        ask_levels,
        bid_depth_quote,
        ask_depth_quote,
        bid_larger_depth_quote,
        ask_larger_depth_quote,
        volume_quote,
        bid_ask_spread_ratio,
        health_rules,
        order_book_limit,
    )
    red_flag = has_unhealthy_red_flag(
        bid_levels,
        ask_levels,
        bid_depth_quote,
        ask_depth_quote,
        bid_larger_depth_quote,
        ask_larger_depth_quote,
        volume_quote,
        bid_ask_spread_ratio,
        unhealthy_values,
    )
    is_low_health = resolve_is_low_health(red_flag, liquidity_score, min_liquidity_score)
    label_primary, labels_other = resolve_health_labels(
        bid_levels,
        ask_levels,
        bid_depth_quote,
        ask_depth_quote,
        bid_larger_depth_quote,
        ask_larger_depth_quote,
        bid_total_depth_quote,
        ask_total_depth_quote,
        volume_quote,
        bid_ask_spread_ratio,
        liquidity_score,
        health_labels,
        min_liquidity_score,
    )

    return models.HealthResult(
        bid_levels=bid_levels,
        ask_levels=ask_levels,
        bid_depth_quote=bid_depth_quote,
        ask_depth_quote=ask_depth_quote,
        bid_larger_depth_quote=bid_larger_depth_quote,
        ask_larger_depth_quote=ask_larger_depth_quote,
        bid_total_depth_quote=bid_total_depth_quote,
        ask_total_depth_quote=ask_total_depth_quote,
        volume_quote=volume_quote,
        bid_ask_spread_ratio=bid_ask_spread_ratio,
        liquidity_score=liquidity_score,
        is_low_health=is_low_health,
        health_label_primary=label_primary,
        health_labels_other=labels_other,
    )


def evaluate_health_from_stored_metrics(
    bid_levels: typing.Optional[int],
    ask_levels: typing.Optional[int],
    bid_depth_quote: typing.Optional[float],
    ask_depth_quote: typing.Optional[float],
    bid_larger_depth_quote: typing.Optional[float],
    ask_larger_depth_quote: typing.Optional[float],
    bid_total_depth_quote: typing.Optional[float],
    ask_total_depth_quote: typing.Optional[float],
    volume_quote: typing.Optional[float],
    bid_ask_spread_ratio: typing.Optional[float],
    health_rules: app_config.HealthRules,
    unhealthy_values: app_config.UnhealthyValues,
    health_labels: app_config.HealthLabelsConfig,
    min_liquidity_score: float,
    order_book_limit: typing.Optional[int] = None,
) -> models.HealthResult:
    """Recompute is_low_health and liquidity_score from CSV-stored metrics."""
    if bid_levels is None:
        return models.HealthResult(
            bid_levels=0,
            ask_levels=0 if ask_levels is None else ask_levels,
            bid_depth_quote=0.0 if bid_depth_quote is None else bid_depth_quote,
            ask_depth_quote=0.0 if ask_depth_quote is None else ask_depth_quote,
            bid_larger_depth_quote=0.0 if bid_larger_depth_quote is None else bid_larger_depth_quote,
            ask_larger_depth_quote=0.0 if ask_larger_depth_quote is None else ask_larger_depth_quote,
            bid_total_depth_quote=0.0 if bid_total_depth_quote is None else bid_total_depth_quote,
            ask_total_depth_quote=0.0 if ask_total_depth_quote is None else ask_total_depth_quote,
            volume_quote=volume_quote,
            bid_ask_spread_ratio=bid_ask_spread_ratio,
            liquidity_score=0.0,
            is_low_health=False,
            health_label_primary="",
            health_labels_other=[],
        )

    liquidity_score = _compute_liquidity_score_from_metrics(
        bid_levels,
        ask_levels if ask_levels is not None else 0,
        bid_depth_quote if bid_depth_quote is not None else 0.0,
        ask_depth_quote if ask_depth_quote is not None else 0.0,
        bid_larger_depth_quote if bid_larger_depth_quote is not None else 0.0,
        ask_larger_depth_quote if ask_larger_depth_quote is not None else 0.0,
        volume_quote,
        bid_ask_spread_ratio,
        health_rules,
        order_book_limit,
    )
    red_flag = has_unhealthy_red_flag(
        bid_levels,
        ask_levels,
        bid_depth_quote,
        ask_depth_quote,
        bid_larger_depth_quote,
        ask_larger_depth_quote,
        volume_quote,
        bid_ask_spread_ratio,
        unhealthy_values,
    )
    is_low_health = resolve_is_low_health(red_flag, liquidity_score, min_liquidity_score)
    label_primary, labels_other = resolve_health_labels(
        bid_levels,
        ask_levels,
        bid_depth_quote,
        ask_depth_quote,
        bid_larger_depth_quote,
        ask_larger_depth_quote,
        bid_total_depth_quote,
        ask_total_depth_quote,
        volume_quote,
        bid_ask_spread_ratio,
        liquidity_score,
        health_labels,
        min_liquidity_score,
    )

    return models.HealthResult(
        bid_levels=bid_levels,
        ask_levels=ask_levels if ask_levels is not None else 0,
        bid_depth_quote=bid_depth_quote if bid_depth_quote is not None else 0.0,
        ask_depth_quote=ask_depth_quote if ask_depth_quote is not None else 0.0,
        bid_larger_depth_quote=bid_larger_depth_quote if bid_larger_depth_quote is not None else 0.0,
        ask_larger_depth_quote=ask_larger_depth_quote if ask_larger_depth_quote is not None else 0.0,
        bid_total_depth_quote=bid_total_depth_quote if bid_total_depth_quote is not None else 0.0,
        ask_total_depth_quote=ask_total_depth_quote if ask_total_depth_quote is not None else 0.0,
        volume_quote=volume_quote,
        bid_ask_spread_ratio=bid_ask_spread_ratio,
        liquidity_score=liquidity_score,
        is_low_health=is_low_health,
        health_label_primary=label_primary,
        health_labels_other=labels_other,
    )
