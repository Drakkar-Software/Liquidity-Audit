import liquidity_audit.config as app_config


def default_delisting_risk_config_block(
    exchanges: list[str] | None = None,
) -> dict:
    exchange_names = exchanges or ["mexc", "bitmart"]
    return {
        "exchanges": {
            exchange_name: {
                "depth_band_pct": 0.02,
                "min_depth_quote_usdt": 5000,
                "min_volume_quote_usdt": 10000,
            }
            for exchange_name in exchange_names
        },
    }


def default_delisting_risk(
    exchanges: list[str] | None = None,
) -> app_config.DelistingRiskConfig:
    exchange_names = exchanges or ["mexc", "bitmart"]
    return app_config.DelistingRiskConfig(
        exchanges={
            exchange_name: app_config.DelistingRiskExchangeThresholds(
                depth_band_pct=0.02,
                min_depth_quote_usdt=5000.0,
                min_volume_quote_usdt=10000.0,
            )
            for exchange_name in exchange_names
        },
    )
