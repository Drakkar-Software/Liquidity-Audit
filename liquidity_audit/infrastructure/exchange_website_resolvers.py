import asyncio
import json
import logging
import re
import typing
import urllib.error
import urllib.parse
import urllib.request

import aiohttp

import liquidity_audit.domain.models as models
import liquidity_audit.domain.website.website_resolution as website_resolution
import liquidity_audit.infrastructure.website_finder as website_finder

_LOGGER = logging.getLogger(__name__)

MEXC_INTRODUCE_URL = (
    "https://www.mexc.com/api/platform/spot/market-v2/web/coin/introduce"
)
COINEX_ASSETS_INFO_URL = "https://api.coinex.com/v2/assets/info"
WEEX_SPOT_PAGE_URL = "https://www.weex.com/spot/{base}-{quote}"

_BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

MEXC_HTTP_HEADERS = {
    "User-Agent": _BROWSER_USER_AGENT,
    "Accept": "application/json",
    "Origin": "https://www.mexc.com",
    "Referer": "https://www.mexc.com/",
}

COINEX_HTTP_HEADERS = {
    "User-Agent": _BROWSER_USER_AGENT,
    "Accept": "application/json",
    "Origin": "https://www.coinex.com",
    "Referer": "https://www.coinex.com/",
}

WEEX_HTTP_HEADERS = {
    "User-Agent": _BROWSER_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml",
    "Origin": "https://www.weex.com",
    "Referer": "https://www.weex.com/",
}


def create_mexc_http_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(headers=MEXC_HTTP_HEADERS)


def create_coinex_http_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(headers=COINEX_HTTP_HEADERS)


def create_weex_http_session() -> aiohttp.ClientSession:
    return aiohttp.ClientSession(headers=WEEX_HTTP_HEADERS)


def normalize_website_url(url: str) -> typing.Optional[str]:
    stripped = url.strip()
    if not stripped:
        return None
    if not stripped.startswith(("http://", "https://")):
        stripped = f"https://{stripped}"
    parsed = urllib.parse.urlparse(stripped)
    if not parsed.netloc:
        return None
    return stripped


async def _fetch_json_aiohttp(
    url: str,
    session: aiohttp.ClientSession,
) -> typing.Any:
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
        response.raise_for_status()
        return await response.json(content_type=None)


def _fetch_json_urllib(url: str, headers: dict[str, str]) -> typing.Any:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


async def _fetch_json_mexc(url: str, session: aiohttp.ClientSession) -> typing.Any:
    try:
        return await _fetch_json_aiohttp(url, session)
    except aiohttp.ClientResponseError as error:
        if error.status != 403:
            raise
        _LOGGER.debug(
            "MEXC introduce aiohttp blocked (403), retrying with urllib: %s",
            url,
        )
        try:
            payload = await asyncio.to_thread(
                _fetch_json_urllib,
                url,
                MEXC_HTTP_HEADERS,
            )
            _LOGGER.debug("MEXC introduce urllib fallback succeeded for %s", url)
            return payload
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as fallback_error:
            _LOGGER.warning(
                "MEXC introduce urllib fallback failed for %s: %s",
                url,
                fallback_error,
            )
            raise error from fallback_error


def _website_from_mexc_payload(payload: typing.Any) -> typing.Optional[str]:
    if not isinstance(payload, dict):
        return None
    if payload.get("code") != 0:
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    website_url = data.get("ws")
    if not isinstance(website_url, str):
        return None
    return normalize_website_url(website_url)


def _website_from_coinex_payload(payload: typing.Any) -> typing.Optional[str]:
    if not isinstance(payload, dict):
        return None
    if payload.get("code") != 0:
        return None
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return None
    first_entry = data[0]
    if not isinstance(first_entry, dict):
        return None
    website_url = first_entry.get("website_url")
    if not isinstance(website_url, str):
        return None
    return normalize_website_url(website_url)


def _website_from_weex_html(html: str) -> typing.Optional[str]:
    links_block_match = re.search(r"<h3>Links</h3><ul>(.*?)</ul>", html, re.DOTALL)
    if links_block_match is None:
        return None
    website_match = re.search(
        r'<a href="(https?://[^"]+)"[^>]*>Website</a>',
        links_block_match.group(1),
    )
    if website_match is None:
        return None
    return normalize_website_url(website_match.group(1))


async def _fetch_text_aiohttp(
    url: str,
    session: aiohttp.ClientSession,
) -> str:
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
        response.raise_for_status()
        return await response.text()


