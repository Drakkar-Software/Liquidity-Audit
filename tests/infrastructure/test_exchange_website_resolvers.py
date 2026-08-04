import asyncio
import json
import mock
import pytest
import aiohttp

import liquidity_audit.domain.website.website_resolution as website_resolution
import liquidity_audit.infrastructure.exchange_website_resolvers as exchange_website_resolvers


class TestNormalizeWebsiteUrl:
    def test_returns_https_url_when_scheme_missing(self):
        assert exchange_website_resolvers.normalize_website_url("example.com") == "https://example.com"

    def test_returns_none_for_empty_string(self):
        assert exchange_website_resolvers.normalize_website_url("") is None

    def test_preserves_existing_https_url(self):
        assert (
            exchange_website_resolvers.normalize_website_url("https://www.optimustoken.io/")
            == "https://www.optimustoken.io/"
        )


class TestWebsiteFromMexcPayload:
    def test_extracts_ws_field(self):
        payload = {
            "code": 0,
            "data": {"ws": "https://www.optimustoken.io/"},
        }
        assert (
            exchange_website_resolvers._website_from_mexc_payload(payload)
            == "https://www.optimustoken.io/"
        )

    def test_returns_none_when_code_not_zero(self):
        payload = {"code": 500, "data": {"ws": "https://example.com"}}
        assert exchange_website_resolvers._website_from_mexc_payload(payload) is None

    def test_returns_none_when_ws_missing(self):
        payload = {"code": 0, "data": {}}
        assert exchange_website_resolvers._website_from_mexc_payload(payload) is None


class TestWebsiteFromCoinexPayload:
    def test_extracts_website_url_field(self):
        payload = {
            "code": 0,
            "data": [{"website_url": "https://aioz.network"}],
        }
        assert (
            exchange_website_resolvers._website_from_coinex_payload(payload)
            == "https://aioz.network"
        )

    def test_returns_none_when_data_empty(self):
        payload = {"code": 0, "data": []}
        assert exchange_website_resolvers._website_from_coinex_payload(payload) is None


class TestWebsiteFromWeexHtml:
    def test_extracts_website_link_from_links_section(self):
        html = (
            "<section><h3>Links</h3><ul>"
            "<li><a href=\"https://bitcoin.org/\" target=\"_blank\">Website</a></li>"
            "<li><a href=\"https://bitcoin.org/bitcoin.pdf\">Whitepaper</a></li>"
            "</ul></section>"
        )
        assert (
            exchange_website_resolvers._website_from_weex_html(html)
            == "https://bitcoin.org/"
        )

    def test_returns_none_when_links_section_missing(self):
        assert exchange_website_resolvers._website_from_weex_html("<html></html>") is None

    def test_returns_none_when_website_anchor_missing(self):
        html = "<h3>Links</h3><ul><li><a href=\"https://example.com\">Explorer</a></li></ul>"
        assert exchange_website_resolvers._website_from_weex_html(html) is None


class TestResolveForListing:
    @pytest.mark.asyncio
    async def test_returns_mexc_website_for_mexc_listing(self, monkeypatch):
        listing = mock.Mock()
        listing.exchange = "mexc"
        listing.symbol = "OPTIMUS/USDT"
        listing.base = "OPTIMUS"

        session = mock.AsyncMock()
        fake_resolve_mexc = mock.AsyncMock(return_value="https://www.optimustoken.io/")
        monkeypatch.setattr(
            exchange_website_resolvers,
            "resolve_mexc_website",
            fake_resolve_mexc,
        )

        website = await exchange_website_resolvers.resolve_for_listing(listing, session)

        assert website == "https://www.optimustoken.io/"
        fake_resolve_mexc.assert_awaited_once_with("OPTIMUS", session)

    @pytest.mark.asyncio
    async def test_returns_weex_website_for_weex_listing(self, monkeypatch):
        listing = mock.Mock()
        listing.exchange = "weex"
        listing.symbol = "BTC/USDT"
        listing.base = "BTC"
        listing.quote = "USDT"

        session = mock.AsyncMock()
        fake_resolve_weex = mock.AsyncMock(return_value="https://bitcoin.org/")
        monkeypatch.setattr(
            exchange_website_resolvers,
            "resolve_weex_website",
            fake_resolve_weex,
        )

        website = await exchange_website_resolvers.resolve_for_listing(listing, session)

        assert website == "https://bitcoin.org/"
        fake_resolve_weex.assert_awaited_once_with("BTC", "USDT", session)

    @pytest.mark.asyncio
    async def test_returns_none_for_unsupported_exchange(self):
        listing = mock.Mock()
        listing.exchange = "unknown"
        listing.symbol = "AAA/USDT"
        listing.base = "AAA"
        session = mock.AsyncMock()

        website = await exchange_website_resolvers.resolve_for_listing(listing, session)

        assert website is None


