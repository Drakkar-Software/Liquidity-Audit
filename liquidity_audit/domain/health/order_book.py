import typing


def sorted_bids(bids: list) -> list:
    return sorted(bids, key=lambda level: level[0], reverse=True)


def sorted_asks(asks: list) -> list:
    return sorted(asks, key=lambda level: level[0])


def parse_volume_quote(ticker: dict) -> typing.Optional[float]:
    volume_quote_raw = ticker.get("quoteVolume")
    if volume_quote_raw is None:
        return None
    volume_quote = float(volume_quote_raw)
    if volume_quote <= 0:
        return None
    return volume_quote


def compute_mid_price(
    sorted_bids_list: list,
    sorted_asks_list: list,
    ticker: dict,
) -> typing.Optional[float]:
    if sorted_bids_list and sorted_asks_list:
        return (float(sorted_asks_list[0][0]) + float(sorted_bids_list[0][0])) / 2
    for ticker_key in ("close", "last"):
        ticker_price = ticker.get(ticker_key)
        if ticker_price is not None:
            return float(ticker_price)
    return None


def compute_bid_ask_spread_ratio(
    sorted_bids_list: list,
    sorted_asks_list: list,
    mid_price: float,
) -> typing.Optional[float]:
    if not sorted_bids_list or not sorted_asks_list:
        return None
    spread = float(sorted_asks_list[0][0]) - float(sorted_bids_list[0][0])
    return spread / mid_price


def compute_total_depth_quote(sorted_levels: list) -> float:
    return sum(float(level[0]) * float(level[1]) for level in sorted_levels)


def compute_band_depth_quote(
    sorted_levels: list,
    mid_price: float,
    depth_band_pct: float,
    are_bids: bool,
) -> float:
    if are_bids:
        price_threshold = mid_price * (1 - depth_band_pct)
        return sum(
            float(level[0]) * float(level[1])
            for level in sorted_levels
            if float(level[0]) >= price_threshold
        )
    price_threshold = mid_price * (1 + depth_band_pct)
    return sum(
        float(level[0]) * float(level[1])
        for level in sorted_levels
        if float(level[0]) <= price_threshold
    )