async def resolve_mexc_website(
    base_symbol: str,
    session: aiohttp.ClientSession,
) -> typing.Optional[str]:
    encoded_coin_name = urllib.parse.quote(base_symbol.strip(), safe="")
    url = f"{MEXC_INTRODUCE_URL}?coinName={encoded_coin_name}"
    try:
        payload = await _fetch_json_mexc(url, session)
    except (aiohttp.ClientError, TimeoutError) as error:
        _LOGGER.warning(
            "MEXC introduce request failed for %s: %s",
            base_symbol,
            error,
        )
        return None
    website = _website_from_mexc_payload(payload)
    if website is None:
        _LOGGER.debug("MEXC introduce returned no website for %s", base_symbol)
    return website


async def resolve_coinex_website(
    base_symbol: str,
    session: aiohttp.ClientSession,
) -> typing.Optional[str]:
    encoded_currency = urllib.parse.quote(base_symbol.strip(), safe="")
    url = f"{COINEX_ASSETS_INFO_URL}?ccy={encoded_currency}"
    try:
        payload = await _fetch_json_aiohttp(url, session)
    except (aiohttp.ClientError, TimeoutError) as error:
        _LOGGER.warning(
            "CoinEx assets info request failed for %s: %s",
            base_symbol,
            error,
        )
        return None
    website = _website_from_coinex_payload(payload)
    if website is None:
        _LOGGER.debug("CoinEx assets info returned no website for %s", base_symbol)
    return website


async def resolve_weex_website(
    base_symbol: str,
    quote_symbol: str,
    session: aiohttp.ClientSession,
) -> typing.Optional[str]:
    base = base_symbol.strip()
    quote = quote_symbol.strip()
    if not base or not quote:
        return None
    url = WEEX_SPOT_PAGE_URL.format(
        base=urllib.parse.quote(base, safe=""),
        quote=urllib.parse.quote(quote, safe=""),
    )
    try:
        html = await _fetch_text_aiohttp(url, session)
    except (aiohttp.ClientError, TimeoutError) as error:
        _LOGGER.warning(
            "WEEX spot page request failed for %s/%s: %s",
            base,
            quote,
            error,
        )
        return None
    website = _website_from_weex_html(html)
    if website is None:
        _LOGGER.debug("WEEX spot page returned no website for %s/%s", base, quote)
    return website


async def resolve_exchange_website(
    exchange_name: str,
    base_symbol: str,
    session: aiohttp.ClientSession,
) -> typing.Optional[str]:
    normalized_exchange = exchange_name.strip().lower()
    if normalized_exchange == "mexc":
        return await resolve_mexc_website(base_symbol, session)
    if normalized_exchange == "coinex":
        return await resolve_coinex_website(base_symbol, session)
    return None


async def resolve_for_listing(
    listing: models.ListingRecord,
    session: aiohttp.ClientSession,
) -> typing.Optional[str]:
    base_symbol = listing.base
    if not base_symbol or not base_symbol.strip():
        return None
    normalized_exchange = listing.exchange.strip().lower()
    if normalized_exchange == "weex":
        quote_symbol = listing.quote
        if not quote_symbol or not quote_symbol.strip():
            return None
        website = await resolve_weex_website(
            base_symbol.strip(),
            quote_symbol.strip(),
            session,
        )
    else:
        website = await resolve_exchange_website(
            listing.exchange,
            base_symbol.strip(),
            session,
        )
    if website is not None:
        _LOGGER.info(
            "Exchange website resolved for %s %s via %s: %s",
            listing.exchange,
            listing.symbol,
            normalized_exchange,
            website,
        )
    return website


async def resolve_coingecko_website(
    listing: models.ListingRecord,
    website_finder: website_finder.WebsiteFinder,
    coingecko_client: typing.Any,
) -> website_resolution.WebsiteResolutionResult:
    return await website_finder.resolve_website(
        coingecko_client,
        listing.full_name,
        listing.base,
    )


async def resolve_listing_website(
    listing: models.ListingRecord,
    website_finder: website_finder.WebsiteFinder,
    coingecko_client: typing.Any,
    coingecko_lock: asyncio.Lock,
) -> website_resolution.WebsiteResolutionResult:
    exchange_name = listing.exchange.strip().lower()
    if exchange_name == "mexc":
        async with create_mexc_http_session() as session:
            exchange_website = await resolve_for_listing(listing, session)
    elif exchange_name == "coinex":
        async with create_coinex_http_session() as session:
            exchange_website = await resolve_for_listing(listing, session)
    elif exchange_name == "weex":
        async with create_weex_http_session() as session:
            exchange_website = await resolve_for_listing(listing, session)
    else:
        exchange_website = None
    if exchange_website:
        return website_resolution.WebsiteResolutionResult(
            website=exchange_website,
            coingecko_id=None,
        )
    async with coingecko_lock:
        return await resolve_coingecko_website(
            listing,
            website_finder,
            coingecko_client,
        )
