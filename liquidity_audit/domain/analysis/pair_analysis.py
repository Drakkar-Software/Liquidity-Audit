"""Extended liquidity analysis for 10-candidate reports (raw metrics + display layer)."""

import dataclasses
import math
import statistics
import typing

import liquidity_audit.config as app_config
import liquidity_audit.config.analysis as analysis_config
import liquidity_audit.domain.models as models
import liquidity_audit.domain.health.evaluation as health_evaluation
import liquidity_audit.domain.health.order_book as health_order_book

DEPTH_2_BAND_PCT = 0.02
SLIPPAGE_TRADE_SIZES = (100, 1000, 5000, 10000, 25000)
SLIPPAGE_DISPLAY_SIZE_PREFERENCE = (10_000, 1_000, 100)
INVESTOR_SIMULATOR_MAX_CARDS = 3
MIN_FILL_RATIO = 0.95
HOLLOW_VOLUME_RATIO_THRESHOLD = 10.0
HIGH_LIQUIDITY_SCORE_FOR_VOLUME_EXEMPT = 0.7
GRADE_THRESHOLDS = ((85, "A"), (70, "B"), (55, "C"), (40, "D"))
PEER_COUNT = 3
PEER_METRIC_DEADBAND = 0.95
VOLUME_TIER_RATIO = 5.0
DEPTH_ASYMMETRY_THRESHOLD = 0.4
VOLUME_SKEW_THRESHOLD = 70.0

PEER_TIER_CRITERIA: dict[str, str] = {
    "volume_micro_bucket": "Similar micro-volume tier and quote currency on exchange",
    "volume_5x": "Similar volume tier (5x) and quote currency on exchange",
    "volume_20x": "Similar volume tier (20x) and quote currency on exchange",
    "volume_100x": "Similar volume tier (100x) and quote currency on exchange",
    "marketcap_closest": "Closest market cap and quote currency on exchange",
    "liquidity_score": "Top liquidity score and quote currency on exchange",
    "none": "No other same-quote pairs on exchange",
}


@dataclasses.dataclass(frozen=True)
class PeerSelectionSettings:
    min_relevant_usdt_volume: float
    peer_volume_tier_ratios: tuple[float, ...]
    peer_count: int = PEER_COUNT


def peer_selection_settings_from_analysis_config(
    analysis_config: app_config.AnalysisConfig,
) -> PeerSelectionSettings:
    return PeerSelectionSettings(
        min_relevant_usdt_volume=analysis_config.min_relevant_usdt_volume,
        peer_volume_tier_ratios=analysis_config.peer_volume_tier_ratios,
    )


def default_peer_selection_settings() -> PeerSelectionSettings:
    return PeerSelectionSettings(
        min_relevant_usdt_volume=analysis_config.DEFAULT_MIN_RELEVANT_USDT_VOLUME,
        peer_volume_tier_ratios=analysis_config.DEFAULT_PEER_VOLUME_TIER_RATIOS,
    )


def symbol_to_slug(symbol: str) -> str:
    return symbol.replace("/", "_")


def _parse_positive_ticker_float(ticker: dict, key: str) -> typing.Optional[float]:
    raw_value = ticker.get(key)
    if raw_value is None:
        return None
    parsed = float(raw_value)
    if parsed <= 0:
        return None
    return parsed


def parse_ticker_volume_skew(
    ticker: dict,
) -> tuple[
    typing.Optional[float],
    typing.Optional[float],
    typing.Optional[float],
    typing.Optional[float],
]:
    bid_volume_quote = _parse_positive_ticker_float(ticker, "bidVolume")
    ask_volume_quote = _parse_positive_ticker_float(ticker, "askVolume")
    if bid_volume_quote is None or ask_volume_quote is None:
        return bid_volume_quote, ask_volume_quote, None, None
    total_volume = bid_volume_quote + ask_volume_quote
    if total_volume <= 0:
        return bid_volume_quote, ask_volume_quote, None, None
    buy_volume_pct = bid_volume_quote / total_volume * 100
    sell_volume_pct = ask_volume_quote / total_volume * 100
    return bid_volume_quote, ask_volume_quote, buy_volume_pct, sell_volume_pct


def compute_price_spans(
    sorted_bids: list,
    sorted_asks: list,
    mid_price: float,
) -> tuple[float, float]:
    if mid_price <= 0:
        return 0.0, 0.0
    worst_bid = float(sorted_bids[-1][0]) if sorted_bids else mid_price
    worst_ask = float(sorted_asks[-1][0]) if sorted_asks else mid_price
    bid_span_pct = (mid_price - worst_bid) / mid_price * 100
    ask_span_pct = (worst_ask - mid_price) / mid_price * 100
    return bid_span_pct, ask_span_pct


def compute_depth_2pct_capped(bid_span_pct: float, ask_span_pct: float) -> bool:
    return bid_span_pct < 2.0 or ask_span_pct < 2.0


def compute_max_fillable_buy_quote(sorted_asks: list) -> float:
    return sum(float(level[0]) * float(level[1]) for level in sorted_asks)


def simulate_market_buy_slippage(
    sorted_asks: list,
    mid_price: typing.Optional[float],
    trade_sizes: tuple[int, ...] = SLIPPAGE_TRADE_SIZES,
) -> list[dict[str, typing.Any]]:
    if mid_price is None or mid_price <= 0 or not sorted_asks:
        return [
            {"size": trade_size, "pct": None, "omitted": True, "fill_ratio": 0.0}
            for trade_size in trade_sizes
        ]

    slippage_rows: list[dict[str, typing.Any]] = []
    for trade_size in trade_sizes:
        remaining_quote = float(trade_size)
        tokens_bought = 0.0
        for price_raw, amount_raw in sorted_asks:
            price = float(price_raw)
            amount = float(amount_raw)
            level_quote = price * amount
            take_quote = min(remaining_quote, level_quote)
            tokens_bought += take_quote / price
            remaining_quote -= take_quote
            if remaining_quote <= 0:
                break

        filled_quote = float(trade_size) - remaining_quote
        fill_ratio = filled_quote / float(trade_size)
        if fill_ratio < MIN_FILL_RATIO:
            slippage_rows.append({
                "size": trade_size,
                "pct": None,
                "omitted": True,
                "fill_ratio": fill_ratio,
            })
            continue

        average_price = float(trade_size) / tokens_bought
        slippage_pct = (average_price - mid_price) / mid_price * 100
        slippage_rows.append({
            "size": trade_size,
            "pct": slippage_pct,
            "omitted": False,
            "fill_ratio": fill_ratio,
        })
    return slippage_rows


