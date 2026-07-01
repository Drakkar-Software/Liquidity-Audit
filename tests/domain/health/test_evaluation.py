import pytest

import tests.fixtures.health_fixtures as health_fixtures
import tests.fixtures.health_label_fixtures as health_label_fixtures
import liquidity_audit.config as app_config
import liquidity_audit.domain.models as models
import liquidity_audit.domain.health.evaluation as health_evaluation
import liquidity_audit.domain.health.order_book as health_order_book
import liquidity_audit.infrastructure.listing_health_fetcher as listing_health_fetcher


def _health_labels() -> app_config.HealthLabelsConfig:
    return health_label_fixtures.default_health_labels()


def _evaluate(order_book: dict, ticker: dict) -> models.HealthResult:
    return health_evaluation.evaluate_health(
        order_book,
        ticker,
        health_fixtures.health_rules(),
        health_fixtures.unhealthy_values(),
        _health_labels(),
        health_fixtures.min_liquidity_score(),
    )


def _healthy_order_book() -> dict:
    bids = [[100.0 - index * 0.01, 20.0] for index in range(10)]
    asks = [[100.05 + index * 0.01, 20.0] for index in range(16)]
    return {"bids": bids, "asks": asks}


class TestComputeMidPrice:
    def test_uses_best_bid_and_ask_when_both_sides_present(self):
        sorted_bids = [[100.0, 1.0]]
        sorted_asks = [[101.0, 1.0]]
        ticker = {}
        assert health_order_book.compute_mid_price(sorted_bids, sorted_asks, ticker) == 100.5

    def test_falls_back_to_ticker_close(self):
        assert health_order_book.compute_mid_price([], [], {"close": 42.0}) == 42.0

    def test_falls_back_to_ticker_last(self):
        assert health_order_book.compute_mid_price([], [], {"last": 43.0}) == 43.0

    def test_returns_none_when_mid_cannot_be_resolved(self):
        assert health_order_book.compute_mid_price([], [], {}) is None


class TestComputeBidAskSpreadRatio:
    def test_returns_ratio_when_both_sides_present(self):
        sorted_bids = [[100.0, 1.0]]
        sorted_asks = [[100.1, 1.0]]
        assert health_order_book.compute_bid_ask_spread_ratio(
            sorted_bids, sorted_asks, mid_price=100.05,
        ) == pytest.approx(0.1 / 100.05)

    def test_returns_none_when_one_side_missing(self):
        assert health_order_book.compute_bid_ask_spread_ratio(
            [[100.0, 1.0]], [], mid_price=100.0,
        ) is None


class TestComputeTotalDepthQuote:
    def test_sums_notional_across_all_levels(self):
        sorted_levels = [[100.0, 2.0], [99.0, 1.0], [98.0, 3.0]]
        assert health_order_book.compute_total_depth_quote(sorted_levels) == 593.0


class TestComputeBandDepthQuote:
    def test_sums_bid_notional_within_tight_band(self):
        mid_price = 100.0
        sorted_bids = [[100.0, 2.0], [98.0, 1.0]]
        depth = health_order_book.compute_band_depth_quote(
            sorted_bids, mid_price, depth_band_pct=0.01, are_bids=True,
        )
        assert depth == 200.0

    def test_sums_ask_notional_within_tight_band(self):
        mid_price = 100.0
        sorted_asks = [[100.0, 2.0], [102.0, 1.0]]
        depth = health_order_book.compute_band_depth_quote(
            sorted_asks, mid_price, depth_band_pct=0.01, are_bids=False,
        )
        assert depth == 200.0

    def test_wider_band_includes_more_notional_than_tight_band(self):
        mid_price = 100.0
        sorted_bids = [[100.0, 1.0], [95.0, 2.0]]
        tight_depth = health_order_book.compute_band_depth_quote(
            sorted_bids, mid_price, depth_band_pct=0.01, are_bids=True,
        )
        larger_depth = health_order_book.compute_band_depth_quote(
            sorted_bids, mid_price, depth_band_pct=0.1, are_bids=True,
        )
        assert larger_depth >= tight_depth
        assert larger_depth == 100.0 + 190.0


