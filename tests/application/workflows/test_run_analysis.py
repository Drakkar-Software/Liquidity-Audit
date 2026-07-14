import asyncio
import pathlib
import time
from contextlib import asynccontextmanager

import ccxt
import mock
import pytest

import tests.fixtures.daily_selection_fixtures as daily_selection_fixtures
import tests.fixtures.delisting_risk_fixtures as delisting_risk_fixtures
import tests.fixtures.health_label_fixtures as health_label_fixtures
import liquidity_audit.application.shared.analysis_exchange_processor as analysis_exchange_processor
import liquidity_audit.application.shared.delisted_listing as delisted_listing
import liquidity_audit.application.shared.fetch_pair_metrics as fetch_pair_metrics
import liquidity_audit.application.shared.reanalyze_stored_raw as reanalyze_stored_raw
import liquidity_audit.application.workflows.run_analysis as run_analysis_workflow
import liquidity_audit.infrastructure.analysis_store as analysis_store
import liquidity_audit.infrastructure.ccxt_client as ccxt_client
import liquidity_audit.config as app_config
import liquidity_audit.domain.analysis.delisting_risk as delisting_risk
import liquidity_audit.infrastructure.listings_store as listings_store
import liquidity_audit.infrastructure.market_cap_fetch as market_cap_fetch
import liquidity_audit.domain.models as models
import liquidity_audit.domain.analysis.pair_analysis as token_analysis


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


def _listing(
    exchange: str = "bitmart",
    symbol: str = "PITCH/USDT",
    **fields,
) -> models.ListingRecord:
    base, quote = symbol.split("/")
    defaults = {
        "exchange": exchange,
        "symbol": symbol,
        "base": base,
        "quote": quote,
        "full_name": base,
    }
    defaults.update(fields)
    return models.ListingRecord(**defaults)


def _minimal_raw_metrics(
    exchange: str = "bitmart",
    symbol: str = "PITCH/USDT",
) -> token_analysis.ExtendedRawMetrics:
    return token_analysis.ExtendedRawMetrics(
        exchange=exchange,
        symbol=symbol,
        full_name=symbol.split("/")[0],
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


class TestRunAnalysisParallelExchanges:
    @pytest.mark.asyncio
    async def test_processes_all_exchanges_concurrently(self, tmp_path: pathlib.Path, monkeypatch):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)

        invoked_exchanges: list[str] = []
        overlap_detected = False
        active_count = 0

        async def fake_process_exchange(
            exchange_name,
            listings,
            config,
            store,
            listings_store_instance,
            listings_csv_lock,
            run_started_at,
            **kwargs,
        ):
            nonlocal active_count, overlap_detected
            invoked_exchanges.append(exchange_name)
            active_count += 1
            if active_count > 1:
                overlap_detected = True
            await asyncio.sleep(0.05)
            active_count -= 1
            return [], [], {}, 0, 0

        monkeypatch.setattr(
            analysis_exchange_processor,
            "process_exchange",
            fake_process_exchange,
        )
        monkeypatch.setattr(
            analysis_store.AnalysisStore,
            "save_manifest",
            lambda self, payload: None,
        )
        monkeypatch.setattr(
            listings_store.ListingsStore,
            "load_all",
            lambda self: {},
        )

        started_at = time.perf_counter()
        await run_analysis_workflow.run(config)
        elapsed_seconds = time.perf_counter() - started_at

        assert set(invoked_exchanges) == {"mexc", "bitmart"}
        assert overlap_detected is True
        assert elapsed_seconds < 0.09