def slippage_pct_at_size(slippage_rows: list[dict], size: int) -> typing.Optional[float]:
    for row in slippage_rows:
        if row["size"] == size and not row.get("omitted"):
            return row.get("pct")
    return None


def resolve_slippage_display(
    slippage_rows: list[dict],
    preferred_sizes: tuple[int, ...] = SLIPPAGE_DISPLAY_SIZE_PREFERENCE,
) -> tuple[typing.Optional[int], typing.Optional[float]]:
    for trade_size in preferred_sizes:
        slippage_pct = slippage_pct_at_size(slippage_rows, trade_size)
        if slippage_pct is not None:
            return trade_size, slippage_pct
    return None, None


def format_slippage_trade_size_label(trade_size: int) -> str:
    if trade_size >= 1000:
        return f"${trade_size // 1000}k"
    return f"${trade_size}"


def slippage_metric_title(trade_size: typing.Optional[int]) -> str:
    if trade_size is None:
        return "Slippage"
    return f"Slippage {format_slippage_trade_size_label(trade_size)}"


@dataclasses.dataclass
class ExtendedRawMetrics:
    exchange: str
    symbol: str
    full_name: str
    mid_price: typing.Optional[float]
    spread_pct: typing.Optional[float]
    bid_levels: int
    ask_levels: int
    bid_depth_1pct_quote: float
    ask_depth_1pct_quote: float
    depth_1pct_quote: float
    depth_2pct_quote: float
    depth_10pct_quote: float
    bid_larger_depth_quote: float
    ask_larger_depth_quote: float
    depth_2pct_capped: bool
    volume_quote: typing.Optional[float]
    bid_volume_quote: typing.Optional[float]
    ask_volume_quote: typing.Optional[float]
    buy_volume_pct: typing.Optional[float]
    sell_volume_pct: typing.Optional[float]
    volume_depth_ratio: typing.Optional[float]
    max_fillable_buy_quote: float
    liquidity_score: float
    is_low_health: bool
    health_label_primary: str
    health_labels_other: list[str]
    slippage: list[dict[str, typing.Any]]
    fetched_at: str

    def to_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


def build_extended_raw_metrics(
    exchange: str,
    symbol: str,
    full_name: str,
    order_book: dict,
    ticker: dict,
    health: models.HealthResult,
    fetched_at: str,
) -> ExtendedRawMetrics:
    sorted_bids_list = health_order_book.sorted_bids(order_book.get("bids", []))
    sorted_asks_list = health_order_book.sorted_asks(order_book.get("asks", []))
    mid_price = health_order_book.compute_mid_price(sorted_bids_list, sorted_asks_list, ticker)
    bid_span_pct, ask_span_pct = compute_price_spans(sorted_bids_list, sorted_asks_list, mid_price or 0.0)

    bid_depth_2pct = (
        health_order_book.compute_band_depth_quote(sorted_bids_list, mid_price, DEPTH_2_BAND_PCT, True)
        if mid_price is not None
        else 0.0
    )
    ask_depth_2pct = (
        health_order_book.compute_band_depth_quote(sorted_asks_list, mid_price, DEPTH_2_BAND_PCT, False)
        if mid_price is not None
        else 0.0
    )
    depth_1pct_quote = health.bid_depth_quote + health.ask_depth_quote
    depth_2pct_quote = bid_depth_2pct + ask_depth_2pct
    depth_10pct_quote = health.bid_larger_depth_quote + health.ask_larger_depth_quote

    bid_volume_quote, ask_volume_quote, buy_volume_pct, sell_volume_pct = (
        parse_ticker_volume_skew(ticker)
    )
    tight_depth_total = health.bid_depth_quote + health.ask_depth_quote
    volume_depth_ratio = (
        health.volume_quote / tight_depth_total
        if health.volume_quote is not None and tight_depth_total > 0
        else None
    )
    spread_pct = (
        health.bid_ask_spread_ratio * 100
        if health.bid_ask_spread_ratio is not None
        else None
    )

    return ExtendedRawMetrics(
        exchange=exchange,
        symbol=symbol,
        full_name=full_name,
        mid_price=mid_price,
        spread_pct=spread_pct,
        bid_levels=health.bid_levels,
        ask_levels=health.ask_levels,
        bid_depth_1pct_quote=health.bid_depth_quote,
        ask_depth_1pct_quote=health.ask_depth_quote,
        depth_1pct_quote=depth_1pct_quote,
        depth_2pct_quote=depth_2pct_quote,
        depth_10pct_quote=depth_10pct_quote,
        bid_larger_depth_quote=health.bid_larger_depth_quote,
        ask_larger_depth_quote=health.ask_larger_depth_quote,
        depth_2pct_capped=compute_depth_2pct_capped(bid_span_pct, ask_span_pct),
        volume_quote=health.volume_quote,
        bid_volume_quote=bid_volume_quote,
        ask_volume_quote=ask_volume_quote,
        buy_volume_pct=buy_volume_pct,
        sell_volume_pct=sell_volume_pct,
        volume_depth_ratio=volume_depth_ratio,
        max_fillable_buy_quote=compute_max_fillable_buy_quote(sorted_asks_list),
        liquidity_score=health.liquidity_score,
        is_low_health=health.is_low_health,
        health_label_primary=health.health_label_primary,
        health_labels_other=list(health.health_labels_other),
        slippage=simulate_market_buy_slippage(sorted_asks_list, mid_price),
        fetched_at=fetched_at,
    )


def score_to_grade(score_100: int) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if score_100 >= threshold:
            return grade
    return "F"


def score_to_status(score_100: int, is_low_health: bool) -> str:
    if is_low_health or score_100 < 40:
        return "Poor"
    if score_100 >= 70 and not is_low_health:
        return "Good"
    return "Fair"


def status_to_class(status: str) -> str:
    if status == "Good":
        return "status-good"
    if status == "Fair":
        return "status-fair"
    return "status-poor"


def _median_or_none(values: list[float]) -> typing.Optional[float]:
    if not values:
        return None
    return float(statistics.median(values))


