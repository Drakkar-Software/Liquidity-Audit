import liquidity_audit.config as app_config
import liquidity_audit.domain.analysis.delisting_risk as delisting_risk


def _thresholds(
    depth_band_pct: float = 0.02,
    min_depth_quote_usdt: float = 5000.0,
    min_volume_quote_usdt: float = 10000.0,
) -> app_config.DelistingRiskExchangeThresholds:
    return app_config.DelistingRiskExchangeThresholds(
        depth_band_pct=depth_band_pct,
        min_depth_quote_usdt=min_depth_quote_usdt,
        min_volume_quote_usdt=min_volume_quote_usdt,
    )


def _order_book(mid_price: float = 100.0) -> dict:
    return {
        "bids": [[mid_price * 0.99, 100.0], [mid_price * 0.985, 100.0]],
        "asks": [[mid_price * 1.01, 100.0], [mid_price * 1.015, 100.0]],
    }


def _ticker(
    mid_price: float = 100.0,
    volume_quote: float | None = 15000.0,
) -> dict:
    ticker = {
        "bid": mid_price * 0.99,
        "ask": mid_price * 1.01,
    }
    if volume_quote is not None:
        ticker["quoteVolume"] = volume_quote
    return ticker


class TestEvaluateDelistingRiskVolume:
    def test_flags_low_volume_when_below_threshold(self):
        labels = delisting_risk.evaluate_delisting_risk(
            volume_quote=5000.0,
            order_book=_order_book(),
            ticker=_ticker(volume_quote=5000.0),
            thresholds=_thresholds(min_volume_quote_usdt=10000.0),
        )
        assert labels == [delisting_risk.LABEL_LOW_VOLUME]

    def test_flags_low_volume_when_volume_missing(self):
        labels = delisting_risk.evaluate_delisting_risk(
            volume_quote=None,
            order_book=_order_book(),
            ticker=_ticker(volume_quote=None),
            thresholds=_thresholds(),
        )
        assert labels == [delisting_risk.LABEL_LOW_VOLUME]


class TestEvaluateDelistingRiskDepth:
    def test_flags_low_depth_when_band_depth_below_threshold(self):
        shallow_order_book = {
            "bids": [[99.0, 1.0]],
            "asks": [[101.0, 1.0]],
        }
        labels = delisting_risk.evaluate_delisting_risk(
            volume_quote=20000.0,
            order_book=shallow_order_book,
            ticker=_ticker(volume_quote=20000.0),
            thresholds=_thresholds(min_depth_quote_usdt=5000.0),
        )
        assert labels == [delisting_risk.LABEL_LOW_DEPTH]


class TestEvaluateDelistingRiskCombined:
    def test_returns_both_labels_when_volume_and_depth_fail(self):
        shallow_order_book = {
            "bids": [[99.0, 1.0]],
            "asks": [[101.0, 1.0]],
        }
        labels = delisting_risk.evaluate_delisting_risk(
            volume_quote=1000.0,
            order_book=shallow_order_book,
            ticker=_ticker(volume_quote=1000.0),
            thresholds=_thresholds(),
        )
        assert labels == [delisting_risk.LABEL_LOW_DEPTH, delisting_risk.LABEL_LOW_VOLUME]

    def test_returns_empty_list_when_above_thresholds(self):
        labels = delisting_risk.evaluate_delisting_risk(
            volume_quote=20000.0,
            order_book=_order_book(),
            ticker=_ticker(volume_quote=20000.0),
            thresholds=_thresholds(),
        )
        assert labels == []

    def test_uses_custom_depth_band_pct(self):
        mid_price = 100.0
        order_book = {
            "bids": [[mid_price * 0.99, 50.0], [mid_price * 0.985, 100.0]],
            "asks": [[mid_price * 1.01, 50.0], [mid_price * 1.015, 100.0]],
        }
        labels_at_one_pct = delisting_risk.evaluate_delisting_risk(
            volume_quote=20000.0,
            order_book=order_book,
            ticker=_ticker(volume_quote=20000.0),
            thresholds=_thresholds(depth_band_pct=0.01, min_depth_quote_usdt=15000.0),
        )
        labels_at_two_pct = delisting_risk.evaluate_delisting_risk(
            volume_quote=20000.0,
            order_book=order_book,
            ticker=_ticker(volume_quote=20000.0),
            thresholds=_thresholds(depth_band_pct=0.02, min_depth_quote_usdt=15000.0),
        )
        assert labels_at_one_pct == [delisting_risk.LABEL_LOW_DEPTH]
        assert labels_at_two_pct == []


class TestEvaluateDelistingRiskFromStored:
    def test_matches_live_evaluation_for_stored_metrics(self):
        labels = delisting_risk.evaluate_delisting_risk_from_stored(
            volume_quote=5000.0,
            band_depth_quote=140.0,
            thresholds=_thresholds(),
        )
        assert labels == [delisting_risk.LABEL_LOW_DEPTH, delisting_risk.LABEL_LOW_VOLUME]


class TestBuildDelistingRiskCards:
    def test_builds_cards_for_each_label(self):
        cards = delisting_risk.build_delisting_risk_cards(
            [delisting_risk.LABEL_LOW_DEPTH, delisting_risk.LABEL_LOW_VOLUME],
            volume_quote=8200.0,
            band_depth_quote=140.0,
            thresholds=_thresholds(),
        )
        assert len(cards) == 2
        assert cards[0]["title"] == "Low depth"
        assert cards[1]["title"] == "Low volume"
        assert cards[0]["severity"] == "Critical"
        assert "$140" in cards[0]["evidence"]
        assert "$8.2k" in cards[1]["evidence"]

    def test_returns_empty_list_when_no_labels(self):
        assert delisting_risk.build_delisting_risk_cards([], 20000.0, 9000.0, _thresholds()) == []

