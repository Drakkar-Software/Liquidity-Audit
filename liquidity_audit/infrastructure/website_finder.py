import asyncio
import dataclasses
import logging
import re
import typing

import ccxt

import liquidity_audit.domain.website.website_resolution as website_resolution

_LOGGER = logging.getLogger(__name__)
COINGECKO_RATE_LIMIT_RETRY_DELAY_SECONDS = 60


class WebsiteFinderError(Exception):
    pass


@dataclasses.dataclass
class _CoingeckoPickResult:
    market: dict | None
    ambiguous_candidates: list[tuple[str, str]] = dataclasses.field(default_factory=list)
    name_mismatch_candidates: list[tuple[str, str]] = dataclasses.field(default_factory=list)


def _normalize_name(name: str) -> str:
    lowered = name.lower().strip()
    return re.sub(r"[^a-z0-9]+", "", lowered)


def _name_match_score(exchange_full_name: str, coingecko_name: str) -> int:
    normalized_exchange = _normalize_name(exchange_full_name)
    normalized_coingecko = _normalize_name(coingecko_name)
    if not normalized_exchange or not normalized_coingecko:
        return 0
    if normalized_exchange == normalized_coingecko:
        return 100
    if normalized_exchange in normalized_coingecko or normalized_coingecko in normalized_exchange:
        return 50
    return 0


def _coingecko_candidate_id_and_name(market: dict) -> tuple[str, str] | None:
    coin_id = market.get("id")
    if not isinstance(coin_id, str) or not coin_id.strip():
        return None
    market_info = market.get("info", {})
    coingecko_name = market_info.get("name") if isinstance(market_info, dict) else None
    if not isinstance(coingecko_name, str):
        return None
    return coin_id, coingecko_name


def _format_candidate_list(candidates: list[tuple[str, str]]) -> str:
    return ", ".join(f"{name} ({coin_id})" for coin_id, name in candidates)


def _collect_coingecko_candidates(markets: list[dict]) -> list[tuple[str, str]]:
    collected_candidates: list[tuple[str, str]] = []
    for market in markets:
        candidate = _coingecko_candidate_id_and_name(market)
        if candidate is not None:
            collected_candidates.append(candidate)
    return collected_candidates


async def _call_coingecko_with_rate_limit_retry(
    operation: typing.Callable[[], typing.Awaitable[typing.Any]],
    on_rate_limit_before_retry: typing.Callable[[], typing.Awaitable[None]] | None = None,
) -> typing.Any:
    while True:
        try:
            return await operation()
        except ccxt.RateLimitExceeded as rate_limit_error:
            _LOGGER.warning(
                "CoinGecko rate limit exceeded, sleeping %s seconds before retry: %s",
                COINGECKO_RATE_LIMIT_RETRY_DELAY_SECONDS,
                rate_limit_error,
            )
            if on_rate_limit_before_retry is not None:
                await on_rate_limit_before_retry()
            await asyncio.sleep(COINGECKO_RATE_LIMIT_RETRY_DELAY_SECONDS)


def _first_non_empty_url(urls: typing.Any) -> typing.Optional[str]:
    if not isinstance(urls, list):
        return None
    for url in urls:
        if isinstance(url, str) and url.strip():
            return url.strip()
    return None


def _symbol_candidates_from_markets_by_id(markets_by_id: dict) -> tuple[dict[str, list[dict]], int]:
    symbol_candidates: dict[str, list[dict]] = {}
    indexed_market_count = 0
    for markets_for_id in markets_by_id.values():
        if isinstance(markets_for_id, list):
            market_list = markets_for_id
        else:
            market_list = [markets_for_id]
        for market in market_list:
            base = market.get("base")
            if not isinstance(base, str):
                continue
            symbol_key = base.upper()
            symbol_candidates.setdefault(symbol_key, []).append(market)
            indexed_market_count += 1
    return symbol_candidates, indexed_market_count


def _coingecko_vs_currency(coingecko_client) -> str:
    client_options = getattr(coingecko_client, "options", {}) or {}
    vs_currency = client_options.get("vsCurrency", "usd")
    if isinstance(vs_currency, str) and vs_currency.strip():
        return vs_currency.strip().lower()
    return "usd"


