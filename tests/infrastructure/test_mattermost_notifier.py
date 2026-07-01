import logging

import pytest

import liquidity_audit.domain.models as models
import liquidity_audit.infrastructure.mattermost_notifier as mattermost_notifier


def _listing(symbol: str, is_low_health: bool = False) -> models.ListingRecord:
    return models.ListingRecord(
        exchange="mexc",
        symbol=symbol,
        base=symbol.split("/")[0],
        quote="USDT",
        full_name="Test Token",
        bid_levels=1,
        ask_levels=1,
        bid_depth_quote=10.0,
        ask_depth_quote=10.0,
        volume_quote=1000.0,
        liquidity_score=0.42,
        is_low_health=is_low_health,
        health_label_primary="few_orders" if is_low_health else None,
    )


def _selection(
    symbol: str,
    *,
    is_new_listing: bool = False,
    is_low_health: bool = True,
) -> models.DailyProjectSelection:
    return models.DailyProjectSelection(
        record=_listing(symbol, is_low_health=is_low_health),
        selection_tier=models.SELECTION_TIER_EXISTING_DIVERSIFIED,
        is_new_listing=is_new_listing,
    )


class TestFormatSelectedProjectMessage:
    def test_includes_ticker_exchange_topic_and_health(self):
        selection = _selection("LOW/USDT", is_new_listing=True)
        message = mattermost_notifier._format_selected_project_message(selection)
        assert "**LOW** · mexc · new listing" in message
        assert "- Pair: LOW/USDT" in message
        assert "few_orders" in message

    def test_uses_bad_health_topic_for_existing_selection(self):
        selection = _selection("LOW/USDT", is_new_listing=False)
        message = mattermost_notifier._format_selected_project_message(selection)
        assert "**LOW** · mexc · bad health" in message


class TestFormatRunNotificationText:
    def test_joins_summary_and_daily_selection_sections(self):
        daily_selection = _selection("LOW/USDT", is_new_listing=False)
        run_summary = models.RunSummary(
            new_listings_total=0,
            new_low_health_count=0,
            selections_proposed_total=1,
            selections_proposed_new=0,
            selections_proposed_existing=1,
            failed_enrichments_count=0,
        )
        notification_text = mattermost_notifier.format_run_notification_text(
            run_summary,
            [daily_selection],
        )
        assert "Run summary" in notification_text
        assert "Daily project selections (1)" in notification_text
        assert "**LOW** · mexc · bad health" in notification_text
        assert '**Enrich selected**' in notification_text
        assert '`--projects-whitelist "mexc:LOW"`' in notification_text

    def test_omits_enrich_line_when_no_selections(self):
        run_summary = models.RunSummary(
            new_listings_total=0,
            new_low_health_count=0,
            selections_proposed_total=0,
            selections_proposed_new=0,
            selections_proposed_existing=0,
            failed_enrichments_count=0,
        )
        notification_text = mattermost_notifier.format_run_notification_text(
            run_summary,
            [],
        )
        assert "Enrich selected" not in notification_text
        assert "--projects-whitelist" not in notification_text


class TestFormatProjectsWhitelistArg:
    def test_joins_exchange_base_pairs(self):
        first_selection = _selection("BTC/USDT")
        first_selection.record.exchange = "mexc"
        second_selection = _selection("LOW/USDT")
        second_selection.record.exchange = "bitmart"
        assert mattermost_notifier.format_projects_whitelist_arg([
            first_selection,
            second_selection,
        ]) == "mexc:BTC,bitmart:LOW"

    def test_includes_website_domain_when_website_known(self):
        selection = _selection("DATA/USDT")
        selection.record.website = "https://datafdn.org/"
        assert mattermost_notifier.format_projects_whitelist_arg([selection]) == (
            "mexc:DATA@datafdn.org"
        )


class TestSendRunNotifications:
    @pytest.mark.asyncio
    async def test_posts_summary_and_daily_selections(self, monkeypatch, caplog):
        posted_payloads = []

        class FakeResponse:
            status = 200

            async def text(self):
                return ""

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

        class FakeSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def post(self, webhook_url, json=None):
                posted_payloads.append((webhook_url, json))
                return FakeResponse()

        monkeypatch.setattr(mattermost_notifier.aiohttp, "ClientSession", FakeSession)
        monkeypatch.setenv("MATTERMOST_WEBHOOK_URL", "https://mattermost.example/hooks/abc")

        daily_selection = _selection("LOW/USDT", is_new_listing=True)
        run_summary = models.RunSummary(
            new_listings_total=2,
            new_low_health_count=1,
            selections_proposed_total=1,
            selections_proposed_new=1,
            selections_proposed_existing=0,
            failed_enrichments_count=0,
        )
        with caplog.at_level(logging.INFO, logger=mattermost_notifier.__name__):
            await mattermost_notifier.send_run_notifications(
                run_summary,
                [daily_selection],
            )

        assert len(posted_payloads) == 1
        webhook_url, payload = posted_payloads[0]
        assert webhook_url == "https://mattermost.example/hooks/abc"
        assert "Run summary" in payload["text"]
        assert "**LOW** · mexc · new listing" in payload["text"]
        assert any(
            "Mattermost notification payload:" in record.message
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_logs_payload_without_posting_when_post_false(self, monkeypatch, caplog):
        post_called = False

        class FakeSession:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            def post(self, webhook_url, json=None):
                nonlocal post_called
                post_called = True
                raise AssertionError("post should not be called")

        monkeypatch.setattr(mattermost_notifier.aiohttp, "ClientSession", FakeSession)

        run_summary = models.RunSummary(
            new_listings_total=0,
            new_low_health_count=0,
            selections_proposed_total=0,
            selections_proposed_new=0,
            selections_proposed_existing=0,
            failed_enrichments_count=0,
        )
        with caplog.at_level(logging.INFO, logger=mattermost_notifier.__name__):
            await mattermost_notifier.send_run_notifications(
                run_summary,
                [],
                post=False,
            )

        assert post_called is False
        assert any(
            "Mattermost notification payload:" in record.message
            for record in caplog.records
        )
        assert any(
            "Mattermost notification skipped (identify-selected-only)" in record.message
            for record in caplog.records
        )


class TestLoadMattermostWebhookUrl:
    def test_returns_stripped_url_from_env(self, monkeypatch):
        monkeypatch.setenv("MATTERMOST_WEBHOOK_URL", "  https://mattermost.example/hooks/abc  ")

        assert mattermost_notifier.load_mattermost_webhook_url() == (
            "https://mattermost.example/hooks/abc"
        )

    def test_raises_when_env_missing(self, monkeypatch):
        monkeypatch.delenv("MATTERMOST_WEBHOOK_URL", raising=False)

        with pytest.raises(mattermost_notifier.MattermostConfigurationError, match="MATTERMOST_WEBHOOK_URL"):
            mattermost_notifier.load_mattermost_webhook_url()

    def test_raises_when_env_empty(self, monkeypatch):
        monkeypatch.setenv("MATTERMOST_WEBHOOK_URL", "   ")

        with pytest.raises(mattermost_notifier.MattermostConfigurationError, match="MATTERMOST_WEBHOOK_URL"):
            mattermost_notifier.load_mattermost_webhook_url()
