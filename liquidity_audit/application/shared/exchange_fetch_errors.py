import ccxt


def is_skippable_pair_fetch_error(error: BaseException) -> bool:
    if isinstance(error, ccxt.NullResponse):
        return True
    if isinstance(error, ccxt.BadSymbol):
        return False
    error_text = str(error).lower()
    if isinstance(error, ccxt.BadRequest):
        return "symbol is not found" in error_text or "100204" in str(error)
    if isinstance(error, ccxt.ExchangeError):
        return "market" in error_text and "not found" in error_text
    return False
