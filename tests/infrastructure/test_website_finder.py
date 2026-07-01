import ccxt
import pytest

import liquidity_audit.domain.website.website_resolution as website_resolution
import liquidity_audit.infrastructure.website_finder as website_finder_module


def _coingecko_market(coin_id: str, base: str, name: str) -> dict:
    return {
        "id": coin_id,
        "base": base,
        "info": {"name": name},
    }


def _grass_markets_by_id() -> dict:
    return {
        "grass": [_coingecko_market("grass", "GRASS", "Grass")],
        "grass-2": [_coingecko_market("grass-2", "GRASS", "Grass")],
    }


class TestSymbolCandidatesFromMarketsById:
    def test_indexes_all_coins_with_duplicate_symbol(self):
        symbol_candidates, indexed_market_count = (
            website_finder_module._symbol_candidates_from_markets_by_id(
                _grass_markets_by_id(),
            )
        )

        assert indexed_market_count == 2
        assert len(symbol_candidates["GRASS"]) == 2
        grass_ids = {market["id"] for market in symbol_candidates["GRASS"]}
        assert grass_ids == {"grass", "grass-2"}


class TestPickCoingeckoMarket:
    @pytest.mark.asyncio
    async def test_matches_by_name_primary(self):
        finder = website_finder_module.WebsiteFinder()
        finder._symbol_candidates = {
            "CAT": [
                _coingecko_market("cat-1", "CAT", "Random Cat"),
                _coingecko_market("catcoin", "CAT", "Catcoin"),
            ],
        }

        class FakeCoingeckoClient:
            async def publicGetCoinsMarkets(self, params):
                raise AssertionError("should not fetch market cap ranks for a single winner")

        pick_result = await finder._pick_coingecko_market(
            FakeCoingeckoClient(),
            "Catcoin",
            "CAT",
        )
        assert pick_result.market is not None
        assert pick_result.market["id"] == "catcoin"

    @pytest.mark.asyncio
    async def test_returns_name_mismatch_candidates(self):
        finder = website_finder_module.WebsiteFinder()
        finder._symbol_candidates = {
            "DATA": [_coingecko_market("streamr", "DATA", "Streamr")],
        }

        class FakeCoingeckoClient:
            async def publicGetCoinsMarkets(self, params):
                raise AssertionError("should not fetch market cap ranks on name mismatch")

        pick_result = await finder._pick_coingecko_market(
            FakeCoingeckoClient(),
            "Data Network",
            "DATA",
        )
        assert pick_result.market is None
        assert pick_result.name_mismatch_candidates == [("streamr", "Streamr")]

    @pytest.mark.asyncio
    async def test_resolves_grass_tie_by_market_cap_rank(self):
        finder = website_finder_module.WebsiteFinder()
        finder._symbol_candidates, _indexed_market_count = (
            website_finder_module._symbol_candidates_from_markets_by_id(
                _grass_markets_by_id(),
            )
        )

        class FakeCoingeckoClient:
            async def publicGetCoinsMarkets(self, params):
                assert params["ids"] == "grass,grass-2"
                return [
                    {"id": "grass", "market_cap_rank": 134},
                    {"id": "grass-2", "market_cap_rank": 12295},
                ]

        pick_result = await finder._pick_coingecko_market(
            FakeCoingeckoClient(),
            "GRASS",
            "GRASS",
        )
        assert pick_result.market is not None
        assert pick_result.market["id"] == "grass"
        assert pick_result.ambiguous_candidates == []

    @pytest.mark.asyncio
    async def test_returns_ambiguous_when_market_cap_ranks_tie(self):
        finder = website_finder_module.WebsiteFinder()
        finder._symbol_candidates, _indexed_market_count = (
            website_finder_module._symbol_candidates_from_markets_by_id(
                _grass_markets_by_id(),
            )
        )

        class FakeCoingeckoClient:
            async def publicGetCoinsMarkets(self, params):
                return [
                    {"id": "grass", "market_cap_rank": 100},
                    {"id": "grass-2", "market_cap_rank": 100},
                ]

        pick_result = await finder._pick_coingecko_market(
            FakeCoingeckoClient(),
            "GRASS",
            "GRASS",
        )
        assert pick_result.market is None
        assert {candidate[0] for candidate in pick_result.ambiguous_candidates} == {
            "grass",
            "grass-2",
        }

    @pytest.mark.asyncio
    async def test_returns_ambiguous_when_market_cap_ranks_missing(self):
        finder = website_finder_module.WebsiteFinder()
        finder._symbol_candidates, _indexed_market_count = (
            website_finder_module._symbol_candidates_from_markets_by_id(
                _grass_markets_by_id(),
            )
        )

        class FakeCoingeckoClient:
            async def publicGetCoinsMarkets(self, params):
                return []

        pick_result = await finder._pick_coingecko_market(
            FakeCoingeckoClient(),
            "GRASS",
            "GRASS",
        )
        assert pick_result.market is None
        assert len(pick_result.ambiguous_candidates) == 2


class TestResolveWebsite:
    @pytest.mark.asyncio
    async def test_returns_name_mismatch_failure_reason(self, caplog):
        finder = website_finder_module.WebsiteFinder()
        finder._symbol_candidates = {
            "DATA": [_coingecko_market("streamr", "DATA", "Streamr")],
        }
        finder._index_loaded = True

        class FakeCoingeckoClient:
            async def publicGetCoinsId(self, params):
                raise AssertionError("should not fetch coin detail when name mismatches")

            async def publicGetCoinsMarkets(self, params):
                raise AssertionError("should not fetch market cap ranks on name mismatch")

        with caplog.at_level("WARNING"):
            result = await finder.resolve_website(FakeCoingeckoClient(), "Data Network", "DATA")

        assert result.failure_reason == website_resolution.COINGECKO_NAME_MISMATCH
        assert result.symbol_coingecko_candidates == [{"id": "streamr", "name": "Streamr"}]
        assert any("CoinGecko name mismatch" in record.message for record in caplog.records)


class TestCallCoingeckoWithRateLimitRetry:
    @pytest.mark.asyncio
    async def test_retries_after_rate_limit(self, monkeypatch):
        call_count = 0
        sleep_calls: list[float] = []

        async def fake_sleep(seconds: float) -> None:
            sleep_calls.append(seconds)

        monkeypatch.setattr(website_finder_module.asyncio, "sleep", fake_sleep)

        async def operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ccxt.RateLimitExceeded("rate limited")
            return "ok"

        result = await website_finder_module._call_coingecko_with_rate_limit_retry(operation)
        assert result == "ok"
        assert call_count == 2