def compute_exchange_averages(
    raw_metrics_list: list[ExtendedRawMetrics],
    rankings_min_volume_quote: float,
) -> dict[str, typing.Optional[float]]:
    eligible = [
        raw_metrics
        for raw_metrics in raw_metrics_list
        if raw_metrics.volume_quote is not None
        and raw_metrics.volume_quote >= rankings_min_volume_quote
    ]
    spread_values = [
        raw_metrics.spread_pct
        for raw_metrics in eligible
        if raw_metrics.spread_pct is not None
    ]
    depth_values = [raw_metrics.depth_2pct_quote for raw_metrics in eligible]
    slippage_values = []
    for raw_metrics in eligible:
        _trade_size, slippage_pct = resolve_slippage_display(raw_metrics.slippage)
        if slippage_pct is not None:
            slippage_values.append(slippage_pct)
    volume_depth_ratios = [
        raw_metrics.volume_depth_ratio
        for raw_metrics in eligible
        if raw_metrics.volume_depth_ratio is not None
    ]
    volume_values = [
        raw_metrics.volume_quote
        for raw_metrics in eligible
        if raw_metrics.volume_quote is not None
    ]
    return {
        "exchange_avg_spread_pct": _median_or_none(spread_values),
        "exchange_avg_depth_2pct": _median_or_none(depth_values),
        "exchange_avg_slippage_10k": _median_or_none(slippage_values),
        "exchange_median_volume_depth_ratio": _median_or_none(volume_depth_ratios),
        "exchange_median_volume_quote": _median_or_none(volume_values),
    }


def listings_share_quote(left_symbol: str, right_symbol: str) -> bool:
    if "/" not in left_symbol or "/" not in right_symbol:
        return False
    return left_symbol.split("/", 1)[1] == right_symbol.split("/", 1)[1]


def resolve_peer_volume(raw_metrics: ExtendedRawMetrics) -> float:
    if raw_metrics.volume_quote is not None and raw_metrics.volume_quote > 0:
        return raw_metrics.volume_quote
    bid_volume = raw_metrics.bid_volume_quote
    ask_volume = raw_metrics.ask_volume_quote
    if bid_volume is not None and ask_volume is not None:
        side_volume_total = bid_volume + ask_volume
        if side_volume_total > 0:
            return side_volume_total
    return 0.0


def _is_micro_volume(volume: float, min_relevant_usdt_volume: float) -> bool:
    return volume < min_relevant_usdt_volume


def _volume_within_tier(
    target_volume: float,
    candidate_volume: float,
    max_tier_ratio: float,
) -> bool:
    if target_volume <= 0 or candidate_volume <= 0:
        return False
    ratio = max(target_volume, candidate_volume) / min(target_volume, candidate_volume)
    return ratio <= max_tier_ratio


def _volume_tier_label(max_ratio_used: float) -> str:
    if max_ratio_used <= 5:
        return "volume_5x"
    if max_ratio_used <= 20:
        return "volume_20x"
    return "volume_100x"


def _resolve_market_cap_usd(
    symbol: str,
    market_cap_by_symbol: typing.Optional[dict[str, typing.Optional[float]]],
) -> typing.Optional[float]:
    if market_cap_by_symbol is None:
        return None
    market_cap = market_cap_by_symbol.get(symbol)
    if market_cap is None or market_cap <= 0:
        return None
    return market_cap


def _is_unknown_market_cap_peer(
    raw_metrics: ExtendedRawMetrics,
    market_cap_by_symbol: typing.Optional[dict[str, typing.Optional[float]]],
    min_relevant_usdt_volume: float,
) -> bool:
    if _resolve_market_cap_usd(raw_metrics.symbol, market_cap_by_symbol) is not None:
        return False
    return _is_micro_volume(resolve_peer_volume(raw_metrics), min_relevant_usdt_volume)


def _marketcap_log_distance(left_market_cap: float, right_market_cap: float) -> float:
    return abs(math.log(left_market_cap) - math.log(right_market_cap))


def _same_quote_candidates(
    target: ExtendedRawMetrics,
    universe: list[ExtendedRawMetrics],
    excluded_symbols: set[str],
) -> list[ExtendedRawMetrics]:
    return [
        raw_metrics
        for raw_metrics in universe
        if raw_metrics.symbol != target.symbol
        and raw_metrics.symbol not in excluded_symbols
        and listings_share_quote(target.symbol, raw_metrics.symbol)
    ]


def select_peer_symbols_with_fallback(
    target: ExtendedRawMetrics,
    universe: list[ExtendedRawMetrics],
    settings: PeerSelectionSettings,
    market_cap_by_symbol: typing.Optional[dict[str, typing.Optional[float]]] = None,
) -> tuple[list[ExtendedRawMetrics], str, str]:
    target_volume = resolve_peer_volume(target)
    selected: list[ExtendedRawMetrics] = []
    selected_symbols: set[str] = set()
    tier = "none"
    max_volume_ratio_used = 0.0

    def add_peers(candidates: list[ExtendedRawMetrics]) -> None:
        for candidate in candidates:
            if len(selected) >= settings.peer_count:
                return
            if candidate.symbol in selected_symbols:
                continue
            selected.append(candidate)
            selected_symbols.add(candidate.symbol)

    if _is_micro_volume(target_volume, settings.min_relevant_usdt_volume):
        micro_candidates = [
            candidate
            for candidate in _same_quote_candidates(target, universe, selected_symbols)
            if _is_micro_volume(resolve_peer_volume(candidate), settings.min_relevant_usdt_volume)
        ]
        micro_candidates.sort(key=lambda raw_metrics: raw_metrics.liquidity_score, reverse=True)
        if micro_candidates:
            add_peers(micro_candidates)
            tier = "volume_micro_bucket"

    if (
        not _is_micro_volume(target_volume, settings.min_relevant_usdt_volume)
        and len(selected) < settings.peer_count
    ):
        for tier_ratio in settings.peer_volume_tier_ratios:
            if len(selected) >= settings.peer_count:
                break
            tier_candidates = [
                candidate
                for candidate in _same_quote_candidates(target, universe, selected_symbols)
                if not _is_micro_volume(resolve_peer_volume(candidate), settings.min_relevant_usdt_volume)
                and _volume_within_tier(
                    target_volume,
                    resolve_peer_volume(candidate),
                    tier_ratio,
                )
            ]
            tier_candidates.sort(key=lambda raw_metrics: raw_metrics.liquidity_score, reverse=True)
            before_count = len(selected)
            add_peers(tier_candidates)
            if len(selected) > before_count:
                max_volume_ratio_used = max(max_volume_ratio_used, tier_ratio)
        if max_volume_ratio_used > 0:
            tier = _volume_tier_label(max_volume_ratio_used)

    if len(selected) < settings.peer_count:
        target_market_cap = _resolve_market_cap_usd(target.symbol, market_cap_by_symbol)
        if target_market_cap is not None:
            market_cap_candidates = [
                candidate
                for candidate in _same_quote_candidates(target, universe, selected_symbols)
                if _resolve_market_cap_usd(candidate.symbol, market_cap_by_symbol) is not None
            ]
            market_cap_candidates.sort(
                key=lambda raw_metrics: (
                    _marketcap_log_distance(
                        target_market_cap,
                        _resolve_market_cap_usd(raw_metrics.symbol, market_cap_by_symbol) or 0.0,
                    ),
                    -raw_metrics.liquidity_score,
                ),
            )
            before_count = len(selected)
            add_peers(market_cap_candidates)
            if len(selected) > before_count:
                tier = "marketcap_closest"
        else:
            unknown_cap_candidates = [
                candidate
                for candidate in _same_quote_candidates(target, universe, selected_symbols)
                if _is_unknown_market_cap_peer(
                    candidate,
                    market_cap_by_symbol,
                    settings.min_relevant_usdt_volume,
                )
            ]
            unknown_cap_candidates.sort(key=lambda raw_metrics: raw_metrics.liquidity_score, reverse=True)
            before_count = len(selected)
            add_peers(unknown_cap_candidates)
            if len(selected) > before_count:
                tier = "marketcap_closest"

    if len(selected) < settings.peer_count:
        liquidity_score_candidates = _same_quote_candidates(target, universe, selected_symbols)
        liquidity_score_candidates.sort(key=lambda raw_metrics: raw_metrics.liquidity_score, reverse=True)
        before_count = len(selected)
        add_peers(liquidity_score_candidates)
        if len(selected) > before_count:
            tier = "liquidity_score"

    if not selected:
        tier = "none"

    return selected, tier, PEER_TIER_CRITERIA[tier]


