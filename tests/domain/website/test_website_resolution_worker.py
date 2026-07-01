import asyncio
import pathlib

import mock
import pytest

import tests.fixtures.daily_selection_fixtures as daily_selection_fixtures
import tests.fixtures.delisting_risk_fixtures as delisting_risk_fixtures
import liquidity_audit.config as app_config
import liquidity_audit.domain.models as models
import liquidity_audit.domain.website.website_resolution as website_resolution
import liquidity_audit.domain.website.website_resolution_worker as website_resolution_worker
import liquidity_audit.infrastructure.listings_store as listings_store


def _config(csv_path: pathlib.Path) -> app_config.AppConfig:
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
        health_labels=[],
        min_liquidity_score=0.25,
        ccxt_options={},
        coingecko_options={},
        daily_selection=daily_selection_fixtures.default_daily_selection(),
        analysis=app_config.AnalysisConfig(
            output_dir=str(csv_path.parent / "analysis"),
            rankings_min_volume_quote=1000.0,
            checkpoint_every_n_pairs=50,
            delisted_retention_days=30,
        ),
        delisting_risk=delisting_risk_fixtures.default_delisting_risk(["mexc"]),
    )


def _listing(
    symbol: str = "NEW/USDT",
    *,
    is_low_health: bool = True,
    website: str | None = None,
    website_resolution_status: str | None = None,
) -> models.ListingRecord:
    base = symbol.split("/")[0]
    return models.ListingRecord(
        exchange="mexc",
        symbol=symbol,
        base=base,
        quote="USDT",
        full_name=f"{base} Token",
        bid_levels=2 if is_low_health else None,
        is_low_health=is_low_health,
        website=website,
        website_resolution_status=website_resolution_status,
    )


class TestWebsiteResolutionWorkerTryEnqueue:
    @pytest.mark.asyncio
    async def test_skips_duplicate_enqueue(self, tmp_path: pathlib.Path, monkeypatch):
        csv_path = tmp_path / "listings.csv"
        config = _config(csv_path)
        listings_csv_lock = asyncio.Lock()
        store = listings_store.ListingsStore(csv_path)

        worker = website_resolution_worker.WebsiteResolutionWorker(
            store,
            config,
            set(),
            {},
            listings_csv_lock,
        )
        monkeypatch.setattr(worker, "start", mock.AsyncMock())
        worker._consumer_task = asyncio.create_task(asyncio.sleep(3600))

        listing = _listing()
        worker.try_enqueue(listing)
        worker.try_enqueue(listing)

        assert len(worker._enqueued_keys) == 1
        worker._consumer_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await worker._consumer_task


class TestWebsiteResolutionWorkerShutdown:
    @pytest.mark.asyncio
    async def test_serializes_coingecko_resolve_calls(self, tmp_path: pathlib.Path, monkeypatch):
        csv_path = tmp_path / "listings.csv"
        config = _config(csv_path)
        listings_csv_lock = asyncio.Lock()
        store = listings_store.ListingsStore(csv_path)

        active_resolves = 0
        max_active_resolves = 0
        resolve_order: list[str] = []

        async def fake_load_coingecko_index(self, coingecko_client):
            return None

        async def fake_resolve_website(self, coingecko_client, full_name, base_symbol):
            nonlocal active_resolves, max_active_resolves
            active_resolves += 1
            max_active_resolves = max(max_active_resolves, active_resolves)
            resolve_order.append(base_symbol)
            await asyncio.sleep(0.02)
            active_resolves -= 1
            return website_resolution.WebsiteResolutionResult(
                website=f"https://{base_symbol.lower()}.example/",
                coingecko_id=base_symbol.lower(),
            )

        monkeypatch.setattr(
            website_resolution_worker.website_finder.WebsiteFinder,
            "load_coingecko_index",
            fake_load_coingecko_index,
        )
        monkeypatch.setattr(
            website_resolution_worker.website_finder.WebsiteFinder,
            "resolve_website",
            fake_resolve_website,
        )
        monkeypatch.setattr(
            website_resolution_worker.ccxt_client,
            "create_exchange",
            lambda *args, **kwargs: mock.AsyncMock(),
        )

        worker = await website_resolution_worker.WebsiteResolutionWorker.create_and_start(
            store,
            config,
            set(),
            listings_csv_lock,
        )
        worker.try_enqueue(_listing("AAA/USDT"))
        worker.try_enqueue(_listing("BBB/USDT"))
        resolved_count = await worker.shutdown()

        assert resolved_count == 2
        assert max_active_resolves == 1
        assert resolve_order == ["AAA", "BBB"]

    @pytest.mark.asyncio
    async def test_persists_resolved_listing_to_store(self, tmp_path: pathlib.Path, monkeypatch):
        csv_path = tmp_path / "listings.csv"
        config = _config(csv_path)
        listings_csv_lock = asyncio.Lock()
        store = listings_store.ListingsStore(csv_path)
        listing = _listing("SAVE/USDT")

        async def fake_load_coingecko_index(self, coingecko_client):
            return None

        async def fake_resolve_website(self, coingecko_client, full_name, base_symbol):
            return website_resolution.WebsiteResolutionResult(
                website="https://save.example/",
                coingecko_id="save",
            )

        monkeypatch.setattr(
            website_resolution_worker.website_finder.WebsiteFinder,
            "load_coingecko_index",
            fake_load_coingecko_index,
        )
        monkeypatch.setattr(
            website_resolution_worker.website_finder.WebsiteFinder,
            "resolve_website",
            fake_resolve_website,
        )
        monkeypatch.setattr(
            website_resolution_worker.ccxt_client,
            "create_exchange",
            lambda *args, **kwargs: mock.AsyncMock(),
        )

        worker = await website_resolution_worker.WebsiteResolutionWorker.create_and_start(
            store,
            config,
            {listing.key()},
            listings_csv_lock,
        )
        worker.try_enqueue(listing)
        await worker.shutdown()

        saved = store.load_all()[listing.key()]
        assert saved.website == "https://save.example/"
        assert saved.coingecko_id == "save"
