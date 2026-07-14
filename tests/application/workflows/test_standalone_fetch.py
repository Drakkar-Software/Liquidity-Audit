import pathlib
from contextlib import asynccontextmanager

import ccxt
import mock
import pytest

import tests.fixtures.daily_selection_fixtures as daily_selection_fixtures
import tests.fixtures.delisting_risk_fixtures as delisting_risk_fixtures
import tests.fixtures.health_label_fixtures as health_label_fixtures
import liquidity_audit.application.shared.fetch_pair_metrics as fetch_pair_metrics
import liquidity_audit.application.workflows.standalone_fetch as standalone_fetch_workflow
import liquidity_audit.config as app_config
import liquidity_audit.domain.analysis.pair_analysis as pair_analysis
import liquidity_audit.infrastructure.ccxt_client as ccxt_client


def _analysis_config(csv_path: pathlib.Path, output_dir: pathlib.Path) -> app_config.AppConfig:
    return app_config.AppConfig(
        listings_csv_path=str(csv_path),
        exchanges=["mexc", "bitmart"],
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
        analysis=app_config.AnalysisConfig(
            output_dir=str(output_dir),
            rankings_min_volume_quote=1000.0,
            checkpoint_every_n_pairs=50,
            delisted_retention_days=30,
        ),
        delisting_risk=delisting_risk_fixtures.default_delisting_risk(["mexc", "bitmart"]),
    )


def _minimal_raw_metrics(
    exchange: str = "bitmart",
    symbol: str = "ULX/USDT",
) -> pair_analysis.ExtendedRawMetrics:
    base = symbol.split("/")[0]
    return pair_analysis.ExtendedRawMetrics(
        exchange=exchange,
        symbol=symbol,
        full_name=base,
        mid_price=1.0,
        spread_pct=1.0,
        bid_levels=10,
        ask_levels=10,
        bid_depth_1pct_quote=100.0,
        ask_depth_1pct_quote=100.0,
        depth_1pct_quote=200.0,
        depth_2pct_quote=300.0,
        depth_10pct_quote=500.0,
        bid_larger_depth_quote=250.0,
        ask_larger_depth_quote=250.0,
        depth_2pct_capped=False,
        volume_quote=10_000.0,
        bid_volume_quote=5000.0,
        ask_volume_quote=5000.0,
        buy_volume_pct=50.0,
        sell_volume_pct=50.0,
        volume_depth_ratio=5.0,
        max_fillable_buy_quote=1000.0,
        liquidity_score=0.5,
        is_low_health=False,
        health_label_primary="",
        health_labels_other=[],
        slippage=[],
        fetched_at="2026-06-12T00:00:00+00:00",
    )


@asynccontextmanager
async def _fake_exchange_client(exchange_name, ccxt_options=None, options=None, reload_markets=True):
    yield mock.Mock()


class TestParsePairSpec:
    def test_parses_base_quote_exchange(self):
        exchange, symbol, base, quote = standalone_fetch_workflow.parse_pair_spec("ULX/USDT:bitmart")
        assert exchange == "bitmart"
        assert symbol == "ULX/USDT"
        assert base == "ULX"
        assert quote == "USDT"

    def test_rejects_missing_exchange(self):
        with pytest.raises(ValueError, match="expected BASE/QUOTE:exchange"):
            standalone_fetch_workflow.parse_pair_spec("ULX/USDT")

    def test_rejects_missing_slash(self):
        with pytest.raises(ValueError, match="symbol must be BASE/QUOTE"):
            standalone_fetch_workflow.parse_pair_spec("ULXUSDT:bitmart")

    def test_rejects_empty_base(self):
        with pytest.raises(ValueError, match="base and quote must be non-empty"):
            standalone_fetch_workflow.parse_pair_spec("/USDT:bitmart")


class TestListingFromPairSpec:
    def test_builds_minimal_listing_record(self):
        listing = standalone_fetch_workflow.listing_from_pair_spec(
            "bitmart",
            "ULX/USDT",
            "ULX",
            "USDT",
        )
        assert listing.exchange == "bitmart"
        assert listing.symbol == "ULX/USDT"
        assert listing.full_name == "ULX"
        assert listing.coingecko_id is None


class TestRunStandaloneFetch:
    @pytest.mark.asyncio
    async def test_returns_full_analysis_payloads_in_input_order(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)
        fetch_calls: list[str] = []

        async def fake_fetch_pair_raw_metrics(exchange_client, listing, config, fetched_at):
            fetch_calls.append(listing.symbol)
            return (
                _minimal_raw_metrics(listing.exchange, listing.symbol),
                [],
                100.0,
            )

        monkeypatch.setattr(ccxt_client, "exchange_client", _fake_exchange_client)
        monkeypatch.setattr(
            fetch_pair_metrics,
            "fetch_pair_raw_metrics",
            fake_fetch_pair_raw_metrics,
        )

        results = await standalone_fetch_workflow.run(
            config,
            ["BTC/USDT:mexc", "ULX/USDT:bitmart"],
        )

        assert fetch_calls == ["BTC/USDT", "ULX/USDT"]
        assert len(results) == 2
        assert results[0]["exchange"] == "mexc"
        assert results[0]["symbol"] == "BTC/USDT"
        assert "raw" in results[0]
        assert "analysis" in results[0]
        assert results[1]["exchange"] == "bitmart"
        assert results[1]["symbol"] == "ULX/USDT"

    @pytest.mark.asyncio
    async def test_records_error_object_for_bad_symbol(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)

        async def fake_fetch_pair_raw_metrics(exchange_client, listing, config, fetched_at):
            if listing.symbol == "ULX/USDT":
                raise ccxt.BadSymbol("ULX/USDT does not exist")
            return (
                _minimal_raw_metrics(listing.exchange, listing.symbol),
                [],
                100.0,
            )

        monkeypatch.setattr(ccxt_client, "exchange_client", _fake_exchange_client)
        monkeypatch.setattr(
            fetch_pair_metrics,
            "fetch_pair_raw_metrics",
            fake_fetch_pair_raw_metrics,
        )

        results = await standalone_fetch_workflow.run(
            config,
            ["BTC/USDT:mexc", "ULX/USDT:bitmart"],
        )

        assert results[0]["symbol"] == "BTC/USDT"
        assert results[1] == {
            "pair": "ULX/USDT:bitmart",
            "error": "ULX/USDT does not exist",
        }

    @pytest.mark.asyncio
    async def test_rejects_unknown_exchange(
        self,
        tmp_path: pathlib.Path,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)

        with pytest.raises(ValueError, match="not in config.exchanges"):
            await standalone_fetch_workflow.run(config, ["BTC/USDT:binance"])
