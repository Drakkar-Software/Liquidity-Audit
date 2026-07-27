import pathlib

import tests.fixtures.analysis_fixtures as analysis_fixtures
import tests.fixtures.delisting_risk_fixtures as delisting_risk_fixtures
import tests.fixtures.health_fixtures as health_fixtures
import tests.fixtures.health_label_fixtures as health_label_fixtures
import liquidity_audit.application.shared.daily_selection as daily_selection
import liquidity_audit.config as app_config
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.domain.models as models


def _low_health_listing(
    exchange: str,
    symbol: str,
    liquidity_score: float,
) -> models.ListingRecord:
    base = symbol.split("/")[0]
    return models.ListingRecord(
        exchange=exchange,
        symbol=symbol,
        base=base,
        quote="USDT",
        full_name=f"{base} Token",
        bid_levels=2,
        ask_levels=2,
        liquidity_score=liquidity_score,
        is_low_health=True,
        health_label_primary="few_orders",
        website=f"https://{exchange}-{base}.example/",
    )


class TestSelectAndRecordDailySelections:
    def test_excludes_listings_on_exchanges_not_in_config(self, tmp_path: pathlib.Path):
        csv_path = tmp_path / "listings.csv"
        history_csv_path = tmp_path / "selected_history.csv"
        store = listings_store.ListingsStore(csv_path)
        store.append_or_update([
            _low_health_listing("bitmart", "KCS/USDT", liquidity_score=0.05),
            _low_health_listing("mexc", "LOW/USDT", liquidity_score=0.1),
        ])
        config = app_config.AppConfig(
            listings_csv_path=str(csv_path),
            exchanges=["mexc", "coinex", "bingx"],
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
            delisting_risk=delisting_risk_fixtures.default_delisting_risk(
                ["mexc", "coinex", "bingx"],
            ),
        )

        daily_selections = daily_selection.select_and_record_daily_selections(
            store,
            config,
            new_listing_keys=set(),
        )

        selected_exchanges = {selection.record.exchange for selection in daily_selections}
        assert "bitmart" not in selected_exchanges
        assert "mexc" in selected_exchanges