async def _fetch_market_cap_ranks(
    coingecko_client,
    coin_ids: list[str],
    on_rate_limit_before_retry: typing.Callable[[], typing.Awaitable[None]] | None = None,
) -> dict[str, int]:
    if not coin_ids:
        return {}
    vs_currency = _coingecko_vs_currency(coingecko_client)
    response = await _call_coingecko_with_rate_limit_retry(
        lambda: coingecko_client.publicGetCoinsMarkets({
            "vs_currency": vs_currency,
            "ids": ",".join(coin_ids),
            "order": "market_cap_desc",
            "per_page": len(coin_ids),
            "page": 1,
        }),
        on_rate_limit_before_retry=on_rate_limit_before_retry,
    )
    if not isinstance(response, list):
        return {}
    market_cap_ranks: dict[str, int] = {}
    for coin_entry in response:
        if not isinstance(coin_entry, dict):
            continue
        coin_id = coin_entry.get("id")
        market_cap_rank = coin_entry.get("market_cap_rank")
        if not isinstance(coin_id, str) or not coin_id.strip():
            continue
        if market_cap_rank is None:
            continue
        market_cap_ranks[coin_id] = int(market_cap_rank)
    return market_cap_ranks


def _pick_market_by_market_cap_rank(
    tied_markets: list[dict],
    market_cap_ranks: dict[str, int],
) -> dict | None:
    ranked_markets: list[tuple[int, dict]] = []
    for market in tied_markets:
        coin_id = market.get("id")
        if not isinstance(coin_id, str) or not coin_id.strip():
            continue
        market_cap_rank = market_cap_ranks.get(coin_id)
        if market_cap_rank is None:
            continue
        ranked_markets.append((market_cap_rank, market))
    if not ranked_markets:
        return None
    ranked_markets.sort(key=lambda ranked_market: ranked_market[0])
    best_market_cap_rank = ranked_markets[0][0]
    top_ranked_markets = [
        market
        for market_cap_rank, market in ranked_markets
        if market_cap_rank == best_market_cap_rank
    ]
    if len(top_ranked_markets) != 1:
        return None
    return top_ranked_markets[0]