def _volume_in_same_tier(
    target_volume: typing.Optional[float],
    candidate_volume: typing.Optional[float],
) -> bool:
    if target_volume is None or candidate_volume is None:
        return False
    if target_volume <= 0 or candidate_volume <= 0:
        return False
    ratio = max(target_volume, candidate_volume) / min(target_volume, candidate_volume)
    return ratio <= VOLUME_TIER_RATIO


def select_peer_symbols(
    target: ExtendedRawMetrics,
    universe: list[ExtendedRawMetrics],
    peer_count: int = PEER_COUNT,
) -> list[ExtendedRawMetrics]:
    settings = PeerSelectionSettings(
        min_relevant_usdt_volume=0.0,
        peer_volume_tier_ratios=(VOLUME_TIER_RATIO,),
        peer_count=peer_count,
    )
    peers, _, _ = select_peer_symbols_with_fallback(target, universe, settings)
    return peers


def peer_row_from_raw(raw_metrics: ExtendedRawMetrics, is_yours: bool) -> dict[str, typing.Any]:
    slippage_trade_size, slippage_pct = resolve_slippage_display(raw_metrics.slippage)
    return {
        "name": raw_metrics.symbol,
        "spread": raw_metrics.spread_pct if raw_metrics.spread_pct is not None else 0.0,
        "depth": raw_metrics.depth_2pct_quote,
        "slippage_trade_size": slippage_trade_size,
        "slippage_pct": slippage_pct,
        "is_yours": is_yours,
    }


def build_peer_median(
    peer_rows: list[dict[str, typing.Any]],
) -> typing.Optional[dict[str, typing.Any]]:
    non_yours = [row for row in peer_rows if not row.get("is_yours")]
    if not non_yours:
        return None
    return {
        "name": "Median",
        "spread": _median_or_none([row["spread"] for row in non_yours]) or 0.0,
        "depth": _median_or_none([row["depth"] for row in non_yours]) or 0.0,
        "slippage_trade_size": None,
        "slippage_pct": _median_or_none(
            [row["slippage_pct"] for row in non_yours if row.get("slippage_pct") is not None]
        ),
        "is_yours": False,
    }


def _clamp_unit_score(value: float) -> float:
    return max(0.0, min(1.0, value))


def _peer_metric_score(ratio: float) -> float:
    if ratio >= PEER_METRIC_DEADBAND:
        return 1.0
    return _clamp_unit_score(ratio)


def peer_median_for_target(
    target: ExtendedRawMetrics,
    universe: list[ExtendedRawMetrics],
    *,
    settings: typing.Optional[PeerSelectionSettings] = None,
    market_cap_by_symbol: typing.Optional[dict[str, typing.Optional[float]]] = None,
) -> typing.Optional[dict[str, typing.Any]]:
    peer_selection_settings = settings or default_peer_selection_settings()
    peer_candidates, _, _ = select_peer_symbols_with_fallback(
        target,
        universe,
        peer_selection_settings,
        market_cap_by_symbol,
    )
    if not peer_candidates:
        return None
    peer_rows = [peer_row_from_raw(peer, is_yours=False) for peer in peer_candidates]
    return build_peer_median(peer_rows)


def compute_peer_relative_score(
    raw_metrics: ExtendedRawMetrics,
    peer_median: dict[str, typing.Any],
) -> typing.Optional[float]:
    metric_scores: list[float] = []

    peer_depth = peer_median.get("depth")
    if peer_depth is not None and peer_depth > 0:
        depth_ratio = raw_metrics.depth_2pct_quote / peer_depth
        metric_scores.append(_peer_metric_score(depth_ratio))

    peer_spread = peer_median.get("spread")
    if (
        peer_spread is not None
        and peer_spread > 0
        and raw_metrics.spread_pct is not None
        and raw_metrics.spread_pct > 0
    ):
        metric_scores.append(_peer_metric_score(peer_spread / raw_metrics.spread_pct))

    _trade_size, slippage_pct = resolve_slippage_display(raw_metrics.slippage)
    peer_slippage_pct = peer_median.get("slippage_pct")
    if (
        slippage_pct is not None
        and slippage_pct > 0
        and peer_slippage_pct is not None
        and peer_slippage_pct > 0
    ):
        metric_scores.append(_peer_metric_score(peer_slippage_pct / slippage_pct))

    if not metric_scores:
        return None
    return sum(metric_scores) / len(metric_scores)


def compute_composite_score(
    raw_metrics: ExtendedRawMetrics,
    universe: list[ExtendedRawMetrics],
    *,
    settings: typing.Optional[PeerSelectionSettings] = None,
    market_cap_by_symbol: typing.Optional[dict[str, typing.Optional[float]]] = None,
) -> tuple[float, typing.Optional[float]]:
    internal_score = raw_metrics.liquidity_score
    peer_median = peer_median_for_target(
        raw_metrics,
        universe,
        settings=settings,
        market_cap_by_symbol=market_cap_by_symbol,
    )
    if peer_median is None:
        return internal_score, None
    peer_relative_score = compute_peer_relative_score(raw_metrics, peer_median)
    if peer_relative_score is None:
        return internal_score, None
    return (internal_score + peer_relative_score) / 2, peer_relative_score


