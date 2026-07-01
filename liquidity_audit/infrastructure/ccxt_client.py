import contextlib
import typing

import ccxt.async_support as async_ccxt


def ccxt_exchange_class_factory(exchange_name: str) -> type:
    if not exchange_name.startswith("ob_"):
        ob_subclass = getattr(async_ccxt, f"ob_{exchange_name}", None)
        if ob_subclass is not None:
            return ob_subclass
    exchange_class = getattr(async_ccxt, exchange_name, None)
    if exchange_class is None:
        raise ValueError(f"unknown exchange: {exchange_name}")
    return exchange_class


def create_exchange(
    exchange_name: str,
    ccxt_options: typing.Optional[dict] = None,
    options: typing.Optional[dict] = None,
) -> async_ccxt.Exchange:
    exchange_class = ccxt_exchange_class_factory(exchange_name)
    client_config: dict = {
        "enableRateLimit": True,
        "options": {
            "defaultType": "spot",
            **(ccxt_options or {}),
            **(options or {}),
        },
    }
    return exchange_class(client_config)


@contextlib.asynccontextmanager
async def exchange_client(
    exchange_name: str,
    ccxt_options: typing.Optional[dict] = None,
    options: typing.Optional[dict] = None,
    reload_markets: bool = True,
):
    client = create_exchange(exchange_name, ccxt_options=ccxt_options, options=options)
    try:
        if reload_markets:
            await client.load_markets(reload=True)
        yield client
    finally:
        await client.close()
