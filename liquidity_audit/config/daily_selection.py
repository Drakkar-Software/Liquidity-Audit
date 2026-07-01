import dataclasses

import liquidity_audit.config._validators as config_validators


@dataclasses.dataclass
class DailySelectionConfig:
    max_per_day: int
    history_csv_path: str
    cooldown_days: int


def load_daily_selection(daily_selection_raw: dict) -> DailySelectionConfig:
    if not isinstance(daily_selection_raw, dict):
        raise config_validators.ConfigError("config key 'daily_selection' must be an object")
    return DailySelectionConfig(
        max_per_day=config_validators.require_positive_int(daily_selection_raw, "max_per_day"),
        history_csv_path=config_validators.require_string(daily_selection_raw, "history_csv_path"),
        cooldown_days=config_validators.require_positive_int(daily_selection_raw, "cooldown_days"),
    )