def compute_score_100(
    raw_metrics: ExtendedRawMetrics,
    universe: list[ExtendedRawMetrics],
    *,
    settings: typing.Optional[PeerSelectionSettings] = None,
    market_cap_by_symbol: typing.Optional[dict[str, typing.Optional[float]]] = None,
) -> tuple[int, int, typing.Optional[int]]:
    internal_score = raw_metrics.liquidity_score
    composite_score, peer_relative_score = compute_composite_score(
        raw_metrics,
        universe,
        settings=settings,
        market_cap_by_symbol=market_cap_by_symbol,
    )
    internal_100 = round(internal_score * 100)
    peer_relative_100 = (
        None if peer_relative_score is None else round(peer_relative_score * 100)
    )
    return round(composite_score * 100), internal_100, peer_relative_100


def _has_label(raw_metrics: ExtendedRawMetrics, label_id: str) -> bool:
    if raw_metrics.health_label_primary == label_id:
        return True
    return label_id in raw_metrics.health_labels_other


def detect_mm_presence(
    raw_metrics: ExtendedRawMetrics,
    health_labels: app_config.HealthLabelsConfig,
) -> dict[str, typing.Any]:
    if _has_label(raw_metrics, health_evaluation.LABEL_WIDE_SPREAD):
        return {"detected": False, "label": "Not detected"}
    if raw_metrics.spread_pct is None or raw_metrics.spread_pct >= 1.0:
        return {"detected": False, "label": "Not detected"}
    if raw_metrics.bid_levels < health_labels.few_orders.min_bid_levels:
        return {"detected": False, "label": "Not detected"}
    if raw_metrics.ask_levels < health_labels.few_orders.min_ask_levels:
        return {"detected": False, "label": "Not detected"}
    depth_max = max(raw_metrics.bid_depth_1pct_quote, raw_metrics.ask_depth_1pct_quote)
    if depth_max <= 0:
        return {"detected": False, "label": "Not detected"}
    depth_symmetry = min(raw_metrics.bid_depth_1pct_quote, raw_metrics.ask_depth_1pct_quote) / depth_max
    if depth_symmetry < 0.4:
        return {"detected": False, "label": "Not detected"}
    return {"detected": True, "label": "Detected"}


def _format_usd_short(value: float) -> str:
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1000:
        return f"${value / 1000:.1f}k"
    return f"${value:.0f}"


def _comparison_impact_text(ratio: float, *, higher_is_worse: bool) -> str:
    if higher_is_worse:
        if ratio <= 0.01:
            return "Better than average"
        if ratio < 0.75:
            return f"{1 / ratio:.1f}× better than average"
        if ratio <= 1.0:
            return "At or better than average"
        if ratio < 1.5:
            return "Near average"
        if ratio < 2.0:
            return f"{ratio:.1f}× above average"
        return f"{ratio:.1f}× worse than average"
    if ratio >= 1.25:
        if ratio >= 2.0:
            return f"{ratio:.1f}× above average"
        return "Above average"
    if ratio >= 1.0:
        return "At or above average"
    if ratio >= 0.67:
        return "Near average"
    return f"{(1 - ratio) * 100:.0f}% below average"


def _spread_impact_text(ratio: float) -> str:
    if ratio <= 0.01:
        return "Tighter than average"
    if ratio < 0.75:
        return f"{1 / ratio:.1f}× tighter than average"
    if ratio <= 1.0:
        return "At or tighter than average"
    if ratio < 1.5:
        return "Near average"
    if ratio < 2.0:
        return f"{ratio:.1f}× wider than average"
    return f"{ratio:.1f}× wider than average"


def _ratio_severity(ratio: float, higher_is_worse: bool) -> str:
    if higher_is_worse:
        if ratio >= 2.0:
            return "Critical"
        if ratio >= 1.5:
            return "Moderate"
        return "Low"
    if ratio <= 0.5:
        return "Critical"
    if ratio <= 0.67:
        return "Moderate"
    return "Low"


def _passes_core_liquidity_checks_for_volume_exempt(
    raw_metrics: ExtendedRawMetrics,
    exchange_averages: dict[str, typing.Optional[float]],
) -> bool:
    if raw_metrics.liquidity_score < HIGH_LIQUIDITY_SCORE_FOR_VOLUME_EXEMPT:
        return False

    checks_run = 0
    checks_passed = 0

    avg_spread = exchange_averages.get("exchange_avg_spread_pct")
    if raw_metrics.spread_pct is not None and avg_spread is not None and avg_spread > 0:
        checks_run += 1
        spread_ratio = raw_metrics.spread_pct / avg_spread
        if _ratio_severity(spread_ratio, higher_is_worse=True) == "Low":
            checks_passed += 1

    avg_depth = exchange_averages.get("exchange_avg_depth_2pct")
    if avg_depth is not None and avg_depth > 0:
        checks_run += 1
        depth_ratio = raw_metrics.depth_2pct_quote / avg_depth
        if _ratio_severity(depth_ratio, higher_is_worse=False) == "Low":
            checks_passed += 1

    slippage_10k = slippage_pct_at_size(raw_metrics.slippage, 10_000)
    avg_slippage = exchange_averages.get("exchange_avg_slippage_10k")
    if slippage_10k is not None and avg_slippage is not None and avg_slippage > 0:
        checks_run += 1
        slippage_ratio = slippage_10k / avg_slippage
        if _ratio_severity(slippage_ratio, higher_is_worse=True) == "Low":
            checks_passed += 1

    return checks_run > 0 and checks_passed == checks_run


def _volume_consistency_severity_and_impact(
    raw_metrics: ExtendedRawMetrics,
    exchange_averages: dict[str, typing.Optional[float]],
) -> tuple[str, str]:
    hollow = raw_metrics.volume_depth_ratio > HOLLOW_VOLUME_RATIO_THRESHOLD
    if not hollow:
        return "Low", "Within normal range"
    if _passes_core_liquidity_checks_for_volume_exempt(raw_metrics, exchange_averages):
        return "Low", "Within normal range"
    return "Critical", "Hollow volume risk"