class TestDepthScoreFromRatio:
    def test_high_depth_band_scores_one(self):
        assert health_evaluation.depth_score_from_ratio(0.05) == 1.0

    def test_depth_above_one_scores_one(self):
        assert health_evaluation.depth_score_from_ratio(5.0) == 1.0

    def test_moderate_depth_band_interpolates(self):
        score = health_evaluation.depth_score_from_ratio(0.005)
        assert 0.5 < score < 1.0

    def test_low_depth_band_interpolates(self):
        score = health_evaluation.depth_score_from_ratio(0.001)
        assert 0.0 < score < 0.5


class TestSpreadScoreFromRatio:
    def test_tight_spread_scores_one(self):
        assert health_evaluation.spread_score_from_ratio(0.0005) == 1.0

    def test_moderate_spread_interpolates(self):
        score = health_evaluation.spread_score_from_ratio(0.003)
        assert 0.5 < score < 1.0

    def test_wide_spread_scores_zero(self):
        assert health_evaluation.spread_score_from_ratio(0.01) == 0.0


class TestComputeDepthPillarScore:
    def test_asymmetric_book_scores_by_weaker_side(self):
        volume_quote = 200_000.0
        symmetric_score = health_evaluation.compute_depth_pillar_score(
            100_000.0,
            100_000.0,
            volume_quote,
        )
        asymmetric_score = health_evaluation.compute_depth_pillar_score(
            180_000.0,
            800.0,
            volume_quote,
        )
        assert symmetric_score > asymmetric_score


class TestComputeLiquidityScoreFromMetrics:
    def test_strong_book_scores_at_least_point_nine_five(self):
        score = health_evaluation._compute_liquidity_score_from_metrics(
            bid_levels=50,
            ask_levels=50,
            bid_depth_quote=50_000.0,
            ask_depth_quote=50_000.0,
            bid_larger_depth_quote=100_000.0,
            ask_larger_depth_quote=100_000.0,
            volume_quote=10_000.0,
            bid_ask_spread_ratio=0.0005,
            health_rules=health_fixtures.health_rules(),
            order_book_limit=50,
        )
        assert score >= 0.95


class TestComputeOrdersScore:
    def test_full_visible_book_scores_one_when_at_limit(self):
        score = health_evaluation.compute_orders_score(
            50,
            50,
            health_fixtures.health_rules(),
            order_book_limit=50,
        )
        assert score == 1.0


class TestComputeLiquidityScore:
    def test_averages_four_pillar_scores(self):
        score = health_evaluation.compute_liquidity_score(1.0, 0.8, 0.6, 0.4)
        assert score == pytest.approx((1.0 + 0.8 + 0.6 + 0.4) / 4)


class TestHasUnhealthyRedFlag:
    def test_red_flag_when_larger_depth_below_floor(self):
        assert health_evaluation.has_unhealthy_red_flag(
            bid_levels=20,
            ask_levels=20,
            bid_depth_quote=100.0,
            ask_depth_quote=100.0,
            bid_larger_depth_quote=10.0,
            ask_larger_depth_quote=100.0,
            volume_quote=100000.0,
            bid_ask_spread_ratio=0.001,
            unhealthy_values=health_fixtures.unhealthy_values(),
        ) is True

    def test_no_red_flag_when_larger_depth_passes_despite_low_tight_depth(self):
        assert health_evaluation.has_unhealthy_red_flag(
            bid_levels=20,
            ask_levels=20,
            bid_depth_quote=6.0,
            ask_depth_quote=6.0,
            bid_larger_depth_quote=500.0,
            ask_larger_depth_quote=500.0,
            volume_quote=25000.0,
            bid_ask_spread_ratio=0.001,
            unhealthy_values=health_fixtures.unhealthy_values(),
        ) is False


class TestResolveIsLowHealth:
    def test_red_flag_always_unhealthy(self):
        assert health_evaluation.resolve_is_low_health(True, 0.99, 0.40) is True

    def test_score_below_threshold_unhealthy_without_red_flag(self):
        assert health_evaluation.resolve_is_low_health(False, 0.30, 0.40) is True

    def test_score_at_threshold_healthy_without_red_flag(self):
        assert health_evaluation.resolve_is_low_health(False, 0.40, 0.40) is False


