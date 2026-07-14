import typing

import liquidity_audit.config as app_config
import liquidity_audit.domain.models as models
import liquidity_audit.infrastructure.ccxt_client as ccxt_client
import liquidity_audit.infrastructure.website_finder as website_finder


def _coingecko_vs_currency(coingecko_client) -> str:
    client_options = getattr(coingecko_client, "options", {}) or {}
    vs_currency = client_options.get("vsCurrency", "usd")
    if isinstance(vs_currency, str) and vs_currency.strip():
        return vs_currency.strip().lower()
    return "usd"


async def fetch_market_caps_by_coingecko_id(
    coingecko_client,
    coingecko_ids: list[str],
    *,
    on_rate_limit_before_retry: typing.Callable[[], typing.Awaitable[None]] | None = None,
) -> dict[str, float]:
    unique_ids = sorted({coin_id.strip() for coin_id in coingecko_ids if coin_id and coin_id.strip()})
    if not unique_ids:
        return {}

    vs_currency = _coingecko_vs_currency(coingecko_client)
    response = await website_finder._call_coingecko_with_rate_limit_retry(
        lambda: coingecko_client.publicGetCoinsMarkets({
            "vs_currency": vs_currency,
            "ids": ",".join(unique_ids),
            "order": "market_cap_desc",
            "per_page": len(unique_ids),
            "page": 1,
        }),
        on_rate_limit_before_retry=on_rate_limit_before_retry,
    )
    if not isinstance(response, list):
        return {}

    market_caps_by_id: dict[str, float] = {}
    for coin_entry in response:
        if not isinstance(coin_entry, dict):
            continue
        coin_id = coin_entry.get("id")
        market_cap = coin_entry.get("market_cap")
        if not isinstance(coin_id, str) or not coin_id.strip():
            continue
        if market_cap is None:
            continue
        market_cap_value = float(market_cap)
        if market_cap_value <= 0:
            continue
        market_caps_by_id[coin_id] = market_cap_value
    return market_caps_by_id


def market_cap_by_symbol_from_listings(
    listings: list,
    market_caps_by_coingecko_id: dict[str, float],
) -> dict[str, typing.Optional[float]]:
    market_cap_by_symbol: dict[str, typing.Optional[float]] = {}
    for listing in listings:
        coingecko_id = getattr(listing, "coingecko_id", None)
        if not coingecko_id:
            market_cap_by_symbol[listing.symbol] = None
            continue
        market_cap_by_symbol[listing.symbol] = market_caps_by_coingecko_id.get(coingecko_id)
    return market_cap_by_symbol


async def fetch_market_cap_by_symbol_for_listings(
    config: app_config.AppConfig,
    listings: list[models.ListingRecord],
) -> dict[str, typing.Optional[float]]:
    coingecko_ids = [
        listing.coingecko_id
        for listing in listings
        if listing.coingecko_id
    ]
    if not coingecko_ids:
        return {}

    coingecko_client = ccxt_client.create_exchange(
        "coingecko",
        ccxt_options=config.ccxt_options,
        options=config.coingecko_options,
    )
    try:
        market_caps_by_coingecko_id = await fetch_market_caps_by_coingecko_id(
            coingecko_client,
            coingecko_ids,
        )
    finally:
        await coingecko_client.close()
    return market_cap_by_symbol_from_listings(listings, market_caps_by_coingecko_id)
