import ccxt

import liquidity_audit.application.shared.exchange_fetch_errors as exchange_fetch_errors


class TestIsSkippablePairFetchError:
    def test_null_response_is_skippable(self):
        error = ccxt.NullResponse(
            "ob_weex fetchTickers() could not find a ticker for SHOGGOTH/USDT",
        )
        assert exchange_fetch_errors.is_skippable_pair_fetch_error(error) is True

    def test_bingx_bad_request_symbol_not_found_is_skippable(self):
        error = ccxt.BadRequest(
            "ob_bingx {\"code\":100204,\"msg\":\"symbol is not found.\",\"timestamp\":1785877647527}",
        )
        assert exchange_fetch_errors.is_skippable_pair_fetch_error(error) is True

    def test_coinex_exchange_error_market_not_found_is_skippable(self):
        error = ccxt.ExchangeError("ob_coinex Invalid Parameter: market USDRUSDT not found")
        assert exchange_fetch_errors.is_skippable_pair_fetch_error(error) is True

    def test_bad_symbol_is_not_skippable(self):
        error = ccxt.BadSymbol("PITCH/USDT does not exist")
        assert exchange_fetch_errors.is_skippable_pair_fetch_error(error) is False

    def test_generic_bad_request_is_not_skippable(self):
        error = ccxt.BadRequest("ob_bingx invalid limit parameter")
        assert exchange_fetch_errors.is_skippable_pair_fetch_error(error) is False

    def test_generic_exchange_error_is_not_skippable(self):
        error = ccxt.ExchangeError("ob_coinex internal server error")
        assert exchange_fetch_errors.is_skippable_pair_fetch_error(error) is False
