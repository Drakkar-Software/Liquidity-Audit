import dataclasses

import liquidity_audit.config._validators as config_validators


KNOWN_HEALTH_LABEL_IDS = frozenset({
    "few_orders",
    "shallow_liquidity",
    "wide_spread",
    "under_depth_for_volume",
    "fragmented_tight_depth",
    "shallow_total_depth",
    "low_liquidity_score",
})


@dataclasses.dataclass
class HealthRules:
    min_buy_orders: int
    min_sell_orders: int
    depth_band_pct: float
    larger_depth_band_pct: float


@dataclasses.dataclass
class UnhealthyValues:
    min_bid_levels: int
    min_ask_levels: int
    min_bid_depth_quote_usdt: float
    min_ask_depth_quote_usdt: float
    min_bid_larger_depth_quote_usdt: float
    min_ask_larger_depth_quote_usdt: float
    max_bid_ask_spread_pct: float
    min_bid_depth_volume_ratio: float
    min_ask_depth_volume_ratio: float
    min_bid_larger_depth_volume_ratio: float
    min_ask_larger_depth_volume_ratio: float


@dataclasses.dataclass
class FewOrdersLabelThresholds:
    min_bid_levels: int
    min_ask_levels: int


@dataclasses.dataclass
class ShallowLiquidityLabelThresholds:
    min_bid_larger_depth_quote_usdt: float
    min_ask_larger_depth_quote_usdt: float


@dataclasses.dataclass
class WideSpreadLabelThresholds:
    max_bid_ask_spread_pct: float


@dataclasses.dataclass
class UnderDepthForVolumeLabelThresholds:
    min_bid_depth_volume_ratio: float
    min_ask_depth_volume_ratio: float
    min_bid_larger_depth_volume_ratio: float
    min_ask_larger_depth_volume_ratio: float


@dataclasses.dataclass
class FragmentedTightDepthLabelThresholds:
    min_bid_depth_quote_usdt: float
    min_ask_depth_quote_usdt: float


@dataclasses.dataclass
class ShallowTotalDepthLabelThresholds:
    min_bid_total_depth_quote_usdt: float
    min_ask_total_depth_quote_usdt: float


@dataclasses.dataclass
class LowLiquidityScoreLabelThresholds:
    pass


@dataclasses.dataclass
class HealthLabelsConfig:
    priority: list[str]
    few_orders: FewOrdersLabelThresholds
    shallow_liquidity: ShallowLiquidityLabelThresholds
    wide_spread: WideSpreadLabelThresholds
    under_depth_for_volume: UnderDepthForVolumeLabelThresholds
    fragmented_tight_depth: FragmentedTightDepthLabelThresholds
    shallow_total_depth: ShallowTotalDepthLabelThresholds
    low_liquidity_score: LowLiquidityScoreLabelThresholds


def reject_deprecated_health_rule_keys(health_raw: dict) -> None:
    for deprecated_key in ("min_depth_quote_usdt", "max_bid_ask_spread_pct"):
        if deprecated_key in health_raw:
            raise config_validators.ConfigError(
                f"config key health_rules.{deprecated_key!r} is deprecated; "
                f"use unhealthy_values instead",
            )


def load_health_labels(health_labels_raw: dict) -> HealthLabelsConfig:
    if not isinstance(health_labels_raw, dict):
        raise config_validators.ConfigError("config key 'health_labels' must be an object")

    priority = health_labels_raw.get("priority")
    if not isinstance(priority, list) or not priority:
        raise config_validators.ConfigError("config key health_labels.priority must be a non-empty list")
    if len(priority) != len(set(priority)):
        raise config_validators.ConfigError("config key health_labels.priority must not contain duplicates")
    for label_id in priority:
        if not isinstance(label_id, str) or label_id not in KNOWN_HEALTH_LABEL_IDS:
            raise config_validators.ConfigError(
                f"config key health_labels.priority contains unknown label {label_id!r}",
            )

    for label_id in KNOWN_HEALTH_LABEL_IDS:
        label_raw = health_labels_raw.get(label_id)
        if label_id == "low_liquidity_score":
            if label_raw is None:
                raise config_validators.ConfigError("config key health_labels.low_liquidity_score is required")
            if not isinstance(label_raw, dict):
                raise config_validators.ConfigError("config key health_labels.low_liquidity_score must be an object")
            continue
        if not isinstance(label_raw, dict):
            raise config_validators.ConfigError(f"config key health_labels.{label_id} must be an object")

    few_orders_raw = health_labels_raw["few_orders"]
    shallow_liquidity_raw = health_labels_raw["shallow_liquidity"]
    wide_spread_raw = health_labels_raw["wide_spread"]
    under_depth_for_volume_raw = health_labels_raw["under_depth_for_volume"]
    fragmented_tight_depth_raw = health_labels_raw["fragmented_tight_depth"]
    shallow_total_depth_raw = health_labels_raw["shallow_total_depth"]

    return HealthLabelsConfig(
        priority=priority,
        few_orders=FewOrdersLabelThresholds(
            min_bid_levels=config_validators.require_positive_int(few_orders_raw, "min_bid_levels"),
            min_ask_levels=config_validators.require_positive_int(few_orders_raw, "min_ask_levels"),
        ),
        shallow_liquidity=ShallowLiquidityLabelThresholds(
            min_bid_larger_depth_quote_usdt=config_validators.require_positive_float(
                shallow_liquidity_raw, "min_bid_larger_depth_quote_usdt",
            ),
            min_ask_larger_depth_quote_usdt=config_validators.require_positive_float(
                shallow_liquidity_raw, "min_ask_larger_depth_quote_usdt",
            ),
        ),
        wide_spread=WideSpreadLabelThresholds(
            max_bid_ask_spread_pct=config_validators.require_positive_float(
                wide_spread_raw, "max_bid_ask_spread_pct",
            ),
        ),
        under_depth_for_volume=UnderDepthForVolumeLabelThresholds(
            min_bid_depth_volume_ratio=config_validators.require_non_negative_float(
                under_depth_for_volume_raw, "min_bid_depth_volume_ratio",
            ),
            min_ask_depth_volume_ratio=config_validators.require_non_negative_float(
                under_depth_for_volume_raw, "min_ask_depth_volume_ratio",
            ),
            min_bid_larger_depth_volume_ratio=config_validators.require_non_negative_float(
                under_depth_for_volume_raw, "min_bid_larger_depth_volume_ratio",
            ),
            min_ask_larger_depth_volume_ratio=config_validators.require_non_negative_float(
                under_depth_for_volume_raw, "min_ask_larger_depth_volume_ratio",
            ),
        ),
        fragmented_tight_depth=FragmentedTightDepthLabelThresholds(
            min_bid_depth_quote_usdt=config_validators.require_positive_float(
                fragmented_tight_depth_raw, "min_bid_depth_quote_usdt",
            ),
            min_ask_depth_quote_usdt=config_validators.require_positive_float(
                fragmented_tight_depth_raw, "min_ask_depth_quote_usdt",
            ),
        ),
        shallow_total_depth=ShallowTotalDepthLabelThresholds(
            min_bid_total_depth_quote_usdt=config_validators.require_positive_float(
                shallow_total_depth_raw, "min_bid_total_depth_quote_usdt",
            ),
            min_ask_total_depth_quote_usdt=config_validators.require_positive_float(
                shallow_total_depth_raw, "min_ask_total_depth_quote_usdt",
            ),
        ),
        low_liquidity_score=LowLiquidityScoreLabelThresholds(),
    )
