import pytest

import liquidity_audit.domain.health.order_book as health_order_book


class TestParseVolumeQuote:
    def test_uses_base_volume_times_close_when_quote_volume_missing(self):
        ticker = {
            "baseVolume": 1000.0,
            "close": 28.5,
        }
        assert health_order_book.parse_volume_quote(ticker) == pytest.approx(28_500.0)

    def test_prefers_quote_volume_when_present(self):
        ticker = {
            "quoteVolume": 50_000.0,
            "baseVolume": 1000.0,
            "close": 28.5,
        }
        assert health_order_book.parse_volume_quote(ticker) == pytest.approx(50_000.0)

    def test_uses_last_when_close_absent(self):
        ticker = {
            "baseVolume": 200.0,
            "last": 10.0,
        }
        assert health_order_book.parse_volume_quote(ticker) == pytest.approx(2000.0)

    def test_uses_last_when_close_is_zero(self):
        ticker = {
            "baseVolume": 200.0,
            "close": 0.0,
            "last": 10.0,
        }
        assert health_order_book.parse_volume_quote(ticker) == pytest.approx(2000.0)

    def test_returns_none_when_volume_cannot_be_derived(self):
        assert health_order_book.parse_volume_quote({}) is None
        assert health_order_book.parse_volume_quote({"baseVolume": 100.0}) is None
        assert health_order_book.parse_volume_quote({"quoteVolume": 0.0}) is None
