import liquidity_audit.config as app_config


def default_health_labels() -> app_config.HealthLabelsConfig:
    return app_config.HealthLabelsConfig(
        priority=[
            "few_orders",
            "shallow_liquidity",
            "wide_spread",
            "under_depth_for_volume",
            "fragmented_tight_depth",
            "shallow_total_depth",
            "low_liquidity_score",
        ],
        few_orders=app_config.FewOrdersLabelThresholds(
            min_bid_levels=8,
            min_ask_levels=15,
        ),
        shallow_liquidity=app_config.ShallowLiquidityLabelThresholds(
            min_bid_larger_depth_quote_usdt=50.0,
            min_ask_larger_depth_quote_usdt=50.0,
        ),
        wide_spread=app_config.WideSpreadLabelThresholds(
            max_bid_ask_spread_pct=0.036,
        ),
        under_depth_for_volume=app_config.UnderDepthForVolumeLabelThresholds(
            min_bid_depth_volume_ratio=0.0002,
            min_ask_depth_volume_ratio=0.0002,
            min_bid_larger_depth_volume_ratio=0.001,
            min_ask_larger_depth_volume_ratio=0.001,
        ),
        fragmented_tight_depth=app_config.FragmentedTightDepthLabelThresholds(
            min_bid_depth_quote_usdt=5.0,
            min_ask_depth_quote_usdt=5.0,
        ),
        shallow_total_depth=app_config.ShallowTotalDepthLabelThresholds(
            min_bid_total_depth_quote_usdt=2000.0,
            min_ask_total_depth_quote_usdt=2000.0,
        ),
        low_liquidity_score=app_config.LowLiquidityScoreLabelThresholds(),
    )


def default_health_labels_config_block() -> dict:
    return {
        "priority": [
            "few_orders",
            "shallow_liquidity",
            "wide_spread",
            "under_depth_for_volume",
            "fragmented_tight_depth",
            "shallow_total_depth",
            "low_liquidity_score",
        ],
        "few_orders": {
            "min_bid_levels": 8,
            "min_ask_levels": 15,
        },
        "shallow_liquidity": {
            "min_bid_larger_depth_quote_usdt": 50,
            "min_ask_larger_depth_quote_usdt": 50,
        },
        "wide_spread": {
            "max_bid_ask_spread_pct": 0.036,
        },
        "under_depth_for_volume": {
            "min_bid_depth_volume_ratio": 0.0002,
            "min_ask_depth_volume_ratio": 0.0002,
            "min_bid_larger_depth_volume_ratio": 0.001,
            "min_ask_larger_depth_volume_ratio": 0.001,
        },
        "fragmented_tight_depth": {
            "min_bid_depth_quote_usdt": 5,
            "min_ask_depth_quote_usdt": 5,
        },
        "shallow_total_depth": {
            "min_bid_total_depth_quote_usdt": 2000,
            "min_ask_total_depth_quote_usdt": 2000,
        },
        "low_liquidity_score": {},
    }
