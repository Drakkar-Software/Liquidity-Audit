import logging
import typing

import liquidity_audit.infrastructure.ccxt_client as ccxt_client
import liquidity_audit.domain.models as models

_LOGGER = logging.getLogger(__name__)

SUPPORTED_QUOTE_CURRENCIES = frozenset({"USDT", "USDC"})


class ListingDiscoveryError(Exception):
    pass


def _is_supported_quote_pair(market: dict) -> bool:
    quote = market.get("quote")
    return isinstance(quote, str) and quote in SUPPORTED_QUOTE_CURRENCIES


def _is_spot_active_market(market: dict) -> bool:
    if market.get("spot") is not True:
        return False
    if market.get("active") is False:
        return False
    return True


def _extract_mexc_full_name(market: dict, symbol: str) -> str:
    market_info = market.get("info")
    if not isinstance(market_info, dict):
        raise ListingDiscoveryError(f"MEXC market {symbol!r} has no info dict")
    full_name = market_info.get("fullName")
    if not isinstance(full_name, str) or not full_name.strip():
        raise ListingDiscoveryError(f"MEXC market {symbol!r} is missing info.fullName")
    return full_name.strip()


def _try_extract_bitmart_full_name(currencies: dict, base: str) -> typing.Optional[str]:
    currency = currencies.get(base)
    if not isinstance(currency, dict):
        return None
    full_name = currency.get("name")
    if not isinstance(full_name, str) or not full_name.strip():
        return None
    return full_name.strip()


def _bitmart_listing_from_market(
    symbol: str,
    market: dict,
    currencies: dict,
) -> typing.Optional[models.ListingRecord]:
    base = market.get("base")
    quote = market.get("quote")
    if not isinstance(base, str) or not isinstance(quote, str):
        return None
    full_name = _try_extract_bitmart_full_name(currencies, base)
    if full_name is None:
        return None
    return models.ListingRecord(
        exchange="bitmart",
        symbol=symbol,
        base=base,
        quote=quote,
        full_name=full_name,
    )


def _market_to_listing(
    exchange_name: str,
    symbol: str,
    market: dict,
) -> models.ListingRecord:
    base = market.get("base")
    quote = market.get("quote")
    if not isinstance(base, str) or not isinstance(quote, str):
        raise ListingDiscoveryError(f"{exchange_name} market {symbol!r} has invalid base/quote")

    if exchange_name == "mexc":
        full_name = _extract_mexc_full_name(market, symbol)
    else:
        raise ListingDiscoveryError(f"unsupported exchange for listing discovery: {exchange_name}")

    return models.ListingRecord(
        exchange=exchange_name,
        symbol=symbol,
        base=base,
        quote=quote,
        full_name=full_name,
    )


async def fetch_current_listings(
    client,
    exchange_name: str,
    currencies: typing.Optional[dict] = None,
) -> list[models.ListingRecord]:
    listings: list[models.ListingRecord] = []
    spot_active_market_count = 0
    missing_bitmart_currency_count = 0

    for symbol, market in client.markets.items():
        if not _is_spot_active_market(market):
            continue
        if not _is_supported_quote_pair(market):
            continue
        spot_active_market_count += 1

        if exchange_name == "bitmart":
            if currencies is None:
                raise ListingDiscoveryError("BitMart currencies must be loaded before listing extraction")
            listing = _bitmart_listing_from_market(symbol, market, currencies)
            if listing is None:
                missing_bitmart_currency_count += 1
                continue
            listings.append(listing)
            continue

        listings.append(_market_to_listing(exchange_name, symbol, market))

    if exchange_name == "bitmart":
        _LOGGER.info(
            "BitMart currency name missing for %s active spot market(s) out of %s",
            missing_bitmart_currency_count,
            spot_active_market_count,
        )

    return listings


def filter_new_listings(
    listings: list[models.ListingRecord],
    known_keys: set[tuple[str, str]],
) -> list[models.ListingRecord]:
    new_listings = [
        listing
        for listing in listings
        if listing.key() not in known_keys
    ]
    _LOGGER.info(
        "Found %s new listing(s) out of %s current listing(s)",
        len(new_listings),
        len(listings),
    )
    for listing in new_listings:
        _LOGGER.info(
            "New listing: %s %s (%s)",
            listing.exchange,
            listing.symbol,
            listing.full_name,
        )
    return new_listings


async def fetch_exchange_listings(
    client,
    exchange_name: str,
) -> list[models.ListingRecord]:
    currencies = None
    if exchange_name == "bitmart":
        _LOGGER.info("Fetching BitMart currencies for full name resolution")
        currencies = await client.fetch_currencies()
        _LOGGER.info("Loaded %s BitMart currencies", len(currencies))
    listings = await fetch_current_listings(client, exchange_name, currencies=currencies)
    _LOGGER.info(
        "Fetched %s active spot listing(s) on %s",
        len(listings),
        exchange_name,
    )
    return listings


async def find_new_listings(
    exchange_name: str,
    known_keys: set[tuple[str, str]],
) -> list[models.ListingRecord]:
    async with ccxt_client.exchange_client(exchange_name) as client:
        current_listings = await fetch_exchange_listings(client, exchange_name)
        return filter_new_listings(current_listings, known_keys)
