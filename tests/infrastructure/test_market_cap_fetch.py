import mock
import pytest

import liquidity_audit.config as app_config
import liquidity_audit.domain.models as models
import liquidity_audit.infrastructure.ccxt_client as ccxt_client
import liquidity_audit.infrastructure.market_cap_fetch as market_cap_fetch


class TestFetchMarketCapsByCoingeckoId:
    @pytest.mark.asyncio
    async def test_maps_coingecko_ids_to_market_cap_usd(self):
        coingecko_client = mock.Mock()
        coingecko_client.options = {"vsCurrency": "usd"}
        coingecko_client.publicGetCoinsMarkets = mock.AsyncMock(return_value=[
            {"id": "ultron", "market_cap": 12_500_000.0},
            {"id": "bitcoin", "market_cap": 1_000_000_000_000.0},
        ])

        market_caps = await market_cap_fetch.fetch_market_caps_by_coingecko_id(
            coingecko_client,
            ["ultron", "bitcoin"],
        )

        assert market_caps == {
            "ultron": 12_500_000.0,
            "bitcoin": 1_000_000_000_000.0,
        }


class TestMarketCapBySymbolFromListings:
    def test_maps_listing_symbols_to_market_caps(self):
        listing_with_id = mock.Mock(symbol="ULX/USDT", coingecko_id="ultron")
        listing_without_id = mock.Mock(symbol="UNKNOWN/USDT", coingecko_id=None)

        market_cap_by_symbol = market_cap_fetch.market_cap_by_symbol_from_listings(
            [listing_with_id, listing_without_id],
            {"ultron": 12_500_000.0},
        )

        assert market_cap_by_symbol == {
            "ULX/USDT": 12_500_000.0,
            "UNKNOWN/USDT": None,
        }


class TestFetchMarketCapBySymbolForListings:
    @pytest.mark.asyncio
    async def test_fetches_once_and_maps_symbols(self, monkeypatch):
        listing_with_id = models.ListingRecord(
            exchange="bitmart",
            symbol="ULX/USDT",
            base="ULX",
            quote="USDT",
            full_name="ULX",
            coingecko_id="ultron",
        )
        listing_without_id = models.ListingRecord(
            exchange="mexc",
            symbol="UNKNOWN/USDT",
            base="UNKNOWN",
            quote="USDT",
            full_name="UNKNOWN",
        )
        config = app_config.AppConfig(
            listings_csv_path="listings.csv",
            exchanges=["bitmart", "mexc"],
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
            health_labels=mock.Mock(),
            min_liquidity_score=0.25,
            ccxt_options={},
            coingecko_options={},
            daily_selection=mock.Mock(),
            analysis=mock.Mock(),
            delisting_risk=mock.Mock(),
        )
        coingecko_client = mock.Mock()
        coingecko_client.close = mock.AsyncMock()
        create_calls: list[str] = []

        def fake_create_exchange(exchange_name, ccxt_options=None, options=None):
            create_calls.append(exchange_name)
            return coingecko_client

        async def fake_fetch_market_caps_by_coingecko_id(client, coingecko_ids):
            assert client is coingecko_client
            assert coingecko_ids == ["ultron"]
            return {"ultron": 12_500_000.0}

        monkeypatch.setattr(ccxt_client, "create_exchange", fake_create_exchange)
        monkeypatch.setattr(
            market_cap_fetch,
            "fetch_market_caps_by_coingecko_id",
            fake_fetch_market_caps_by_coingecko_id,
        )

        market_cap_by_symbol = await market_cap_fetch.fetch_market_cap_by_symbol_for_listings(
            config,
            [listing_with_id, listing_without_id],
        )

        assert create_calls == ["coingecko"]
        coingecko_client.close.assert_awaited_once()
        assert market_cap_by_symbol == {
            "ULX/USDT": 12_500_000.0,
            "UNKNOWN/USDT": None,
        }

    @pytest.mark.asyncio
    async def test_returns_empty_map_when_no_coingecko_ids(self):
        config = mock.Mock()
        listing = models.ListingRecord(
            exchange="bitmart",
            symbol="ULX/USDT",
            base="ULX",
            quote="USDT",
            full_name="ULX",
        )

        market_cap_by_symbol = await market_cap_fetch.fetch_market_cap_by_symbol_for_listings(
            config,
            [listing],
        )

        assert market_cap_by_symbol == {}
