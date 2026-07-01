import dataclasses
import json
import pathlib
import typing

import liquidity_audit.config._validators as config_validators
import liquidity_audit.config.analysis as analysis_config
import liquidity_audit.config.daily_selection as daily_selection_config
import liquidity_audit.config.delisting_risk as delisting_risk_config
import liquidity_audit.config.health as health_config

ConfigError = config_validators.ConfigError
KNOWN_HEALTH_LABEL_IDS = health_config.KNOWN_HEALTH_LABEL_IDS
HealthRules = health_config.HealthRules
UnhealthyValues = health_config.UnhealthyValues
FewOrdersLabelThresholds = health_config.FewOrdersLabelThresholds
ShallowLiquidityLabelThresholds = health_config.ShallowLiquidityLabelThresholds
WideSpreadLabelThresholds = health_config.WideSpreadLabelThresholds
UnderDepthForVolumeLabelThresholds = health_config.UnderDepthForVolumeLabelThresholds
FragmentedTightDepthLabelThresholds = health_config.FragmentedTightDepthLabelThresholds
ShallowTotalDepthLabelThresholds = health_config.ShallowTotalDepthLabelThresholds
LowLiquidityScoreLabelThresholds = health_config.LowLiquidityScoreLabelThresholds
HealthLabelsConfig = health_config.HealthLabelsConfig
DailySelectionConfig = daily_selection_config.DailySelectionConfig
AnalysisConfig = analysis_config.AnalysisConfig
DelistingRiskExchangeThresholds = delisting_risk_config.DelistingRiskExchangeThresholds
DelistingRiskConfig = delisting_risk_config.DelistingRiskConfig


@dataclasses.dataclass
class AppConfig:
    listings_csv_path: str
    exchanges: list[str]
    order_book_limit: int
    health_rules: HealthRules
    unhealthy_values: UnhealthyValues
    health_labels: HealthLabelsConfig
    min_liquidity_score: float
    ccxt_options: dict[str, typing.Any]
    coingecko_options: dict[str, typing.Any]
    daily_selection: DailySelectionConfig
    analysis: AnalysisConfig
    delisting_risk: DelistingRiskConfig


def _load_daily_selection_config(raw: dict) -> DailySelectionConfig:
    daily_selection_raw = raw.get("daily_selection")
    if daily_selection_raw is None:
        daily_selection_raw = raw.get("daily_contacts", {})
    return daily_selection_config.load_daily_selection(daily_selection_raw)


def load_config(config_path: str | pathlib.Path) -> AppConfig:
    path = pathlib.Path(config_path)
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")

    with path.open(encoding="utf-8") as config_file:
        raw = json.load(config_file)

    if not isinstance(raw, dict):
        raise ConfigError("config root must be a JSON object")

    health_raw = raw.get("health_rules")
    if not isinstance(health_raw, dict):
        raise ConfigError("config key 'health_rules' must be an object")
    health_config.reject_deprecated_health_rule_keys(health_raw)

    unhealthy_raw = raw.get("unhealthy_values")
    if not isinstance(unhealthy_raw, dict):
        raise ConfigError("config key 'unhealthy_values' must be an object")

    exchanges = raw.get("exchanges")
    if not isinstance(exchanges, list) or not exchanges:
        raise ConfigError("config key 'exchanges' must be a non-empty list of strings")
    if not all(isinstance(exchange, str) and exchange.strip() for exchange in exchanges):
        raise ConfigError("config key 'exchanges' must contain non-empty strings")

    ccxt_options = raw.get("ccxt_options", {})
    if not isinstance(ccxt_options, dict):
        raise ConfigError("config key 'ccxt_options' must be an object")

    coingecko_options = raw.get("coingecko_options", {})
    if not isinstance(coingecko_options, dict):
        raise ConfigError("config key 'coingecko_options' must be an object")

    depth_band_pct = config_validators.require_positive_float(health_raw, "depth_band_pct")
    larger_depth_band_pct = config_validators.require_positive_float(health_raw, "larger_depth_band_pct")
    if larger_depth_band_pct < depth_band_pct:
        raise ConfigError(
            "config key health_rules.larger_depth_band_pct must be >= depth_band_pct",
        )

    min_liquidity_score = raw.get("min_liquidity_score")
    if not isinstance(min_liquidity_score, (int, float)) or not (0.0 <= float(min_liquidity_score) <= 1.0):
        raise ConfigError("config key 'min_liquidity_score' must be a number between 0 and 1")

    return AppConfig(
        listings_csv_path=config_validators.require_string(raw, "listings_csv_path"),
        exchanges=exchanges,
        order_book_limit=config_validators.require_positive_int(raw, "order_book_limit"),
        health_rules=HealthRules(
            min_buy_orders=config_validators.require_positive_int(health_raw, "min_buy_orders"),
            min_sell_orders=config_validators.require_positive_int(health_raw, "min_sell_orders"),
            depth_band_pct=depth_band_pct,
            larger_depth_band_pct=larger_depth_band_pct,
        ),
        unhealthy_values=UnhealthyValues(
            min_bid_levels=config_validators.require_positive_int(unhealthy_raw, "min_bid_levels"),
            min_ask_levels=config_validators.require_positive_int(unhealthy_raw, "min_ask_levels"),
            min_bid_depth_quote_usdt=config_validators.require_positive_float(
                unhealthy_raw, "min_bid_depth_quote_usdt",
            ),
            min_ask_depth_quote_usdt=config_validators.require_positive_float(
                unhealthy_raw, "min_ask_depth_quote_usdt",
            ),
            min_bid_larger_depth_quote_usdt=config_validators.require_positive_float(
                unhealthy_raw, "min_bid_larger_depth_quote_usdt",
            ),
            min_ask_larger_depth_quote_usdt=config_validators.require_positive_float(
                unhealthy_raw, "min_ask_larger_depth_quote_usdt",
            ),
            max_bid_ask_spread_pct=config_validators.require_positive_float(
                unhealthy_raw, "max_bid_ask_spread_pct",
            ),
            min_bid_depth_volume_ratio=config_validators.require_non_negative_float(
                unhealthy_raw, "min_bid_depth_volume_ratio",
            ),
            min_ask_depth_volume_ratio=config_validators.require_non_negative_float(
                unhealthy_raw, "min_ask_depth_volume_ratio",
            ),
            min_bid_larger_depth_volume_ratio=config_validators.require_non_negative_float(
                unhealthy_raw, "min_bid_larger_depth_volume_ratio",
            ),
            min_ask_larger_depth_volume_ratio=config_validators.require_non_negative_float(
                unhealthy_raw, "min_ask_larger_depth_volume_ratio",
            ),
        ),
        health_labels=health_config.load_health_labels(raw.get("health_labels", {})),
        min_liquidity_score=float(min_liquidity_score),
        ccxt_options=ccxt_options,
        coingecko_options=coingecko_options,
        daily_selection=_load_daily_selection_config(raw),
        analysis=analysis_config.load_analysis_config(raw.get("analysis")),
        delisting_risk=delisting_risk_config.load_delisting_risk(raw.get("delisting_risk"), exchanges),
    )
