import dataclasses

import liquidity_audit.config._validators as config_validators


@dataclasses.dataclass
class DelistingRiskExchangeThresholds:
    depth_band_pct: float
    min_depth_quote_usdt: float
    min_volume_quote_usdt: float


@dataclasses.dataclass
class DelistingRiskConfig:
    exchanges: dict[str, DelistingRiskExchangeThresholds]

    def thresholds_for(self, exchange: str) -> DelistingRiskExchangeThresholds:
        return self.exchanges[exchange]


def load_delisting_risk_exchange_thresholds(
    exchange_name: str,
    exchange_raw: dict,
) -> DelistingRiskExchangeThresholds:
    if not isinstance(exchange_raw, dict):
        raise config_validators.ConfigError(
            f"config key delisting_risk.exchanges.{exchange_name!r} must be an object",
        )
    depth_band_pct = exchange_raw.get("depth_band_pct")
    if not isinstance(depth_band_pct, (int, float)) or not (0 < float(depth_band_pct) <= 1):
        raise config_validators.ConfigError(
            f"config key delisting_risk.exchanges.{exchange_name}.depth_band_pct "
            "must be a number > 0 and <= 1",
        )
    return DelistingRiskExchangeThresholds(
        depth_band_pct=float(depth_band_pct),
        min_depth_quote_usdt=config_validators.require_positive_float(
            exchange_raw, "min_depth_quote_usdt",
        ),
        min_volume_quote_usdt=config_validators.require_positive_float(
            exchange_raw, "min_volume_quote_usdt",
        ),
    )


def load_delisting_risk(
    delisting_risk_raw: dict | None,
    exchanges: list[str],
) -> DelistingRiskConfig:
    if delisting_risk_raw is None:
        raise config_validators.ConfigError("config key 'delisting_risk' is required")
    if not isinstance(delisting_risk_raw, dict):
        raise config_validators.ConfigError("config key 'delisting_risk' must be an object")

    exchanges_raw = delisting_risk_raw.get("exchanges")
    if not isinstance(exchanges_raw, dict) or not exchanges_raw:
        raise config_validators.ConfigError("config key delisting_risk.exchanges must be a non-empty object")

    thresholds_by_exchange: dict[str, DelistingRiskExchangeThresholds] = {}
    for exchange_name in exchanges:
        if exchange_name not in exchanges_raw:
            raise config_validators.ConfigError(
                f"config key delisting_risk.exchanges is missing entry for exchange {exchange_name!r}",
            )
        thresholds_by_exchange[exchange_name] = load_delisting_risk_exchange_thresholds(
            exchange_name,
            exchanges_raw[exchange_name],
        )

    for configured_exchange in exchanges_raw:
        if configured_exchange not in exchanges:
            raise config_validators.ConfigError(
                f"config key delisting_risk.exchanges contains unknown exchange "
                f"{configured_exchange!r}; expected one of {exchanges!r}",
            )

    return DelistingRiskConfig(exchanges=thresholds_by_exchange)
