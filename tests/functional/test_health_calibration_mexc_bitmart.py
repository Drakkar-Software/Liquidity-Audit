import pathlib

import pytest

import liquidity_audit.config as app_config
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.domain.health.evaluation as health_evaluation

_FUNCTIONAL_CSV = pathlib.Path(__file__).resolve().parent / "mexc_bitmart_jun_26_listings.csv"


def _load_calibration_config() -> app_config.AppConfig:
    config_path = pathlib.Path(__file__).resolve().parents[2] / "config.example.json"
    return app_config.load_config(config_path)


class TestHealthCalibrationMexcBitmart:
    def test_unhealthy_rate_in_target_band(self):
        if not _FUNCTIONAL_CSV.is_file():
            pytest.skip(f"functional CSV not found: {_FUNCTIONAL_CSV}")

        config = _load_calibration_config()
        records = listings_store.ListingsStore(_FUNCTIONAL_CSV).load_all()

        evaluable_count = 0
        unhealthy_count = 0
        red_flag_count = 0
        score_only_count = 0

        for record in records.values():
            if record.bid_levels is None:
                continue
            if record.bid_larger_depth_quote is None or record.ask_larger_depth_quote is None:
                continue
            evaluable_count += 1

            health = health_evaluation.evaluate_health_from_stored_metrics(
                record.bid_levels,
                record.ask_levels,
                record.bid_depth_quote,
                record.ask_depth_quote,
                record.bid_larger_depth_quote,
                record.ask_larger_depth_quote,
                record.bid_total_depth_quote,
                record.ask_total_depth_quote,
                record.volume_quote,
                record.bid_ask_spread_ratio,
                config.health_rules,
                config.unhealthy_values,
                config.health_labels,
                config.min_liquidity_score,
            )
            if not health.is_low_health:
                continue

            unhealthy_count += 1
            if health_evaluation.has_unhealthy_red_flag(
                record.bid_levels,
                record.ask_levels,
                record.bid_depth_quote,
                record.ask_depth_quote,
                record.bid_larger_depth_quote,
                record.ask_larger_depth_quote,
                record.volume_quote,
                record.bid_ask_spread_ratio,
                config.unhealthy_values,
            ):
                red_flag_count += 1
            else:
                score_only_count += 1

        if evaluable_count < 100:
            pytest.skip(
                "functional CSV has too few rows with larger_depth columns; "
                "regenerate snapshot via identify-only run",
            )

        unhealthy_rate = unhealthy_count / evaluable_count
        assert 0.15 <= unhealthy_rate <= 0.20, (
            f"unhealthy rate {unhealthy_rate:.1%} outside 15-20% band "
            f"(evaluable={evaluable_count}, unhealthy={unhealthy_count}, "
            f"red_flag={red_flag_count}, score_only={score_only_count})"
        )
        assert unhealthy_rate < 0.30, (
            f"unhealthy rate {unhealthy_rate:.1%} should stay below 30% vs legacy ~41%"
        )

    def test_wide_larger_depth_saves_borderline_pair(self):
        config = _load_calibration_config()
        health = health_evaluation.evaluate_health_from_stored_metrics(
            bid_levels=20,
            ask_levels=20,
            bid_depth_quote=6.0,
            ask_depth_quote=6.0,
            bid_larger_depth_quote=500.0,
            ask_larger_depth_quote=500.0,
            bid_total_depth_quote=5000.0,
            ask_total_depth_quote=5000.0,
            volume_quote=25000.0,
            bid_ask_spread_ratio=0.001,
            health_rules=config.health_rules,
            unhealthy_values=config.unhealthy_values,
            health_labels=config.health_labels,
            min_liquidity_score=config.min_liquidity_score,
        )
        assert health_evaluation.has_unhealthy_red_flag(
            20,
            20,
            6.0,
            6.0,
            500.0,
            500.0,
            25000.0,
            0.001,
            config.unhealthy_values,
        ) is False
        assert health.is_low_health is False

    def test_empty_wide_depth_still_unhealthy(self):
        config = _load_calibration_config()
        health = health_evaluation.evaluate_health_from_stored_metrics(
            bid_levels=20,
            ask_levels=20,
            bid_depth_quote=100.0,
            ask_depth_quote=100.0,
            bid_larger_depth_quote=10.0,
            ask_larger_depth_quote=10.0,
            bid_total_depth_quote=5000.0,
            ask_total_depth_quote=5000.0,
            volume_quote=100000.0,
            bid_ask_spread_ratio=0.001,
            health_rules=config.health_rules,
            unhealthy_values=config.unhealthy_values,
            health_labels=config.health_labels,
            min_liquidity_score=config.min_liquidity_score,
        )
        assert health.is_low_health is True