class TestEvaluateHealth:
    def test_low_health_when_bid_levels_below_red_flag(self):
        order_book = {
            "bids": [[100.0, 50.0]] * 4,
            "asks": [[100.05, 50.0]] * 16,
        }
        result = _evaluate(order_book, {"quoteVolume": 10000.0})
        assert result.is_low_health is True
        assert result.bid_levels == 4

    def test_low_health_when_spread_exceeds_red_flag(self):
        order_book = {
            "bids": [[100.0, 50.0]] * 10,
            "asks": [[106.0, 50.0]] * 16,
        }
        result = _evaluate(order_book, {"quoteVolume": 10000.0})
        assert result.is_low_health is True
        assert result.bid_ask_spread_ratio is not None
        assert result.bid_ask_spread_ratio > 0.036

    def test_low_health_when_one_sided_book_cannot_compute_spread(self):
        order_book = {"bids": [[100.0, 50.0]] * 10, "asks": []}
        result = _evaluate(order_book, {"close": 100.0, "quoteVolume": 10000.0})
        assert result.is_low_health is True
        assert result.bid_ask_spread_ratio is None

    def test_low_health_when_mid_price_missing(self):
        order_book = {"bids": [[100.0, 1.0]], "asks": []}
        result = _evaluate(order_book, {})
        assert result.is_low_health is True
        assert result.liquidity_score == 0.0

    def test_healthy_when_red_flags_pass_and_score_above_threshold(self):
        result = _evaluate(_healthy_order_book(), {"quoteVolume": 10000.0})
        assert result.is_low_health is False
        assert result.bid_larger_depth_quote >= result.bid_depth_quote
        assert result.ask_larger_depth_quote >= result.ask_depth_quote
        assert 0.0 < result.liquidity_score <= 1.0

    def test_larger_depth_at_least_tight_depth(self):
        result = _evaluate(_healthy_order_book(), {"quoteVolume": 10000.0})
        assert result.bid_larger_depth_quote >= result.bid_depth_quote
        assert result.ask_larger_depth_quote >= result.ask_depth_quote

    def test_populates_total_depth_from_all_fetched_orders(self):
        order_book = _healthy_order_book()
        expected_bid_total = health_order_book.compute_total_depth_quote(
            health_order_book.sorted_bids(order_book["bids"]),
        )
        expected_ask_total = health_order_book.compute_total_depth_quote(
            health_order_book.sorted_asks(order_book["asks"]),
        )
        result = _evaluate(order_book, {"quoteVolume": 10000.0})
        assert result.bid_total_depth_quote == pytest.approx(expected_bid_total)
        assert result.ask_total_depth_quote == pytest.approx(expected_ask_total)
        assert result.bid_total_depth_quote >= result.bid_larger_depth_quote
        assert result.ask_total_depth_quote >= result.ask_larger_depth_quote


