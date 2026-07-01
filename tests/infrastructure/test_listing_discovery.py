import pytest

import liquidity_audit.infrastructure.listing_discovery as listing_discovery
import liquidity_audit.domain.models as models


def _spot_market(base: str, quote: str, info: dict) -> dict:
    return {
        "base": base,
        "quote": quote,
        "spot": True,
        "active": True,
        "info": info,
    }


class TestIsSupportedQuotePair:
    def test_accepts_usdt_and_usdc(self):
        assert listing_discovery._is_supported_quote_pair({"quote": "USDT"}) is True
        assert listing_discovery._is_supported_quote_pair({"quote": "USDC"}) is True

    def test_rejects_other_quotes(self):
        assert listing_discovery._is_supported_quote_pair({"quote": "BTC"}) is False
        assert listing_discovery._is_supported_quote_pair({"quote": "USD"}) is False


class TestIsSpotActiveMarket:
    def test_accepts_active_spot_market(self):
        market = {"spot": True, "active": True}
        assert listing_discovery._is_spot_active_market(market) is True

    def test_rejects_non_spot_market(self):
        market = {"spot": False, "active": True}
        assert listing_discovery._is_spot_active_market(market) is False

    def test_rejects_inactive_market(self):
        market = {"spot": True, "active": False}
        assert listing_discovery._is_spot_active_market(market) is False


class TestExtractMexcFullName:
    def test_returns_full_name(self):
        market = _spot_market("BTC", "USDT", {"fullName": "Bitcoin"})
        assert listing_discovery._extract_mexc_full_name(market, "BTC/USDT") == "Bitcoin"

    def test_raises_when_full_name_missing(self):
        market = _spot_market("BTC", "USDT", {})
        with pytest.raises(listing_discovery.ListingDiscoveryError):
            listing_discovery._extract_mexc_full_name(market, "BTC/USDT")


class TestFilterNewListings:
    def test_returns_only_unknown_keys(self):
        listings = [
            models.ListingRecord("mexc", "BTC/USDT", "BTC", "USDT", "Bitcoin"),
            models.ListingRecord("mexc", "ETH/USDT", "ETH", "USDT", "Ethereum"),
        ]
        known_keys = {("mexc", "BTC/USDT")}
        result = listing_discovery.filter_new_listings(listings, known_keys)
        assert len(result) == 1
        assert result[0].symbol == "ETH/USDT"


class TestFetchCurrentListings:
    @pytest.mark.asyncio
    async def test_mexc_extracts_spot_listings(self):
        class FakeClient:
            markets = {
                "BTC/USDT": _spot_market("BTC", "USDT", {"fullName": "Bitcoin"}),
                "ETH/USDC": _spot_market("ETH", "USDC", {"fullName": "Ethereum"}),
                "BTC/USD:BTC": {"base": "BTC", "quote": "USD", "spot": False, "active": True, "info": {}},
                "SOL/BTC": _spot_market("SOL", "BTC", {"fullName": "Solana"}),
            }

        listings = await listing_discovery.fetch_current_listings(FakeClient(), "mexc")
        assert len(listings) == 2
        assert {listing.symbol for listing in listings} == {"BTC/USDT", "ETH/USDC"}
        assert listings[0].full_name == "Bitcoin"

    @pytest.mark.asyncio
    async def test_bitmart_uses_currency_name(self):
        class FakeClient:
            markets = {
                "BTC/USDT": _spot_market("BTC", "USDT", {}),
            }

            async def fetch_currencies(self):
                return {"BTC": {"name": "Bitcoin"}}

        listings = await listing_discovery.fetch_exchange_listings(FakeClient(), "bitmart")
        assert listings[0].full_name == "Bitcoin"

    @pytest.mark.asyncio
    async def test_bitmart_skips_markets_with_missing_currency_name(self):
        class FakeClient:
            markets = {
                "BTC/USDT": _spot_market("BTC", "USDT", {}),
                "BZ/USDT": _spot_market("BZ", "USDT", {}),
            }

            async def fetch_currencies(self):
                return {"BTC": {"name": "Bitcoin"}}

        listings = await listing_discovery.fetch_exchange_listings(FakeClient(), "bitmart")
        assert len(listings) == 1
        assert listings[0].symbol == "BTC/USDT"