def build_health_dashboard(
    raw_metrics: ExtendedRawMetrics,
    exchange_averages: dict[str, typing.Optional[float]],
) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []

    avg_spread = exchange_averages.get("exchange_avg_spread_pct")
    if raw_metrics.spread_pct is not None and avg_spread is not None and avg_spread > 0:
        ratio = raw_metrics.spread_pct / avg_spread
        cards.append({
            "severity": _ratio_severity(ratio, higher_is_worse=True),
            "title": "Spread",
            "impact": _spread_impact_text(ratio),
            "evidence": f"{raw_metrics.spread_pct:.2f}% vs {avg_spread:.2f}% avg",
        })

    avg_depth = exchange_averages.get("exchange_avg_depth_2pct")
    if avg_depth is not None and avg_depth > 0:
        ratio = raw_metrics.depth_2pct_quote / avg_depth
        depth_note = " (visible book)" if raw_metrics.depth_2pct_capped else ""
        cards.append({
            "severity": _ratio_severity(ratio, higher_is_worse=False),
            "title": "Depth ±2%",
            "impact": f"{(1 - ratio) * 100:.0f}% below average" if ratio < 1 else "At or above average",
            "evidence": f"{_format_usd_short(raw_metrics.depth_2pct_quote)}{depth_note} vs "
            f"{_format_usd_short(avg_depth)} avg",
        })

    slippage_trade_size, slippage_pct = resolve_slippage_display(raw_metrics.slippage)
    avg_slippage = exchange_averages.get("exchange_avg_slippage_10k")
    if slippage_pct is not None and avg_slippage is not None and avg_slippage > 0:
        ratio = slippage_pct / avg_slippage
        cards.append({
            "severity": _ratio_severity(ratio, higher_is_worse=True),
            "title": slippage_metric_title(slippage_trade_size),
            "impact": _comparison_impact_text(ratio, higher_is_worse=True),
            "evidence": f"{slippage_pct:.2f}% vs {avg_slippage:.2f}% avg",
        })

    median_vol_depth = exchange_averages.get("exchange_median_volume_depth_ratio")
    if raw_metrics.volume_depth_ratio is not None:
        volume_severity, volume_impact = _volume_consistency_severity_and_impact(
            raw_metrics,
            exchange_averages,
        )
        evidence = f"Vol/depth {raw_metrics.volume_depth_ratio:.1f}×"
        if median_vol_depth is not None:
            evidence += f" vs {median_vol_depth:.1f}× median"
        cards.append({
            "severity": volume_severity,
            "title": "Volume consistency",
            "impact": volume_impact,
            "evidence": evidence,
        })

    return cards


def qualifies_for_perfect_score(
    raw_metrics: ExtendedRawMetrics,
    issues: list[dict[str, typing.Any]],
    health_dashboard: list[dict[str, str]],
) -> bool:
    if raw_metrics.is_low_health:
        return False
    if not issues or not all(issue.get("ok") for issue in issues):
        return False
    if not health_dashboard:
        return False
    return all(row.get("severity") == "Low" for row in health_dashboard)


def build_issues(
    raw_metrics: ExtendedRawMetrics,
    exchange_averages: dict[str, typing.Optional[float]],
    peer_median_slippage_pct: typing.Optional[float],
    health_labels: app_config.HealthLabelsConfig,
) -> list[dict[str, typing.Any]]:
    median_volume = exchange_averages.get("exchange_median_volume_quote")
    good_volume = (
        raw_metrics.volume_quote is not None
        and median_volume is not None
        and raw_metrics.volume_quote >= median_volume
    )
    _slippage_trade_size, slippage_pct = resolve_slippage_display(raw_metrics.slippage)
    high_slippage = True
    if slippage_pct is None:
        high_slippage = False
    elif peer_median_slippage_pct is not None and peer_median_slippage_pct > 0:
        high_slippage = slippage_pct >= peer_median_slippage_pct * 2

    return [
        {"label": "Good volume", "ok": good_volume},
        {"label": "Wide spread", "ok": not _has_label(raw_metrics, health_evaluation.LABEL_WIDE_SPREAD)},
        {
            "label": "Low depth",
            "ok": not (
                _has_label(raw_metrics, health_evaluation.LABEL_SHALLOW_LIQUIDITY)
                or _has_label(raw_metrics, health_evaluation.LABEL_SHALLOW_TOTAL_DEPTH)
            ),
        },
        {"label": "High slippage", "ok": not high_slippage},
        {
            "label": "Quote gaps",
            "ok": (
                raw_metrics.bid_levels >= health_labels.few_orders.min_bid_levels
                and raw_metrics.ask_levels >= health_labels.few_orders.min_ask_levels
            ),
        },
    ]


def build_verdict(
    raw_metrics: ExtendedRawMetrics,
    exchange_averages: dict[str, typing.Optional[float]],
) -> str:
    slippage_trade_size, slippage_pct = resolve_slippage_display(raw_metrics.slippage)
    avg_slippage = exchange_averages.get("exchange_avg_slippage_10k")
    if slippage_pct is not None and avg_slippage is not None and avg_slippage > 0:
        ratio = slippage_pct / avg_slippage
        size_label = format_slippage_trade_size_label(slippage_trade_size)
        if ratio <= 1.0:
            return (
                f"{raw_metrics.symbol} executes a {size_label} buy with ~{slippage_pct:.2f}% slippage — "
                f"at or better than {raw_metrics.exchange} average."
            )
        if ratio < 2.0:
            return (
                f"{raw_metrics.symbol} loses ~{slippage_pct:.2f}% on a {size_label} buy — "
                f"slightly above {raw_metrics.exchange} average slippage."
            )
        return (
            f"{raw_metrics.symbol} loses ~{slippage_pct:.1f}% on a {size_label} buy — "
            f"{ratio:.0f}× worse than {raw_metrics.exchange} average."
        )
    spread_text = f"{raw_metrics.spread_pct:.1f}%" if raw_metrics.spread_pct is not None else "wide"
    return (
        f"{raw_metrics.symbol} has {spread_text} spread and only "
        f"{_format_usd_short(raw_metrics.max_fillable_buy_quote)} visible ask liquidity — "
        f"large buys are likely impractical on {raw_metrics.exchange}."
    )


def _select_investor_simulator_rows(
    rows: list[dict[str, typing.Any]],
    max_cards: int = INVESTOR_SIMULATOR_MAX_CARDS,
) -> list[dict[str, typing.Any]]:
    fillable_rows = sorted(
        [row for row in rows if not row.get("omitted")],
        key=lambda row: row["size"],
        reverse=True,
    )
    omitted_rows = sorted(
        [row for row in rows if row.get("omitted")],
        key=lambda row: row["size"],
        reverse=True,
    )
    selected_rows = fillable_rows[:max_cards]
    remaining_card_count = max_cards - len(selected_rows)
    if remaining_card_count > 0:
        omitted_rows_ascending = sorted(omitted_rows, key=lambda row: row["size"])
        selected_rows.extend(omitted_rows_ascending[:remaining_card_count])
    selected_rows.sort(key=lambda row: row["size"], reverse=True)
    return selected_rows


