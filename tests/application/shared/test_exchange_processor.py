import contextlib

import mock
import pytest

import tests.fixtures.daily_selection_fixtures as daily_selection_fixtures
import tests.fixtures.delisting_risk_fixtures as delisting_risk_fixtures
import liquidity_audit.application.shared.exchange_processor as exchange_processor
import liquidity_audit.config as app_config
import liquidity_audit.domain.models as models
import liquidity_audit.infrastructure.ccxt_client as ccxt_client


def _config() -> app_config.AppConfig:
    return app_config.AppConfig(
        listings_csv_path="data/listings.csv",
        exchanges=["mexc", "coinex"],
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
        health_labels=[],
        min_liquidity_score=0.25,
        ccxt_options={},
        coingecko_options={},
        daily_selection=daily_selection_fixtures.default_daily_selection(),
        analysis=app_config.AnalysisConfig(
            output_dir="data/analysis",
            rankings_min_volume_quote=1000.0,
            checkpoint_every_n_pairs=50,
            delisted_retention_days=30,
        ),
        delisting_risk=delisting_risk_fixtures.default_delisting_risk(["mexc", "coinex"]),
    )


def _listing(exchange: str, symbol: str) -> models.ListingRecord:
    base = symbol.split("/")[0]
    return models.ListingRecord(
        exchange=exchange,
        symbol=symbol,
        base=base,
        quote="USDT",
        full_name=base,
    )


@contextlib.asynccontextmanager
async def _fake_exchange_client(*args, **kwargs):
    yield mock.Mock()


class TestProcessExchangeBootstrap:
    @pytest.mark.asyncio
    async def test_seeds_store_without_counting_as_new_listings(self, monkeypatch):
        config = _config()
        discovered = [
            _listing("coinex", "BTC/USDT"),
            _listing("coinex", "ETH/USDT"),
        ]
        known_keys = {("mexc", "AAA/USDT")}

        monkeypatch.setattr(ccxt_client, "exchange_client", _fake_exchange_client)
        monkeypatch.setattr(
            exchange_processor.listing_discovery,
            "fetch_exchange_listings",
            mock.AsyncMock(return_value=discovered),
        )

        saved_listings, new_listings, failed_enrichments = await exchange_processor.process_exchange(
            "coinex",
            known_keys,
            config,
            identify_only=False,
        )

        assert len(saved_listings) == 2
        assert new_listings == []
        assert failed_enrichments == []
        assert all(listing.first_seen_at for listing in saved_listings)

    @pytest.mark.asyncio
    async def test_counts_new_listings_when_exchange_has_history(self, monkeypatch):
        config = _config()
        discovered = [
            _listing("coinex", "BTC/USDT"),
            _listing("coinex", "ETH/USDT"),
        ]
        known_keys = {("coinex", "BTC/USDT")}

        monkeypatch.setattr(ccxt_client, "exchange_client", _fake_exchange_client)
        monkeypatch.setattr(
            exchange_processor.listing_discovery,
            "fetch_exchange_listings",
            mock.AsyncMock(return_value=discovered),
        )

        saved_listings, new_listings, failed_enrichments = await exchange_processor.process_exchange(
            "coinex",
            known_keys,
            config,
            identify_only=False,
        )

        assert len(saved_listings) == 1
        assert len(new_listings) == 1
        assert new_listings[0].symbol == "ETH/USDT"
        assert failed_enrichments == []
