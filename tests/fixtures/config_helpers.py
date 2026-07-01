import tests.fixtures.daily_selection_fixtures as daily_selection_fixtures
import tests.fixtures.delisting_risk_fixtures as delisting_risk_fixtures
import tests.fixtures.health_label_fixtures as health_label_fixtures


def minimal_config(overrides: dict | None = None) -> dict:
    config = {
        "listings_csv_path": "data/listings.csv",
        "exchanges": ["mexc"],
        "order_book_limit": 50,
        "health_rules": {
            "min_buy_orders": 5,
            "min_sell_orders": 5,
            "depth_band_pct": 0.01,
            "larger_depth_band_pct": 0.1,
        },
        "unhealthy_values": {
            "min_bid_levels": 8,
            "min_ask_levels": 15,
            "min_bid_depth_quote_usdt": 5,
            "min_ask_depth_quote_usdt": 5,
            "min_bid_larger_depth_quote_usdt": 50,
            "min_ask_larger_depth_quote_usdt": 50,
            "max_bid_ask_spread_pct": 0.036,
            "min_bid_depth_volume_ratio": 0.0002,
            "min_ask_depth_volume_ratio": 0.0002,
            "min_bid_larger_depth_volume_ratio": 0.001,
            "min_ask_larger_depth_volume_ratio": 0.001,
        },
        "min_liquidity_score": 0.25,
        "health_labels": health_label_fixtures.default_health_labels_config_block(),
        "daily_selection": daily_selection_fixtures.default_daily_selection_config_block(),
        "analysis": {
            "output_dir": "data/analysis",
            "rankings_min_volume_quote": 1000,
            "checkpoint_every_n_pairs": 50,
            "delisted_retention_days": 30,
        },
        "delisting_risk": delisting_risk_fixtures.default_delisting_risk_config_block(["mexc"]),
    }
    if overrides:
        config.update(overrides)
    return config