def build_investor_simulator(
    raw_metrics: ExtendedRawMetrics,
) -> list[dict[str, typing.Any]]:
    if raw_metrics.mid_price is None:
        return []
    rows: list[dict[str, typing.Any]] = []
    for slippage_row in raw_metrics.slippage:
        trade_size = slippage_row["size"]
        if slippage_row.get("omitted"):
            fill_ratio = slippage_row.get("fill_ratio")
            rows.append({
                "size": trade_size,
                "omitted": True,
                "fill_ratio": fill_ratio,
                "highlight": False,
            })
            continue
        slippage_pct = slippage_row["pct"]
        if slippage_pct is None:
            continue
        overpay_usd = trade_size * slippage_pct / 100
        average_price = raw_metrics.mid_price * (1 + slippage_pct / 100)
        rows.append({
            "size": trade_size,
            "omitted": False,
            "overpay_pct": round(slippage_pct, 2),
            "overpay_usd": round(overpay_usd, 2),
            "fair_price": raw_metrics.mid_price,
            "avg_price": average_price,
            "highlight": False,
        })
    display_trade_size, _display_slippage_pct = resolve_slippage_display(raw_metrics.slippage)
    highlight_size = display_trade_size
    if highlight_size is None and rows:
        highlight_size = rows[-1]["size"]
    for row in rows:
        if row["size"] == highlight_size:
            row["highlight"] = True
    return _select_investor_simulator_rows(rows)


def build_lost_opportunity(raw_metrics: ExtendedRawMetrics) -> dict[str, typing.Any]:
    trade_size, slippage_pct = resolve_slippage_display(raw_metrics.slippage)
    if trade_size is None or slippage_pct is None:
        return {
            "size": 0,
            "cost": 0,
            "range": "",
            "note": "Insufficient visible liquidity for institutional-size entries.",
        }
    cost = trade_size * slippage_pct / 100
    non_omitted_pcts = [
        row["pct"] for row in raw_metrics.slippage if not row.get("omitted") and row.get("pct") is not None
    ]
    if len(non_omitted_pcts) >= 2:
        range_text = f"{min(non_omitted_pcts):.1f}–{max(non_omitted_pcts):.1f}%"
    elif non_omitted_pcts:
        range_text = f"{non_omitted_pcts[0]:.1f}%"
    else:
        range_text = ""
    return {
        "size": trade_size,
        "cost": round(cost, 2),
        "range": range_text,
    }


def _depth_asymmetry(raw_metrics: ExtendedRawMetrics) -> float:
    total = raw_metrics.bid_depth_1pct_quote + raw_metrics.ask_depth_1pct_quote
    if total <= 0:
        return 0.0
    return abs(raw_metrics.bid_depth_1pct_quote - raw_metrics.ask_depth_1pct_quote) / total


def build_root_causes(
    raw_metrics: ExtendedRawMetrics,
    peer_median_depth: typing.Optional[float],
) -> list[dict[str, str]]:
    causes: list[dict[str, str]] = []
    liquidity_trigger = (
        _has_label(raw_metrics, health_evaluation.LABEL_SHALLOW_LIQUIDITY)
        or _has_label(raw_metrics, health_evaluation.LABEL_SHALLOW_TOTAL_DEPTH)
        or raw_metrics.max_fillable_buy_quote < 5000
    )
    if liquidity_trigger:
        if peer_median_depth is not None:
            depth_evidence = (
                f"Depth ±2% at {_format_usd_short(raw_metrics.depth_2pct_quote)}"
                f" vs {_format_usd_short(peer_median_depth)} peer median"
            )
        else:
            depth_evidence = (
                f"Depth ±2% at {_format_usd_short(raw_metrics.depth_2pct_quote)}"
                " vs no comparable peers"
            )
        slippage_trade_size, slippage_pct = resolve_slippage_display(raw_metrics.slippage)
        if slippage_pct is not None:
            size_label = format_slippage_trade_size_label(slippage_trade_size)
            impact = f"{size_label} buys move price {slippage_pct:.0f}%+"
        else:
            impact = "Large orders move price significantly"
        causes.append({
            "rank": "1",
            "title": "Insufficient resting liquidity",
            "evidence": depth_evidence,
            "impact": impact,
        })

    imbalance_trigger = (
        (raw_metrics.sell_volume_pct is not None and raw_metrics.sell_volume_pct > VOLUME_SKEW_THRESHOLD)
        or (raw_metrics.buy_volume_pct is not None and raw_metrics.buy_volume_pct > VOLUME_SKEW_THRESHOLD)
        or _depth_asymmetry(raw_metrics) > DEPTH_ASYMMETRY_THRESHOLD
    )
    if imbalance_trigger:
        skew_text = (
            f"{raw_metrics.sell_volume_pct:.0f}% sell-side volume in 24h"
            if raw_metrics.sell_volume_pct is not None and raw_metrics.sell_volume_pct >= (
                raw_metrics.buy_volume_pct or 0
            )
            else f"{raw_metrics.buy_volume_pct:.0f}% buy-side volume in 24h"
            if raw_metrics.buy_volume_pct is not None
            else "Order book depth asymmetry"
        )
        causes.append({
            "rank": str(len(causes) + 1),
            "title": "Order book imbalance",
            "evidence": skew_text,
            "impact": "Buyers face wider effective spread",
        })
    return causes[:2]


def build_improvements(
    raw_metrics: ExtendedRawMetrics,
    peer_median: typing.Optional[dict[str, typing.Any]],
) -> list[dict[str, str]]:
    slippage_trade_size, slippage_pct = resolve_slippage_display(raw_metrics.slippage)
    if peer_median is None:
        return [
            {
                "metric": "Spread",
                "current": f"{raw_metrics.spread_pct:.1f}%" if raw_metrics.spread_pct is not None else "—",
                "potential": "—",
            },
            {
                "metric": "Depth ±2%",
                "current": _format_usd_short(raw_metrics.depth_2pct_quote),
                "potential": "—",
            },
            {
                "metric": slippage_metric_title(slippage_trade_size),
                "current": f"{slippage_pct:.1f}%" if slippage_pct is not None else "—",
                "potential": "—",
            },
        ]
    return [
        {
            "metric": "Spread",
            "current": f"{raw_metrics.spread_pct:.1f}%" if raw_metrics.spread_pct is not None else "—",
            "potential": f"{peer_median['spread']:.1f}%",
        },
        {
            "metric": "Depth ±2%",
            "current": _format_usd_short(raw_metrics.depth_2pct_quote),
            "potential": _format_usd_short(peer_median["depth"]),
        },
        {
            "metric": slippage_metric_title(slippage_trade_size),
            "current": f"{slippage_pct:.1f}%" if slippage_pct is not None else "—",
            "potential": (
                f"{peer_median['slippage_pct']:.1f}%"
                if peer_median.get("slippage_pct") is not None
                else "—"
            ),
        },
    ]


