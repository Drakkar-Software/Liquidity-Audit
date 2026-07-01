import json
import pathlib

import pytest

import tests.fixtures.config_helpers as config_helpers
import liquidity_audit.config as app_config


class TestLoadConfigCcxtOptions:
    def test_ccxt_options_optional_defaults_to_empty(self, tmp_path: pathlib.Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_helpers.minimal_config()), encoding="utf-8")

        config = app_config.load_config(config_path)
        assert config.ccxt_options == {}

    def test_coingecko_options_optional_defaults_to_empty(self, tmp_path: pathlib.Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_helpers.minimal_config()), encoding="utf-8")

        config = app_config.load_config(config_path)
        assert config.coingecko_options == {}

    def test_loads_ccxt_options_from_config(self, tmp_path: pathlib.Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_helpers.minimal_config({
            "ccxt_options": {
                "maxRetriesOnFailure": 3,
                "maxRetriesOnFailureDelay": 2000,
            },
        })), encoding="utf-8")

        config = app_config.load_config(config_path)
        assert config.ccxt_options["maxRetriesOnFailure"] == 3

    def test_rejects_non_object_ccxt_options(self, tmp_path: pathlib.Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_helpers.minimal_config({
            "ccxt_options": "invalid",
        })), encoding="utf-8")

        with pytest.raises(app_config.ConfigError):
            app_config.load_config(config_path)


class TestLoadConfigHealthRules:
    def test_rejects_larger_depth_band_below_tight_band(self, tmp_path: pathlib.Path):
        config_path = tmp_path / "config.json"
        config_data = config_helpers.minimal_config()
        config_data["health_rules"]["larger_depth_band_pct"] = 0.005
        config_path.write_text(json.dumps(config_data), encoding="utf-8")

        with pytest.raises(app_config.ConfigError, match="larger_depth_band_pct"):
            app_config.load_config(config_path)

    def test_rejects_deprecated_min_depth_quote_usdt(self, tmp_path: pathlib.Path):
        config_path = tmp_path / "config.json"
        config_data = config_helpers.minimal_config()
        config_data["health_rules"]["min_depth_quote_usdt"] = 1000
        config_path.write_text(json.dumps(config_data), encoding="utf-8")

        with pytest.raises(app_config.ConfigError, match="deprecated"):
            app_config.load_config(config_path)

    def test_loads_unhealthy_values_and_min_liquidity_score(self, tmp_path: pathlib.Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_helpers.minimal_config()), encoding="utf-8")

        config = app_config.load_config(config_path)
        assert config.unhealthy_values.min_bid_levels == 8
        assert config.min_liquidity_score == 0.25
        assert config.health_rules.larger_depth_band_pct == 0.1
        assert config.health_labels.priority[0] == "few_orders"


class TestLoadConfigDailySelection:
    def test_loads_daily_selection(self, tmp_path: pathlib.Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_helpers.minimal_config()), encoding="utf-8")

        config = app_config.load_config(config_path)
        assert config.daily_selection.max_per_day == 10
        assert config.daily_selection.history_csv_path == "data/selected_history.csv"
        assert config.daily_selection.cooldown_days == 30

    def test_rejects_missing_daily_selection(self, tmp_path: pathlib.Path):
        config_data = config_helpers.minimal_config()
        del config_data["daily_selection"]
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_data), encoding="utf-8")

        with pytest.raises(app_config.ConfigError, match="max_per_day"):
            app_config.load_config(config_path)


class TestLoadConfigHealthLabels:
    def test_rejects_unknown_priority_label(self, tmp_path: pathlib.Path):
        config_data = config_helpers.minimal_config()
        config_data["health_labels"]["priority"] = ["unknown_label"]
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_data), encoding="utf-8")

        with pytest.raises(app_config.ConfigError, match="unknown label"):
            app_config.load_config(config_path)

    def test_rejects_duplicate_priority_labels(self, tmp_path: pathlib.Path):
        config_data = config_helpers.minimal_config()
        config_data["health_labels"]["priority"] = [
            "few_orders",
            "few_orders",
        ]
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_data), encoding="utf-8")

        with pytest.raises(app_config.ConfigError, match="duplicates"):
            app_config.load_config(config_path)


class TestLoadConfigDelistingRisk:
    def test_loads_delisting_risk_thresholds(self, tmp_path: pathlib.Path):
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_helpers.minimal_config()), encoding="utf-8")

        config = app_config.load_config(config_path)
        mexc_thresholds = config.delisting_risk.thresholds_for("mexc")
        assert mexc_thresholds.depth_band_pct == 0.02
        assert mexc_thresholds.min_depth_quote_usdt == 5000
        assert mexc_thresholds.min_volume_quote_usdt == 10000

    def test_rejects_missing_exchange_entry(self, tmp_path: pathlib.Path):
        config_data = config_helpers.minimal_config()
        config_data["exchanges"] = ["mexc", "bitmart"]
        config_data["delisting_risk"]["exchanges"] = {
            "mexc": {
                "depth_band_pct": 0.02,
                "min_depth_quote_usdt": 5000,
                "min_volume_quote_usdt": 10000,
            },
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_data), encoding="utf-8")

        with pytest.raises(app_config.ConfigError, match="missing entry"):
            app_config.load_config(config_path)

    def test_rejects_invalid_depth_band_pct(self, tmp_path: pathlib.Path):
        config_data = config_helpers.minimal_config()
        config_data["delisting_risk"]["exchanges"]["mexc"]["depth_band_pct"] = 0
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(config_data), encoding="utf-8")

        with pytest.raises(app_config.ConfigError, match="depth_band_pct"):
            app_config.load_config(config_path)
