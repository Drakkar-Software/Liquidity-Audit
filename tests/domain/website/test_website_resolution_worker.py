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
    exchange: str = "mexc",
    is_low_health: bool = True,
    website: str | None = None,
    website_resolution_status: str | None = None,
) -> models.ListingRecord:
    base = symbol.split("/")[0]
    return models.ListingRecord(
        exchange=exchange,
        symbol=symbol,
        base=base,
        quote="USDT",
        full_name=f"{base} Token",
        bid_levels=2 if is_low_health else None,
        is_low_health=is_low_health,
        website=website,
        website_resolution_status=website_resolution_status,
    )


def _mock_ccxt_client(exchange_name: str) -> mock.AsyncMock:
    client = mock.AsyncMock()
    client.rateLimit = 50 if exchange_name == "mexc" else 2.5
    client.throttle = mock.AsyncMock()
    client.open = mock.Mock()
    client.close = mock.AsyncMock()
    return client


_UNPATCHED = object()


def _patch_worker_infrastructure(
    monkeypatch,
    *,
    mexc_website: str | None | object = _UNPATCHED,
    coinex_website: str | None | object = _UNPATCHED,
):
    async def fake_load_coingecko_index(self, coingecko_client):
        return None

    monkeypatch.setattr(
        website_resolution_worker.website_finder.WebsiteFinder,
        "load_coingecko_index",
        fake_load_coingecko_index,
    )
    monkeypatch.setattr(
        website_resolution_worker.exchange_website_resolvers,
        "create_mexc_http_session",
        lambda: mock.AsyncMock(),
    )
    monkeypatch.setattr(
        website_resolution_worker.exchange_website_resolvers,
        "create_coinex_http_session",
        lambda: mock.AsyncMock(),
    )
    if mexc_website is not _UNPATCHED:
        monkeypatch.setattr(
            website_resolution_worker.exchange_website_resolvers,
            "resolve_mexc_website",
            mock.AsyncMock(return_value=mexc_website),
        )
    if coinex_website is not _UNPATCHED:
        monkeypatch.setattr(
            website_resolution_worker.exchange_website_resolvers,
            "resolve_coinex_website",
            mock.AsyncMock(return_value=coinex_website),
        )

    def fake_create_exchange(exchange_name, **kwargs):
        return _mock_ccxt_client(exchange_name)

    monkeypatch.setattr(
        website_resolution_worker.ccxt_client,
        "create_exchange",
        fake_create_exchange,
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

        listing = _listing()
        worker.try_enqueue(listing)
        worker.try_enqueue(listing)

        assert len(worker._enqueued_keys) == 1
        assert worker._mexc_queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_routes_coinex_to_coinex_queue(self, tmp_path: pathlib.Path, monkeypatch):
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

        listing = _listing("AIOZ/USDT", exchange="coinex")
        worker.try_enqueue(listing)

        assert worker._coinex_queue.qsize() == 1
        assert worker._mexc_queue.qsize() == 0
        assert worker._coingecko_queue.qsize() == 0

    @pytest.mark.asyncio
    async def test_routes_bingx_to_coingecko_queue(self, tmp_path: pathlib.Path, monkeypatch):
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

        listing = _listing("TOKEN/USDT", exchange="bingx")
        worker.try_enqueue(listing)

        assert worker._coingecko_queue.qsize() == 1
        assert worker._mexc_queue.qsize() == 0
        assert worker._coinex_queue.qsize() == 0


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

        _patch_worker_infrastructure(monkeypatch, mexc_website=None)

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
            "resolve_website",
            fake_resolve_website,
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

        _patch_worker_infrastructure(monkeypatch, mexc_website=None)

        async def fake_resolve_website(self, coingecko_client, full_name, base_symbol):
            return website_resolution.WebsiteResolutionResult(
                website="https://save.example/",
                coingecko_id="save",
            )

        monkeypatch.setattr(
            website_resolution_worker.website_finder.WebsiteFinder,
            "resolve_website",
            fake_resolve_website,
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

    @pytest.mark.asyncio
    async def test_shutdown_returns_after_queue_drain_timeout(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        config = _config(csv_path)
        listings_csv_lock = asyncio.Lock()
        store = listings_store.ListingsStore(csv_path)

        _patch_worker_infrastructure(monkeypatch, mexc_website=None)

        async def slow_resolve_website(self, coingecko_client, full_name, base_symbol):
            await asyncio.sleep(5.0)
            return website_resolution.WebsiteResolutionResult(
                website=f"https://{base_symbol.lower()}.example/",
                coingecko_id=base_symbol.lower(),
            )

        monkeypatch.setattr(
            website_resolution_worker,
            "SHUTDOWN_QUEUE_DRAIN_TIMEOUT_SECONDS",
            0.01,
        )
        monkeypatch.setattr(
            website_resolution_worker,
            "CONSUMER_STOP_TIMEOUT_SECONDS",
            0.05,
        )
        monkeypatch.setattr(
            website_resolution_worker.website_finder.WebsiteFinder,
            "resolve_website",
            slow_resolve_website,
        )

        worker = await website_resolution_worker.WebsiteResolutionWorker.create_and_start(
            store,
            config,
            set(),
            listings_csv_lock,
        )
        worker.try_enqueue(_listing("SLOW/USDT"))
        worker.try_enqueue(_listing("SKIP/USDT"))
        resolved_count = await worker.shutdown()

        assert resolved_count == 0


class TestWebsiteResolutionWorkerConsumerLoop:
    @pytest.mark.asyncio
    async def test_continues_after_resolve_failure(self, tmp_path: pathlib.Path, monkeypatch):
        csv_path = tmp_path / "listings.csv"
        config = _config(csv_path)
        listings_csv_lock = asyncio.Lock()
        store = listings_store.ListingsStore(csv_path)

        _patch_worker_infrastructure(monkeypatch, mexc_website=None)

        async def fake_resolve_website(self, coingecko_client, full_name, base_symbol):
            if base_symbol == "FAIL":
                raise RuntimeError("CoinGecko lookup failed")
            return website_resolution.WebsiteResolutionResult(
                website=f"https://{base_symbol.lower()}.example/",
                coingecko_id=base_symbol.lower(),
            )

        monkeypatch.setattr(
            website_resolution_worker.website_finder.WebsiteFinder,
            "resolve_website",
            fake_resolve_website,
        )

        worker = await website_resolution_worker.WebsiteResolutionWorker.create_and_start(
            store,
            config,
            set(),
            listings_csv_lock,
        )
        worker.try_enqueue(_listing("FAIL/USDT"))
        worker.try_enqueue(_listing("OK/USDT"))
        resolved_count = await worker.shutdown()

        assert resolved_count == 1
        assert worker._failed_count == 1
        saved = store.load_all()[_listing("OK/USDT").key()]
        assert saved.website == "https://ok.example/"


class TestWebsiteResolutionWorkerExchangeFallback:
    @pytest.mark.asyncio
    async def test_uses_exchange_website_without_calling_coingecko(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        config = _config(csv_path)
        listings_csv_lock = asyncio.Lock()
        store = listings_store.ListingsStore(csv_path)
        listing = _listing("OPTIMUS/USDT")

        _patch_worker_infrastructure(
            monkeypatch,
            mexc_website="https://www.optimustoken.io/",
        )

        async def fake_resolve_website(self, coingecko_client, full_name, base_symbol):
            raise AssertionError("CoinGecko should not be called when exchange resolves website")

        monkeypatch.setattr(
            website_resolution_worker.website_finder.WebsiteFinder,
            "resolve_website",
            fake_resolve_website,
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
        assert saved.website == "https://www.optimustoken.io/"
        assert saved.coingecko_id is None

    @pytest.mark.asyncio
    async def test_mexc_failure_enqueues_coingecko_fallback(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        config = _config(csv_path)
        listings_csv_lock = asyncio.Lock()
        store = listings_store.ListingsStore(csv_path)
        listing = _listing("FALLBACK/USDT")

        _patch_worker_infrastructure(monkeypatch, mexc_website=None)

        async def fake_resolve_website(self, coingecko_client, full_name, base_symbol):
            return website_resolution.WebsiteResolutionResult(
                website="https://fallback.example/",
                coingecko_id="fallback",
            )

        monkeypatch.setattr(
            website_resolution_worker.website_finder.WebsiteFinder,
            "resolve_website",
            fake_resolve_website,
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
        assert saved.website == "https://fallback.example/"
        assert saved.coingecko_id == "fallback"

    @pytest.mark.asyncio
    async def test_awaits_mexc_throttle_before_resolve(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        config = _config(csv_path)
        listings_csv_lock = asyncio.Lock()
        store = listings_store.ListingsStore(csv_path)
        listing = _listing("THROTTLE/USDT")

        _patch_worker_infrastructure(
            monkeypatch,
            mexc_website="https://throttle.example/",
        )

        worker = await website_resolution_worker.WebsiteResolutionWorker.create_and_start(
            store,
            config,
            {listing.key()},
            listings_csv_lock,
        )
        worker.try_enqueue(listing)
        await worker.shutdown()

        worker._mexc_throttle_client.throttle.assert_awaited_once_with(1)

