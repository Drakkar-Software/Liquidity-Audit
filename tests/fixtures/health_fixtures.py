import liquidity_audit.config as app_config


def health_rules() -> app_config.HealthRules:
    return app_config.HealthRules(
        min_buy_orders=5,
        min_sell_orders=5,
        depth_band_pct=0.01,
        larger_depth_band_pct=0.1,
    )


def unhealthy_values() -> app_config.UnhealthyValues:
    return app_config.UnhealthyValues(
        min_bid_levels=8,
        min_ask_levels=15,
        min_bid_depth_quote_usdt=5.0,
        min_ask_depth_quote_usdt=5.0,
        min_bid_larger_depth_quote_usdt=50.0,
        min_ask_larger_depth_quote_usdt=50.0,
        max_bid_ask_spread_pct=0.036,
        min_bid_depth_volume_ratio=0.0002,
        min_ask_depth_volume_ratio=0.0002,
        min_bid_larger_depth_volume_ratio=0.001,
        min_ask_larger_depth_volume_ratio=0.001,
    )


def min_liquidity_score() -> float:
    return 0.25
