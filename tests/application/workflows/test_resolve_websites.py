import logging
import pathlib

import mock
import pytest

import tests.fixtures.daily_selection_fixtures as daily_selection_fixtures
import tests.fixtures.delisting_risk_fixtures as delisting_risk_fixtures
import liquidity_audit.application.workflows.resolve_websites as resolve_websites_workflow
import liquidity_audit.config as app_config
import liquidity_audit.domain.models as models
import liquidity_audit.domain.website.website_resolution as website_resolution
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


def _listing(symbol: str = "NEW/USDT") -> models.ListingRecord:
    base = symbol.split("/")[0]
    return models.ListingRecord(
        exchange="mexc",
        symbol=symbol,
        base=base,
        quote="USDT",
        full_name=f"{base} Token",
        bid_levels=2,
        is_low_health=True,
    )


class TestResolveWebsitesForSelectionCandidates:
    @pytest.mark.asyncio
    async def test_logs_batch_progress(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
        caplog: pytest.LogCaptureFixture,
    ):
        csv_path = tmp_path / "listings.csv"
        config = _config(csv_path)
        listing = _listing()
        store = listings_store.ListingsStore(csv_path)
        store.append_or_update([listing])

        async def fake_load_coingecko_index(self, coingecko_client):
            return None

        async def fake_resolve_website(self, coingecko_client, full_name, base_symbol):
            return website_resolution.WebsiteResolutionResult(
                website="https://new.example/",
                coingecko_id="new",
            )

        monkeypatch.setattr(
            resolve_websites_workflow.website_finder.WebsiteFinder,
            "load_coingecko_index",
            fake_load_coingecko_index,
        )
        monkeypatch.setattr(
            resolve_websites_workflow.website_finder.WebsiteFinder,
            "resolve_website",
            fake_resolve_website,
        )
        monkeypatch.setattr(
            resolve_websites_workflow.ccxt_client,
            "create_exchange",
            lambda *args, **kwargs: mock.AsyncMock(),
        )

        with caplog.at_level(logging.INFO):
            resolved_count = await resolve_websites_workflow.resolve_websites_for_selection_candidates(
                store,
                config,
                set(),
            )

        messages = [record.message for record in caplog.records]
        assert resolved_count == 1
        assert any("Loaded 1 listing(s), 1 need CoinGecko website resolution" in message for message in messages)
        assert any("CoinGecko index loaded, resolving 1 listing(s)" in message for message in messages)
        assert any("CoinGecko website enrichment progress: 1/1 (100%)" in message for message in messages)
        assert any("Saving 1 resolved listing(s) to listings.csv" in message for message in messages)