class TestFetchJsonMexcFallback:
    @pytest.mark.asyncio
    async def test_uses_urllib_fallback_on_aiohttp_403(self, monkeypatch):
        session = mock.AsyncMock()
        aiohttp_error = aiohttp.ClientResponseError(
            request_info=mock.Mock(),
            history=(),
            status=403,
            message="Forbidden",
        )
        monkeypatch.setattr(
            exchange_website_resolvers,
            "_fetch_json_aiohttp",
            mock.AsyncMock(side_effect=aiohttp_error),
        )
        monkeypatch.setattr(
            exchange_website_resolvers,
            "_fetch_json_urllib",
            mock.Mock(return_value={"code": 0, "data": {"ws": "https://mexc.example/"}}),
        )

        payload = await exchange_website_resolvers._fetch_json_mexc(
            "https://www.mexc.com/api/test",
            session,
        )

        assert payload == {"code": 0, "data": {"ws": "https://mexc.example/"}}
        exchange_website_resolvers._fetch_json_urllib.assert_called_once_with(
            "https://www.mexc.com/api/test",
            exchange_website_resolvers.MEXC_HTTP_HEADERS,
        )

    @pytest.mark.asyncio
    async def test_raises_when_both_aiohttp_and_urllib_fail(self, monkeypatch):
        session = mock.AsyncMock()
        aiohttp_error = aiohttp.ClientResponseError(
            request_info=mock.Mock(),
            history=(),
            status=403,
            message="Forbidden",
        )
        monkeypatch.setattr(
            exchange_website_resolvers,
            "_fetch_json_aiohttp",
            mock.AsyncMock(side_effect=aiohttp_error),
        )
        monkeypatch.setattr(
            exchange_website_resolvers,
            "_fetch_json_urllib",
            mock.Mock(side_effect=json.JSONDecodeError("bad", "doc", 0)),
        )

        with pytest.raises(aiohttp.ClientResponseError):
            await exchange_website_resolvers._fetch_json_mexc(
                "https://www.mexc.com/api/test",
                session,
            )


class TestResolveListingWebsite:
    @pytest.mark.asyncio
    async def test_skips_coingecko_when_exchange_returns_website(self, monkeypatch):
        listing = mock.Mock()
        listing.exchange = "mexc"
        listing.symbol = "OPTIMUS/USDT"
        listing.base = "OPTIMUS"
        listing.full_name = "Optimus"

        website_finder = mock.Mock()
        website_finder.resolve_website = mock.AsyncMock()
        coingecko_client = mock.Mock()
        coingecko_lock = mock.AsyncMock()

        monkeypatch.setattr(
            exchange_website_resolvers,
            "resolve_for_listing",
            mock.AsyncMock(return_value="https://www.optimustoken.io/"),
        )

        resolution = await exchange_website_resolvers.resolve_listing_website(
            listing,
            website_finder,
            coingecko_client,
            coingecko_lock,
        )

        assert resolution.website == "https://www.optimustoken.io/"
        assert resolution.coingecko_id is None
        website_finder.resolve_website.assert_not_called()

    @pytest.mark.asyncio
    async def test_falls_back_to_coingecko_when_exchange_returns_none(self, monkeypatch):
        listing = mock.Mock()
        listing.exchange = "mexc"
        listing.symbol = "NEW/USDT"
        listing.base = "NEW"
        listing.full_name = "New Token"

        website_finder = mock.Mock()
        website_finder.resolve_website = mock.AsyncMock(
            return_value=website_resolution.WebsiteResolutionResult(
                website="https://new.example/",
                coingecko_id="new",
            ),
        )
        coingecko_client = mock.Mock()
        coingecko_lock = asyncio.Lock()

        monkeypatch.setattr(
            exchange_website_resolvers,
            "resolve_for_listing",
            mock.AsyncMock(return_value=None),
        )

        resolution = await exchange_website_resolvers.resolve_listing_website(
            listing,
            website_finder,
            coingecko_client,
            coingecko_lock,
        )

        website_finder.resolve_website.assert_awaited_once_with(
            coingecko_client,
            "New Token",
            "NEW",
        )
        assert resolution.website == "https://new.example/"
        assert resolution.coingecko_id == "new"
