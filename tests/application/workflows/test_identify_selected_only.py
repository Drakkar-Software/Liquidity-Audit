import pathlib

import pytest

import tests.fixtures.analysis_fixtures as analysis_fixtures
import tests.fixtures.delisting_risk_fixtures as delisting_risk_fixtures
import tests.fixtures.health_fixtures as health_fixtures
import tests.fixtures.health_label_fixtures as health_label_fixtures
import liquidity_audit.application.workflows.identify_selected_only as identify_selected_only_workflow
import liquidity_audit.config as app_config
import liquidity_audit.infrastructure.selected_history_store as selected_history_store
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.domain.models as models


class TestIdentifySelectedOnly:
    @pytest.mark.asyncio
    async def test_appends_selected_history_and_returns_result(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        history_csv_path = tmp_path / "selected_history.csv"
        store = listings_store.ListingsStore(csv_path)
        store.append_or_update([
            models.ListingRecord(
                exchange="mexc",
                symbol="LOW/USDT",
                base="LOW",
                quote="USDT",
                full_name="Low Token",
                bid_levels=2,
                ask_levels=2,
                liquidity_score=0.1,
                is_low_health=True,
                health_label_primary="few_orders",
                website="https://low.example/",
            ),
        ])
        config = app_config.AppConfig(
            listings_csv_path=str(csv_path),
            exchanges=["mexc"],
            order_book_limit=50,
            health_rules=health_fixtures.health_rules(),
            unhealthy_values=health_fixtures.unhealthy_values(),
            health_labels=health_label_fixtures.default_health_labels(),
            min_liquidity_score=0.25,
            ccxt_options={},
            coingecko_options={},
            daily_selection=app_config.DailySelectionConfig(
                max_per_day=5,
                history_csv_path=str(history_csv_path),
                cooldown_days=30,
            ),
            analysis=analysis_fixtures.default_analysis_config(),
            delisting_risk=delisting_risk_fixtures.default_delisting_risk(["mexc"]),
        )

        result = await identify_selected_only_workflow.run(config)

        assert result.run_summary.selections_proposed_total == 1
        history_records = selected_history_store.SelectedHistoryStore(
            history_csv_path,
        ).load_all()
        assert len(history_records) == 1
        assert history_records[0].symbol == "LOW/USDT"