class TestEvaluateHealthFromStoredMetrics:
    def test_stub_row_skips_evaluation(self):
        result = health_evaluation.evaluate_health_from_stored_metrics(
            bid_levels=None,
            ask_levels=None,
            bid_depth_quote=None,
            ask_depth_quote=None,
            bid_larger_depth_quote=None,
            ask_larger_depth_quote=None,
            bid_total_depth_quote=None,
            ask_total_depth_quote=None,
            volume_quote=None,
            bid_ask_spread_ratio=None,
            health_rules=health_fixtures.health_rules(),
            unhealthy_values=health_fixtures.unhealthy_values(),
            health_labels=_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        )
        assert result.is_low_health is False
        assert result.liquidity_score == 0.0
        assert result.health_label_primary == ""
        assert result.health_labels_other == []

    def test_low_health_when_stored_metrics_fail_red_flag(self):
        result = health_evaluation.evaluate_health_from_stored_metrics(
            bid_levels=4,
            ask_levels=20,
            bid_depth_quote=2000.0,
            ask_depth_quote=2000.0,
            bid_larger_depth_quote=2000.0,
            ask_larger_depth_quote=2000.0,
            bid_total_depth_quote=5000.0,
            ask_total_depth_quote=5000.0,
            volume_quote=10000.0,
            bid_ask_spread_ratio=0.001,
            health_rules=health_fixtures.health_rules(),
            unhealthy_values=health_fixtures.unhealthy_values(),
            health_labels=_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        )
        assert result.is_low_health is True
        assert result.health_label_primary == health_evaluation.LABEL_FEW_ORDERS

    def test_low_health_when_stored_spread_exceeds_red_flag(self):
        result = health_evaluation.evaluate_health_from_stored_metrics(
            bid_levels=50,
            ask_levels=50,
            bid_depth_quote=5000.0,
            ask_depth_quote=5000.0,
            bid_larger_depth_quote=5000.0,
            ask_larger_depth_quote=5000.0,
            bid_total_depth_quote=5000.0,
            ask_total_depth_quote=5000.0,
            volume_quote=100000.0,
            bid_ask_spread_ratio=0.051,
            health_rules=health_fixtures.health_rules(),
            unhealthy_values=health_fixtures.unhealthy_values(),
            health_labels=_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        )
        assert result.is_low_health is True
        assert result.health_label_primary == health_evaluation.LABEL_WIDE_SPREAD

    def test_healthy_when_stored_metrics_pass(self):
        result = health_evaluation.evaluate_health_from_stored_metrics(
            bid_levels=50,
            ask_levels=50,
            bid_depth_quote=5000.0,
            ask_depth_quote=5000.0,
            bid_larger_depth_quote=5000.0,
            ask_larger_depth_quote=5000.0,
            bid_total_depth_quote=5000.0,
            ask_total_depth_quote=5000.0,
            volume_quote=100000.0,
            bid_ask_spread_ratio=0.001,
            health_rules=health_fixtures.health_rules(),
            unhealthy_values=health_fixtures.unhealthy_values(),
            health_labels=_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        )
        assert result.is_low_health is False
        assert 0.0 < result.liquidity_score <= 1.0
        assert result.health_label_primary == ""

    def test_red_flag_when_larger_depth_missing_on_complete_row(self):
        result = health_evaluation.evaluate_health_from_stored_metrics(
            bid_levels=50,
            ask_levels=50,
            bid_depth_quote=5000.0,
            ask_depth_quote=5000.0,
            bid_larger_depth_quote=None,
            ask_larger_depth_quote=5000.0,
            bid_total_depth_quote=5000.0,
            ask_total_depth_quote=5000.0,
            volume_quote=100000.0,
            bid_ask_spread_ratio=0.001,
            health_rules=health_fixtures.health_rules(),
            unhealthy_values=health_fixtures.unhealthy_values(),
            health_labels=_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        )
        assert result.is_low_health is True


class TestQualifiesForHealthLabel:
    def test_few_orders_qualifies_when_bid_levels_low(self):
        assert health_evaluation.qualifies_for_health_label(
            health_evaluation.LABEL_FEW_ORDERS,
            bid_levels=4,
            ask_levels=20,
            bid_depth_quote=100.0,
            ask_depth_quote=100.0,
            bid_larger_depth_quote=100.0,
            ask_larger_depth_quote=100.0,
            bid_total_depth_quote=5000.0,
            ask_total_depth_quote=5000.0,
            volume_quote=10000.0,
            bid_ask_spread_ratio=0.001,
            liquidity_score=0.5,
            health_labels=_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        ) is True

    def test_shallow_liquidity_qualifies_when_larger_depth_low(self):
        assert health_evaluation.qualifies_for_health_label(
            health_evaluation.LABEL_SHALLOW_LIQUIDITY,
            bid_levels=20,
            ask_levels=20,
            bid_depth_quote=100.0,
            ask_depth_quote=100.0,
            bid_larger_depth_quote=10.0,
            ask_larger_depth_quote=100.0,
            bid_total_depth_quote=5000.0,
            ask_total_depth_quote=5000.0,
            volume_quote=10000.0,
            bid_ask_spread_ratio=0.001,
            liquidity_score=0.5,
            health_labels=_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        ) is True

    def test_shallow_total_depth_qualifies_when_bid_total_low(self):
        assert health_evaluation.qualifies_for_health_label(
            health_evaluation.LABEL_SHALLOW_TOTAL_DEPTH,
            bid_levels=20,
            ask_levels=20,
            bid_depth_quote=100.0,
            ask_depth_quote=100.0,
            bid_larger_depth_quote=100.0,
            ask_larger_depth_quote=100.0,
            bid_total_depth_quote=1500.0,
            ask_total_depth_quote=5000.0,
            volume_quote=10000.0,
            bid_ask_spread_ratio=0.001,
            liquidity_score=0.5,
            health_labels=_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        ) is True

    def test_under_depth_for_volume_not_qualifying_when_volume_missing(self):
        assert health_evaluation.qualifies_for_health_label(
            health_evaluation.LABEL_UNDER_DEPTH_FOR_VOLUME,
            bid_levels=20,
            ask_levels=20,
            bid_depth_quote=1.0,
            ask_depth_quote=1.0,
            bid_larger_depth_quote=1.0,
            ask_larger_depth_quote=1.0,
            bid_total_depth_quote=5000.0,
            ask_total_depth_quote=5000.0,
            volume_quote=None,
            bid_ask_spread_ratio=0.001,
            liquidity_score=0.5,
            health_labels=_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        ) is False