def build_roadmap(
    raw_metrics: ExtendedRawMetrics,
    peer_median: typing.Optional[dict[str, typing.Any]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if peer_median is None:
        return rows
    if _has_label(raw_metrics, health_evaluation.LABEL_WIDE_SPREAD):
        spread_delta = (raw_metrics.spread_pct or 0) - peer_median["spread"]
        rows.append({
            "issue": "Wide spread",
            "fix": "Resting orders both sides",
            "cost": "Low–Med",
            "impact": f"−{max(spread_delta, 0):.1f}% spread",
        })
    if _has_label(raw_metrics, health_evaluation.LABEL_SHALLOW_LIQUIDITY):
        depth_delta = peer_median["depth"] - raw_metrics.depth_2pct_quote
        rows.append({
            "issue": "Low depth",
            "fix": "Depth injection program",
            "cost": "Med",
            "impact": f"+{_format_usd_short(max(depth_delta, 0))} depth",
        })
    if _has_label(raw_metrics, health_evaluation.LABEL_FEW_ORDERS):
        rows.append({
            "issue": "Quote gaps",
            "fix": "Continuous quoting",
            "cost": "Low",
            "impact": "Both sides quoted at snapshot",
        })
    return rows


def _rankings_volume_quote(raw_metrics: ExtendedRawMetrics) -> float:
    if raw_metrics.volume_quote is None:
        return 0.0
    return raw_metrics.volume_quote


def _is_rankings_volume_eligible(
    raw_metrics: ExtendedRawMetrics,
    rankings_min_volume_quote: float,
) -> bool:
    return (
        raw_metrics.volume_quote is not None
        and raw_metrics.volume_quote >= rankings_min_volume_quote
    )


def build_rankings(
    raw_metrics_list: list[ExtendedRawMetrics],
    rankings_min_volume_quote: float,
) -> list[dict[str, typing.Any]]:
    sorted_metrics = sorted(
        raw_metrics_list,
        key=lambda raw_metrics: (
            compute_score_100(raw_metrics, raw_metrics_list)[0],
            _rankings_volume_quote(raw_metrics),
        ),
        reverse=True,
    )
    eligible_rank = 0
    rankings: list[dict[str, typing.Any]] = []
    for raw_metrics in sorted_metrics:
        score_100, _, _ = compute_score_100(raw_metrics, raw_metrics_list)
        rank: typing.Optional[int] = None
        if _is_rankings_volume_eligible(raw_metrics, rankings_min_volume_quote):
            eligible_rank += 1
            rank = eligible_rank
        rankings.append({
            "symbol": raw_metrics.symbol,
            "score_100": score_100,
            "volume_quote": _rankings_volume_quote(raw_metrics),
            "rank": rank,
        })
    return rankings


def build_pair_analysis(
    raw_metrics: ExtendedRawMetrics,
    universe: list[ExtendedRawMetrics],
    exchange_averages: dict[str, typing.Optional[float]],
    health_labels: app_config.HealthLabelsConfig,
    delisting_risk_cards: typing.Optional[list[dict[str, str]]] = None,
    *,
    peer_selection_settings: typing.Optional[PeerSelectionSettings] = None,
    market_cap_by_symbol: typing.Optional[dict[str, typing.Optional[float]]] = None,
) -> dict[str, typing.Any]:
    selection_settings = peer_selection_settings or default_peer_selection_settings()
    score_100, internal_100, peer_relative_100 = compute_score_100(
        raw_metrics,
        universe,
        settings=selection_settings,
        market_cap_by_symbol=market_cap_by_symbol,
    )
    mm_presence = detect_mm_presence(raw_metrics, health_labels)

    peer_candidates, peer_tier, peer_criteria = select_peer_symbols_with_fallback(
        raw_metrics,
        universe,
        selection_settings,
        market_cap_by_symbol,
    )
    peer_rows = [peer_row_from_raw(raw_metrics, is_yours=True)]
    peer_rows.extend(peer_row_from_raw(peer, is_yours=False) for peer in peer_candidates)
    peer_median = build_peer_median(peer_rows)
    if peer_median is not None:
        peer_rows.append(peer_median)
    display_slippage_trade_size, _display_slippage_pct = resolve_slippage_display(raw_metrics.slippage)

    issues = build_issues(
        raw_metrics,
        exchange_averages,
        peer_median.get("slippage_pct") if peer_median is not None else None,
        health_labels,
    )
    health_dashboard = build_health_dashboard(raw_metrics, exchange_averages)
    if qualifies_for_perfect_score(raw_metrics, issues, health_dashboard):
        score_100 = 100
    status = score_to_status(score_100, raw_metrics.is_low_health)

    score_breakdown: dict[str, typing.Optional[int]] = {
        "internal_100": internal_100,
        "peer_relative_100": peer_relative_100,
    }

    return {
        "exchange": raw_metrics.exchange,
        "symbol": raw_metrics.symbol,
        "full_name": raw_metrics.full_name,
        "raw": raw_metrics.to_dict(),
        "analysis": {
            "score_100": score_100,
            "score_breakdown": score_breakdown,
            "grade": score_to_grade(score_100),
            "status": status,
            "status_class": status_to_class(status),
            "slippage_display_size": display_slippage_trade_size,
            "verdict": build_verdict(raw_metrics, exchange_averages),
            "issues": issues,
            "health_dashboard": health_dashboard,
            "delisting_risk": delisting_risk_cards or [],
            "mm_presence": mm_presence,
            "peers": {
                "tier": peer_tier,
                "criteria": peer_criteria,
                "rows": peer_rows,
                "median": peer_median,
            },
            "investor_simulator": build_investor_simulator(raw_metrics),
            "lost_opportunity": build_lost_opportunity(raw_metrics),
            "root_causes": build_root_causes(
                raw_metrics,
                peer_median["depth"] if peer_median is not None else None,
            ),
            "improvements": build_improvements(raw_metrics, peer_median),
            "roadmap": build_roadmap(raw_metrics, peer_median),
        },
    }