class WebsiteFinder:
    def __init__(self) -> None:
        self._symbol_candidates: dict[str, list[dict]] = {}
        self._index_loaded = False

    async def load_coingecko_index(
        self,
        coingecko_client,
        on_rate_limit_before_retry: typing.Callable[[], typing.Awaitable[None]] | None = None,
    ) -> None:
        await _call_coingecko_with_rate_limit_retry(
            lambda: coingecko_client.load_markets(reload=True),
            on_rate_limit_before_retry=on_rate_limit_before_retry,
        )
        symbol_candidates, indexed_market_count = _symbol_candidates_from_markets_by_id(
            coingecko_client.markets_by_id,
        )
        self._symbol_candidates = symbol_candidates
        self._index_loaded = True
        _LOGGER.info(
            "CoinGecko index loaded: %s coin(s), %s unique symbol(s)",
            indexed_market_count,
            len(symbol_candidates),
        )

    async def _pick_coingecko_market(
        self,
        coingecko_client,
        full_name: str,
        base_symbol: str,
        on_rate_limit_before_retry: typing.Callable[[], typing.Awaitable[None]] | None = None,
    ) -> _CoingeckoPickResult:
        candidates = self._symbol_candidates.get(base_symbol.upper(), [])
        if not candidates:
            return _CoingeckoPickResult(market=None)

        scored_candidates: list[tuple[int, dict]] = []
        for market in candidates:
            market_info = market.get("info", {})
            coingecko_name = market_info.get("name") if isinstance(market_info, dict) else None
            if not isinstance(coingecko_name, str):
                continue
            score = _name_match_score(full_name, coingecko_name)
            if score > 0:
                scored_candidates.append((score, market))

        if not scored_candidates:
            name_mismatch_candidates = _collect_coingecko_candidates(candidates)
            return _CoingeckoPickResult(
                market=None,
                name_mismatch_candidates=name_mismatch_candidates,
            )

        scored_candidates.sort(key=lambda item: item[0], reverse=True)
        best_score = scored_candidates[0][0]
        best_candidates = [market for score, market in scored_candidates if score == best_score]
        if len(best_candidates) > 1:
            tied_coin_ids = [
                coin_id
                for market in best_candidates
                if (coin_id := market.get("id")) and isinstance(coin_id, str) and coin_id.strip()
            ]
            market_cap_ranks = await _fetch_market_cap_ranks(
                coingecko_client,
                tied_coin_ids,
                on_rate_limit_before_retry=on_rate_limit_before_retry,
            )
            market_cap_winner = _pick_market_by_market_cap_rank(best_candidates, market_cap_ranks)
            if market_cap_winner is not None:
                winner_id = market_cap_winner.get("id")
                winner_rank = market_cap_ranks.get(winner_id) if isinstance(winner_id, str) else None
                _LOGGER.info(
                    "CoinGecko name tie for %s (%s) resolved by market cap rank: id=%s rank=%s",
                    full_name,
                    base_symbol,
                    winner_id,
                    winner_rank,
                )
                return _CoingeckoPickResult(market=market_cap_winner)

            ambiguous_candidates: list[tuple[str, str]] = []
            for market in best_candidates:
                candidate = _coingecko_candidate_id_and_name(market)
                if candidate is not None:
                    ambiguous_candidates.append(candidate)
            return _CoingeckoPickResult(
                market=None,
                ambiguous_candidates=ambiguous_candidates,
            )
        return _CoingeckoPickResult(market=best_candidates[0])

    async def resolve_website(
        self,
        coingecko_client,
        full_name: str,
        base_symbol: str,
        on_rate_limit_before_retry: typing.Callable[[], typing.Awaitable[None]] | None = None,
    ) -> website_resolution.WebsiteResolutionResult:
        if not self._index_loaded:
            raise WebsiteFinderError("CoinGecko index not loaded; call load_coingecko_index first")

        pick_result = await self._pick_coingecko_market(
            coingecko_client,
            full_name,
            base_symbol,
            on_rate_limit_before_retry=on_rate_limit_before_retry,
        )
        if pick_result.ambiguous_candidates:
            ambiguous_payload = [
                {"id": coin_id, "name": name}
                for coin_id, name in pick_result.ambiguous_candidates
            ]
            _LOGGER.warning(
                "Ambiguous CoinGecko name match for %s (%s): tied candidates: %s",
                full_name,
                base_symbol,
                _format_candidate_list(pick_result.ambiguous_candidates),
            )
            return website_resolution.WebsiteResolutionResult(
                website=None,
                coingecko_id=None,
                failure_reason=website_resolution.COINGECKO_AMBIGUOUS_NAME_MATCH,
                ambiguous_coingecko_candidates=ambiguous_payload,
            )

        if pick_result.name_mismatch_candidates:
            symbol_payload = [
                {"id": coin_id, "name": name}
                for coin_id, name in pick_result.name_mismatch_candidates
            ]
            _LOGGER.warning(
                "CoinGecko name mismatch for %s (%s): indexed candidate(s): %s",
                full_name,
                base_symbol,
                _format_candidate_list(pick_result.name_mismatch_candidates),
            )
            return website_resolution.WebsiteResolutionResult(
                website=None,
                coingecko_id=None,
                failure_reason=website_resolution.COINGECKO_NAME_MISMATCH,
                symbol_coingecko_candidates=symbol_payload,
            )

        matched_market = pick_result.market
        if matched_market is None:
            _LOGGER.warning(
                "No CoinGecko match for %s (%s)",
                full_name,
                base_symbol,
            )
            return website_resolution.WebsiteResolutionResult(
                website=None,
                coingecko_id=None,
                failure_reason=website_resolution.COINGECKO_NO_MATCH,
            )

        coin_id = matched_market.get("id")
        if not isinstance(coin_id, str) or not coin_id.strip():
            _LOGGER.error(
                "Matched CoinGecko market for %s (%s) has no id",
                full_name,
                base_symbol,
            )
            return website_resolution.WebsiteResolutionResult(
                website=None,
                coingecko_id=None,
                failure_reason=website_resolution.COINGECKO_NO_MATCH,
            )

        _LOGGER.info(
            "Fetching CoinGecko coin detail for %s (id=%s)",
            full_name,
            coin_id,
        )
        coin_detail = await _call_coingecko_with_rate_limit_retry(
            lambda: coingecko_client.publicGetCoinsId({
                "id": coin_id,
                "localization": False,
                "tickers": False,
                "market_data": False,
                "community_data": False,
                "developer_data": False,
            }),
            on_rate_limit_before_retry=on_rate_limit_before_retry,
        )
        links = coin_detail.get("links")
        if not isinstance(links, dict):
            _LOGGER.warning(
                "CoinGecko coin %s has no links section",
                coin_id,
            )
            return website_resolution.WebsiteResolutionResult(
                website=None,
                coingecko_id=coin_id,
                failure_reason=website_resolution.COINGECKO_NO_MATCH,
            )

        homepage = _first_non_empty_url(links.get("homepage"))
        if homepage is None:
            _LOGGER.warning(
                "CoinGecko coin %s has no homepage URL",
                coin_id,
            )
            return website_resolution.WebsiteResolutionResult(
                website=None,
                coingecko_id=coin_id,
                failure_reason=website_resolution.COINGECKO_NO_MATCH,
            )
        return website_resolution.WebsiteResolutionResult(
            website=homepage,
            coingecko_id=coin_id,
        )
