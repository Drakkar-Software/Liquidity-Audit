import collections
import logging
import typing

import ccxt

import liquidity_audit.application.shared.fetch_pair_metrics as fetch_pair_metrics
import liquidity_audit.application.shared.time_utils as time_utils
import liquidity_audit.config as app_config
import liquidity_audit.domain.analysis.pair_analysis as pair_analysis
import liquidity_audit.domain.models as models
import liquidity_audit.infrastructure.ccxt_client as ccxt_client

_LOGGER = logging.getLogger(__name__)


def parse_pair_spec(spec: str) -> tuple[str, str, str, str]:
    if spec.count(":") != 1:
        raise ValueError(
            f"invalid pair spec {spec!r}: expected BASE/QUOTE:exchange",
        )
    symbol_part, exchange = spec.split(":", 1)
    if "/" not in symbol_part:
        raise ValueError(
            f"invalid pair spec {spec!r}: symbol must be BASE/QUOTE",
        )
    base, quote = symbol_part.split("/", 1)
    if not base or not quote:
        raise ValueError(
            f"invalid pair spec {spec!r}: base and quote must be non-empty",
        )
    if not exchange:
        raise ValueError(
            f"invalid pair spec {spec!r}: exchange must be non-empty",
        )
    symbol = f"{base}/{quote}"
    return exchange, symbol, base, quote


def listing_from_pair_spec(
    exchange: str,
    symbol: str,
    base: str,
    quote: str,
) -> models.ListingRecord:
    return models.ListingRecord(
        exchange=exchange,
        symbol=symbol,
        base=base,
        quote=quote,
        full_name=base,
    )


async def run(
    config: app_config.AppConfig,
    pair_specs: list[str],
) -> list[dict[str, typing.Any]]:
    parsed: list[tuple[str, str, str, str, str]] = []
    for spec in pair_specs:
        exchange, symbol, base, quote = parse_pair_spec(spec)
        if exchange not in config.exchanges:
            raise ValueError(
                f"exchange {exchange!r} from {spec!r} is not in config.exchanges: "
                f"{config.exchanges!r}",
            )
        parsed.append((spec, exchange, symbol, base, quote))

    by_exchange: dict[str, list[tuple[int, str, str, str, str]]] = collections.defaultdict(list)
    for index, (original, exchange, symbol, base, quote) in enumerate(parsed):
        by_exchange[exchange].append((index, original, symbol, base, quote))

    output_by_index: dict[int, dict[str, typing.Any]] = {}
    peer_selection_settings = pair_analysis.peer_selection_settings_from_analysis_config(
        config.analysis,
    )

    for exchange_name, exchange_pairs in by_exchange.items():
        raw_metrics_by_symbol: dict[str, pair_analysis.ExtendedRawMetrics] = {}
        delisting_risk_by_symbol: dict[str, list[str]] = {}
        band_depth_by_symbol: dict[str, typing.Optional[float]] = {}
        listing_by_symbol: dict[str, models.ListingRecord] = {}

        async with ccxt_client.exchange_client(
            exchange_name,
            ccxt_options=config.ccxt_options,
        ) as exchange_client:
            for index, original, symbol, base, quote in exchange_pairs:
                listing = listing_from_pair_spec(exchange_name, symbol, base, quote)
                listing_by_symbol[symbol] = listing
                try:
                    fetched_at = time_utils.utc_now_iso()
                    raw_metrics, delisting_risk_labels, band_depth_quote = (
                        await fetch_pair_metrics.fetch_pair_raw_metrics(
                            exchange_client,
                            listing,
                            config,
                            fetched_at,
                        )
                    )
                    raw_metrics_by_symbol[symbol] = raw_metrics
                    delisting_risk_by_symbol[symbol] = delisting_risk_labels
                    band_depth_by_symbol[symbol] = band_depth_quote
                except ccxt.BadSymbol as error:
                    _LOGGER.warning(
                        "BadSymbol for %s %s: %s",
                        exchange_name,
                        symbol,
                        error,
                    )
                    output_by_index[index] = {
                        "pair": original,
                        "error": str(error),
                    }
                except Exception as error:
                    _LOGGER.exception(
                        "Failed to fetch %s %s",
                        exchange_name,
                        symbol,
                    )
                    output_by_index[index] = {
                        "pair": original,
                        "error": str(error),
                    }

        universe = list(raw_metrics_by_symbol.values())
        exchange_averages = pair_analysis.compute_exchange_averages(
            universe,
            config.analysis.rankings_min_volume_quote,
        )

        for index, original, symbol, base, quote in exchange_pairs:
            if index in output_by_index:
                continue
            raw_metrics = raw_metrics_by_symbol.get(symbol)
            if raw_metrics is None:
                continue
            listing = listing_by_symbol[symbol]
            delisting_risk_labels = delisting_risk_by_symbol.get(symbol, [])
            delisting_risk_cards = fetch_pair_metrics.build_delisting_risk_cards_for_listing(
                listing,
                raw_metrics,
                delisting_risk_labels,
                config,
                band_depth_by_symbol.get(symbol),
            )
            output_by_index[index] = pair_analysis.build_pair_analysis(
                raw_metrics,
                universe,
                exchange_averages,
                config.health_labels,
                delisting_risk_cards=delisting_risk_cards,
                peer_selection_settings=peer_selection_settings,
                market_cap_by_symbol=None,
            )

    return [output_by_index[index] for index in range(len(parsed))]