class TestProcessExchangeHandleBadSymbol:
    @pytest.mark.asyncio
    async def test_first_bad_symbol_logs_warning_and_sets_delisted_at(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
        caplog,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)
        listing = _listing()
        listings_store_instance = listings_store.ListingsStore(csv_path)
        store = analysis_store.AnalysisStore(output_dir)
        listings_csv_lock = asyncio.Lock()

        async def raise_bad_symbol(*args, **kwargs):
            raise ccxt.BadSymbol("PITCH/USDT does not exist")

        monkeypatch.setattr(
            fetch_pair_metrics,
            "fetch_pair_raw_metrics",
            raise_bad_symbol,
        )
        monkeypatch.setattr(ccxt_client, "exchange_client", _fake_exchange_client)
        monkeypatch.setattr(
            listings_store.ListingsStore,
            "append_or_update",
            listings_store_instance.append_or_update,
        )

        with caplog.at_level("WARNING"):
            (
                universe,
                failures,
                _pair_analyses,
                newly_delisted,
                skipped_delisted,
            ) = await analysis_exchange_processor.process_exchange(
                "bitmart",
                [listing],
                config,
                store,
                listings_store_instance,
                listings_csv_lock,
                "2026-06-12T00:00:00+00:00",
            )

        assert universe == []
        assert failures == []
        assert newly_delisted == 1
        assert skipped_delisted == 0
        assert listing.delisted_at is not None
        assert any("Delisted bitmart PITCH/USDT" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_already_delisted_skips_fetch_without_warning(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
        caplog,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)
        listing = _listing(delisted_at="2026-06-12T00:00:00+00:00")
        listings_store_instance = listings_store.ListingsStore(csv_path)
        store = analysis_store.AnalysisStore(output_dir)
        listings_csv_lock = asyncio.Lock()
        fetch_calls = 0

        async def count_fetch_calls(*args, **kwargs):
            nonlocal fetch_calls
            fetch_calls += 1
            return _minimal_raw_metrics(), [], None

        monkeypatch.setattr(
            fetch_pair_metrics,
            "fetch_pair_raw_metrics",
            count_fetch_calls,
        )
        monkeypatch.setattr(ccxt_client, "exchange_client", _fake_exchange_client)

        with caplog.at_level("WARNING"):
            (
                _universe,
                failures,
                _pair_analyses,
                newly_delisted,
                skipped_delisted,
            ) = await analysis_exchange_processor.process_exchange(
                "bitmart",
                [listing],
                config,
                store,
                listings_store_instance,
                listings_csv_lock,
                "2026-06-12T00:00:00+00:00",
            )

        assert fetch_calls == 0
        assert failures == []
        assert newly_delisted == 0
        assert skipped_delisted == 1
        assert not any("Delisted" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_past_retention_deletes_pair_json(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)
        listing = _listing(delisted_at="2020-01-01T00:00:00+00:00")
        listings_store_instance = listings_store.ListingsStore(csv_path)
        store = analysis_store.AnalysisStore(output_dir)
        listings_csv_lock = asyncio.Lock()
        pair_json_path = store.pair_json_path("bitmart", "PITCH/USDT")
        pair_json_path.parent.mkdir(parents=True, exist_ok=True)
        pair_json_path.write_text("{}", encoding="utf-8")
        fetch_calls = 0

        async def count_fetch_calls(*args, **kwargs):
            nonlocal fetch_calls
            fetch_calls += 1
            return _minimal_raw_metrics(), [], None

        monkeypatch.setattr(
            fetch_pair_metrics,
            "fetch_pair_raw_metrics",
            count_fetch_calls,
        )
        monkeypatch.setattr(ccxt_client, "exchange_client", _fake_exchange_client)

        (
            _universe,
            failures,
            _pair_analyses,
            newly_delisted,
            skipped_delisted,
        ) = await analysis_exchange_processor.process_exchange(
            "bitmart",
            [listing],
            config,
            store,
            listings_store_instance,
            listings_csv_lock,
            "2026-06-12T00:00:00+00:00",
        )

        assert fetch_calls == 0
        assert failures == []
        assert newly_delisted == 0
        assert skipped_delisted == 1
        assert not pair_json_path.is_file()
        assert listing.delisted_at == "2020-01-01T00:00:00+00:00"


class TestProcessExchangeAnalyzesEveryActiveListing:
    @pytest.mark.asyncio
    async def test_fetches_even_when_recently_analyzed(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)
        listing = _listing(last_analyzed_at="2026-06-13T14:00:00+00:00")
        listings_store_instance = listings_store.ListingsStore(csv_path)
        store = analysis_store.AnalysisStore(output_dir)
        listings_csv_lock = asyncio.Lock()
        fetch_calls = 0

        async def count_fetch_calls(*args, **kwargs):
            nonlocal fetch_calls
            fetch_calls += 1
            return _minimal_raw_metrics(), [delisting_risk.LABEL_LOW_VOLUME], 140.0

        monkeypatch.setattr(
            fetch_pair_metrics,
            "fetch_pair_raw_metrics",
            count_fetch_calls,
        )
        monkeypatch.setattr(ccxt_client, "exchange_client", _fake_exchange_client)

        (
            universe,
            failures,
            pair_analyses,
            _newly_delisted,
            _skipped_delisted,
        ) = await analysis_exchange_processor.process_exchange(
            "bitmart",
            [listing],
            config,
            store,
            listings_store_instance,
            listings_csv_lock,
            "2026-06-13T14:00:00+00:00",
        )

        assert fetch_calls == 1
        assert len(universe) == 1
        assert failures == []
        assert pair_analyses["PITCH/USDT"]["analysis"]["delisting_risk"] != []


class TestProcessExchangeWebsiteWorkerEnqueue:
    @pytest.mark.asyncio
    async def test_enqueues_low_health_listing_after_successful_fetch(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)
        listing = _listing(website=None, website_resolution_status=None)
        listings_store_instance = listings_store.ListingsStore(csv_path)
        store = analysis_store.AnalysisStore(output_dir)
        listings_csv_lock = asyncio.Lock()
        enqueued_keys: list[tuple[str, str]] = []

        class FakeWebsiteWorker:
            def try_enqueue(self, listing_record: models.ListingRecord) -> None:
                enqueued_keys.append(listing_record.key())

        low_health_metrics = _minimal_raw_metrics()
        low_health_metrics.is_low_health = True

        async def return_low_health_metrics(*args, **kwargs):
            return low_health_metrics, [], None

        monkeypatch.setattr(
            fetch_pair_metrics,
            "fetch_pair_raw_metrics",
            return_low_health_metrics,
        )
        monkeypatch.setattr(ccxt_client, "exchange_client", _fake_exchange_client)
        monkeypatch.setattr(
            listings_store.ListingsStore,
            "append_or_update",
            listings_store_instance.append_or_update,
        )

        await analysis_exchange_processor.process_exchange(
            "bitmart",
            [listing],
            config,
            store,
            listings_store_instance,
            listings_csv_lock,
            "2026-06-12T00:00:00+00:00",
            website_worker=FakeWebsiteWorker(),
        )

        assert enqueued_keys == [listing.key()]
        assert listing.is_low_health is True
        assert listing.bid_levels == low_health_metrics.bid_levels


class TestClearDelistedIfRelisted:
    def test_clears_delisted_at_when_set(self):
        listing = _listing(delisted_at="2026-06-01T00:00:00+00:00")
        assert delisted_listing.clear_delisted_if_relisted(listing) is True
        assert listing.delisted_at is None

    def test_returns_false_when_not_delisted(self):
        listing = _listing()
        assert delisted_listing.clear_delisted_if_relisted(listing) is False


class TestRunAnalysisManifestDelistedCounters:
    @pytest.mark.asyncio
    async def test_manifest_includes_delisted_counters(self, tmp_path: pathlib.Path, monkeypatch):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)
        saved_manifest: dict = {}

        async def fake_process_exchange(*args, **kwargs):
            return [], [], {}, 1, 3

        def capture_manifest(self, payload):
            saved_manifest.update(payload)

        monkeypatch.setattr(
            analysis_exchange_processor,
            "process_exchange",
            fake_process_exchange,
        )
        monkeypatch.setattr(analysis_store.AnalysisStore, "save_manifest", capture_manifest)
        monkeypatch.setattr(
            listings_store.ListingsStore,
            "load_all",
            lambda self: {},
        )

        await run_analysis_workflow.run(config)

        assert saved_manifest["pairs_delisted"] == 2
        assert saved_manifest["pairs_delisted_skipped"] == 6


class TestRunAnalysisMarketCapBatch:
    @pytest.mark.asyncio
    async def test_fetches_market_caps_once_and_passes_task_to_process_exchange(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)
        listings = [
            _listing(exchange="mexc", symbol="BTC/USDT"),
            _listing(exchange="bitmart", symbol="ETH/USDT"),
        ]
        fetch_calls: list[list[models.ListingRecord]] = []
        process_exchange_tasks: list[object] = []

        async def fake_fetch_market_cap_by_symbol_for_listings(config_arg, listings_arg):
            fetch_calls.append(listings_arg)
            return {"BTC/USDT": 1_000_000.0, "ETH/USDT": 500_000.0}

        async def fake_process_exchange(*args, **kwargs):
            process_exchange_tasks.append(kwargs.get("market_cap_task"))
            return [], [], {}, 0, 0

        monkeypatch.setattr(
            market_cap_fetch,
            "fetch_market_cap_by_symbol_for_listings",
            fake_fetch_market_cap_by_symbol_for_listings,
        )
        monkeypatch.setattr(
            analysis_exchange_processor,
            "process_exchange",
            fake_process_exchange,
        )
        monkeypatch.setattr(
            listings_store.ListingsStore,
            "load_all",
            lambda self: {listing.key(): listing for listing in listings},
        )
        monkeypatch.setattr(analysis_store.AnalysisStore, "save_manifest", lambda self, payload: None)

        await run_analysis_workflow.run(config)

        assert len(fetch_calls) == 1
        assert fetch_calls[0] == listings
        assert len(process_exchange_tasks) == 2
        assert process_exchange_tasks[0] is process_exchange_tasks[1]
        assert process_exchange_tasks[0] is not None


class TestReanalyzeFromStoredRaw:
    @pytest.mark.asyncio
    async def test_rebuilds_analysis_and_rankings_without_fetch(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)
        listing = _listing()
        listings_store.ListingsStore(csv_path).append_or_update([listing])

        store = analysis_store.AnalysisStore(output_dir)
        raw_metrics = _minimal_raw_metrics()
        store.save_pair_analysis("bitmart", "PITCH/USDT", {"raw": raw_metrics.to_dict()})

        async def fail_fetch(*args, **kwargs):
            raise AssertionError("fetch_pair_raw_metrics must not be called during reanalyze")

        monkeypatch.setattr(
            fetch_pair_metrics,
            "fetch_pair_raw_metrics",
            fail_fetch,
        )
        monkeypatch.setattr(ccxt_client, "exchange_client", _fake_exchange_client)

        reanalyzed_keys, stats = await reanalyze_stored_raw.reanalyze_from_stored_raw(config)

        assert ("bitmart", "PITCH/USDT") in reanalyzed_keys
        assert stats["pairs_reanalyzed"] == 1
        assert stats["pairs_skipped_no_json"] == 0

        pair_payload = store.load_pair_analysis("bitmart", "PITCH/USDT")
        assert pair_payload is not None
        assert "analysis" in pair_payload
        assert pair_payload["analysis"]["score_100"] == 50
        assert len(pair_payload["analysis"]["delisting_risk"]) == 1
        assert pair_payload["analysis"]["delisting_risk"][0]["title"] == "Low depth"

        rankings_path = store.rankings_json_path("bitmart")
        assert rankings_path.is_file()

        updated_listing = listings_store.ListingsStore(csv_path).load_all()[
            ("bitmart", "PITCH/USDT")
        ]
        assert updated_listing.last_analyzed_at is not None
        assert updated_listing.analysis_json_path is not None

    @pytest.mark.asyncio
    async def test_fetches_market_caps_once_for_all_exchanges(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        csv_path = tmp_path / "listings.csv"
        output_dir = tmp_path / "analysis"
        config = _analysis_config(csv_path, output_dir)
        mexc_listing = _listing(exchange="mexc", symbol="BTC/USDT", coingecko_id="bitcoin")
        bitmart_listing = _listing(exchange="bitmart", symbol="ETH/USDT", coingecko_id="ethereum")
        listings_store.ListingsStore(csv_path).append_or_update([
            mexc_listing,
            bitmart_listing,
        ])

        store = analysis_store.AnalysisStore(output_dir)
        store.save_pair_analysis(
            "mexc",
            "BTC/USDT",
            {"raw": _minimal_raw_metrics("mexc", "BTC/USDT").to_dict()},
        )
        store.save_pair_analysis(
            "bitmart",
            "ETH/USDT",
            {"raw": _minimal_raw_metrics("bitmart", "ETH/USDT").to_dict()},
        )

        fetch_calls: list[list[models.ListingRecord]] = []

        async def fake_fetch_market_cap_by_symbol_for_listings(config_arg, listings_arg):
            fetch_calls.append(listings_arg)
            return {
                "BTC/USDT": 1_000_000_000_000.0,
                "ETH/USDT": 400_000_000_000.0,
            }

        monkeypatch.setattr(
            market_cap_fetch,
            "fetch_market_cap_by_symbol_for_listings",
            fake_fetch_market_cap_by_symbol_for_listings,
        )

        await reanalyze_stored_raw.reanalyze_from_stored_raw(config)

        assert len(fetch_calls) == 1
        assert {listing.symbol for listing in fetch_calls[0]} == {"BTC/USDT", "ETH/USDT"}
