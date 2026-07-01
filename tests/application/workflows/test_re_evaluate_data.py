import json
import pathlib

import pytest

import tests.fixtures.analysis_fixtures as analysis_fixtures
import tests.fixtures.daily_selection_fixtures as daily_selection_fixtures
import tests.fixtures.delisting_risk_fixtures as delisting_risk_fixtures
import tests.fixtures.health_label_fixtures as health_label_fixtures
import liquidity_audit.application.workflows.re_evaluate_data as re_evaluate_data_workflow
import liquidity_audit.infrastructure.analysis_store as analysis_store
import liquidity_audit.config as app_config
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.domain.models as models
import liquidity_audit.domain.analysis.pair_analysis as token_analysis
import liquidity_audit.domain.health.evaluation as health_evaluation


def _config(csv_path: pathlib.Path, output_dir: pathlib.Path | None = None) -> app_config.AppConfig:
    analysis_config = analysis_fixtures.default_analysis_config()
    if output_dir is not None:
        analysis_config = app_config.AnalysisConfig(
            output_dir=str(output_dir),
            rankings_min_volume_quote=analysis_config.rankings_min_volume_quote,
            checkpoint_every_n_pairs=analysis_config.checkpoint_every_n_pairs,
            delisted_retention_days=analysis_config.delisted_retention_days,
        )
    return app_config.AppConfig(
        listings_csv_path=str(csv_path),
        exchanges=["mexc"],
        order_book_limit=50,
        health_rules=app_config.HealthRules(
            min_buy_orders=5,
            min_sell_orders=5,
            depth_band_pct=0.01,
            larger_depth_band_pct=0.1,
        ),
        unhealthy_values=app_config.UnhealthyValues(
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
        ),
        health_labels=health_label_fixtures.default_health_labels(),
        min_liquidity_score=0.25,
        ccxt_options={},
        coingecko_options={},
        daily_selection=daily_selection_fixtures.default_daily_selection(),
        analysis=analysis_config,
        delisting_risk=delisting_risk_fixtures.default_delisting_risk(["mexc"]),
    )


class TestReEvaluateData:
    @pytest.mark.asyncio
    async def test_recomputes_health_from_csv_without_network(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        store = listings_store.ListingsStore(csv_path)
        store.append_or_update([
            models.ListingRecord(
                exchange="mexc",
                symbol="LOW/USDT",
                base="LOW",
                quote="USDT",
                full_name="Low Token",
                bid_levels=3,
                ask_levels=50,
                bid_depth_quote=5000.0,
                ask_depth_quote=5000.0,
                bid_larger_depth_quote=5000.0,
                ask_larger_depth_quote=5000.0,
                volume_quote=100000.0,
                bid_ask_spread_ratio=0.001,
                liquidity_score=0.9,
                is_low_health=False,
            ),
        ])

        await re_evaluate_data_workflow.run(_config(csv_path))

        records = listings_store.ListingsStore(csv_path).load_all()
        record = records[("mexc", "LOW/USDT")]
        assert record.is_low_health is True
        assert record.bid_levels == 3
        assert record.liquidity_score is not None
        assert record.health_label_primary == health_evaluation.LABEL_FEW_ORDERS

    @pytest.mark.asyncio
    async def test_rebuilds_pair_json_from_stored_raw_and_writes_manifest(
        self,
        tmp_path: pathlib.Path,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _config(csv_path, output_dir)
        store = listings_store.ListingsStore(csv_path)
        raw_metrics = token_analysis.ExtendedRawMetrics(
            exchange="mexc",
            symbol="BTC/USDT",
            full_name="Bitcoin",
            mid_price=64_210.0,
            spread_pct=0.00005,
            bid_levels=50,
            ask_levels=50,
            bid_depth_1pct_quote=6_306_349.0,
            ask_depth_1pct_quote=6_341_707.0,
            depth_1pct_quote=12_648_056.0,
            depth_2pct_quote=12_648_056.0,
            depth_10pct_quote=12_648_056.0,
            bid_larger_depth_quote=6_306_349.0,
            ask_larger_depth_quote=6_341_707.0,
            depth_2pct_capped=True,
            volume_quote=233_048_420.0,
            bid_volume_quote=0.26,
            ask_volume_quote=0.33,
            buy_volume_pct=44.0,
            sell_volume_pct=56.0,
            volume_depth_ratio=18.4,
            max_fillable_buy_quote=6_341_707.0,
            liquidity_score=1.0,
            is_low_health=False,
            health_label_primary="",
            health_labels_other=[],
            slippage=[
                {"size": 10_000, "pct": 0.00002, "omitted": False, "fill_ratio": 1.0},
            ],
            fetched_at="2026-06-13T14:48:32+00:00",
        )
        store.append_or_update([
            models.ListingRecord(
                exchange="mexc",
                symbol="BTC/USDT",
                base="BTC",
                quote="USDT",
                full_name="Bitcoin",
                bid_levels=50,
                ask_levels=50,
                bid_depth_quote=6_306_349.0,
                ask_depth_quote=6_341_707.0,
                bid_larger_depth_quote=6_306_349.0,
                ask_larger_depth_quote=6_341_707.0,
                volume_quote=233_048_420.0,
                bid_ask_spread_ratio=0.00005,
                liquidity_score=1.0,
                is_low_health=False,
            ),
        ])

        analysis_store_instance = analysis_store.AnalysisStore(output_dir)
        analysis_store_instance.save_pair_analysis(
            "mexc",
            "BTC/USDT",
            {
                "raw": raw_metrics.to_dict(),
                "analysis": {
                    "health_dashboard": [
                        {
                            "severity": "Critical",
                            "title": "Volume consistency",
                            "impact": "Hollow volume risk",
                            "evidence": "stale",
                        },
                    ],
                },
            },
        )

        await re_evaluate_data_workflow.run(config)

        pair_payload = analysis_store_instance.load_pair_analysis("mexc", "BTC/USDT")
        assert pair_payload is not None
        volume_card = next(
            card
            for card in pair_payload["analysis"]["health_dashboard"]
            if card["title"] == "Volume consistency"
        )
        assert volume_card["severity"] == "Low"

        manifest_path = analysis_store_instance.manifest_json_path()
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["mode"] == "re_evaluate_data"
        assert manifest["pairs_reanalyzed"] == 1

        csv_record = listings_store.ListingsStore(csv_path).load_all()[("mexc", "BTC/USDT")]
        assert csv_record.last_analyzed_at is not None
        assert csv_record.analysis_json_path is not None