class TestAssignHealthLabels:
    def test_returns_primary_and_other_labels_in_priority_order(self):
        primary, others = health_evaluation.assign_health_labels(
            ["shallow_liquidity", "few_orders", "wide_spread"],
            _health_labels().priority,
        )
        assert primary == health_evaluation.LABEL_FEW_ORDERS
        assert others == [
            health_evaluation.LABEL_SHALLOW_LIQUIDITY,
            health_evaluation.LABEL_WIDE_SPREAD,
        ]

    def test_returns_empty_when_no_labels_qualify(self):
        assert health_evaluation.assign_health_labels([], _health_labels().priority) == ("", [])


class TestResolveHealthLabels:
    def test_assigns_primary_and_other_for_multiple_qualifying_labels(self):
        primary, others = health_evaluation.resolve_health_labels(
            bid_levels=4,
            ask_levels=20,
            bid_depth_quote=6.0,
            ask_depth_quote=6.0,
            bid_larger_depth_quote=10.0,
            ask_larger_depth_quote=100.0,
            bid_total_depth_quote=5000.0,
            ask_total_depth_quote=5000.0,
            volume_quote=25000.0,
            bid_ask_spread_ratio=0.001,
            liquidity_score=0.5,
            health_labels=_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        )
        assert primary == health_evaluation.LABEL_FEW_ORDERS
        assert health_evaluation.LABEL_SHALLOW_LIQUIDITY in others

    def test_assigns_shallow_total_depth_when_only_total_depth_fails(self):
        primary, others = health_evaluation.resolve_health_labels(
            bid_levels=20,
            ask_levels=20,
            bid_depth_quote=500.0,
            ask_depth_quote=500.0,
            bid_larger_depth_quote=500.0,
            ask_larger_depth_quote=500.0,
            bid_total_depth_quote=1500.0,
            ask_total_depth_quote=2500.0,
            volume_quote=100000.0,
            bid_ask_spread_ratio=0.001,
            liquidity_score=0.5,
            health_labels=_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        )
        assert primary == health_evaluation.LABEL_SHALLOW_TOTAL_DEPTH
        assert others == []


class TestCheckListingHealth:
    @pytest.mark.asyncio
    async def test_fetches_order_book_and_ticker(self):
        class FakeClient:
            async def fetch_order_book(self, symbol, limit=50):
                assert symbol == "BTC/USDT"
                return {"bids": [[100.0, 1.0]], "asks": []}

            async def fetch_ticker(self, symbol):
                assert symbol == "BTC/USDT"
                return {"quoteVolume": 0}

        result = await listing_health_fetcher.check_listing_health(
            FakeClient(),
            "BTC/USDT",
            50,
            health_fixtures.health_rules(),
            health_fixtures.unhealthy_values(),
            _health_labels(),
            health_fixtures.min_liquidity_score(),
        )
        assert result.is_low_health is True
