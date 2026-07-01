import liquidity_audit.config as app_config


def default_daily_selection() -> app_config.DailySelectionConfig:
    return app_config.DailySelectionConfig(
        max_per_day=10,
        history_csv_path="data/selected_history.csv",
        cooldown_days=30,
    )


def default_daily_selection_config_block() -> dict:
    return {
        "max_per_day": 10,
        "history_csv_path": "data/selected_history.csv",
        "cooldown_days": 30,
    }
