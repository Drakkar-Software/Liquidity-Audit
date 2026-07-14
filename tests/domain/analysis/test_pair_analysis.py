import pytest

import tests.fixtures.health_fixtures as health_fixtures
import tests.fixtures.health_label_fixtures as health_label_fixtures
import liquidity_audit.domain.analysis.pair_analysis as token_analysis
import liquidity_audit.domain.health.evaluation as health_evaluation


def _order_book_with_depth(mid_price: float = 100.0, ask_levels: int = 20) -> dict:
    bids = [[mid_price - 0.01 - index * 0.05, 10.0] for index in range(10)]
    asks = [[mid_price + 0.01 + index * 0.05, 10.0] for index in range(ask_levels)]
    return {"bids": bids, "asks": asks}


class TestParseTickerVolumeSkew:
    def test_computes_buy_and_sell_percentages(self):
        bid_volume, ask_volume, buy_pct, sell_pct = token_analysis.parse_ticker_volume_skew({
            "bidVolume": 3000.0,
            "askVolume": 7000.0,
        })
        assert bid_volume == 3000.0
        assert ask_volume == 7000.0
        assert buy_pct == pytest.approx(30.0)
        assert sell_pct == pytest.approx(70.0)

    def test_returns_none_percentages_when_volume_missing(self):
        bid_volume, ask_volume, buy_pct, sell_pct = token_analysis.parse_ticker_volume_skew({})
        assert bid_volume is None
        assert ask_volume is None
        assert buy_pct is None
        assert sell_pct is None


class TestSimulateMarketBuySlippage:
    def test_omits_size_when_book_cannot_fill(self):
        asks = [[100.0, 1.0]]
        rows = token_analysis.simulate_market_buy_slippage(asks, mid_price=100.0, trade_sizes=(1000,))
        assert rows[0]["omitted"] is True
        assert rows[0]["fill_ratio"] < token_analysis.MIN_FILL_RATIO

    def test_computes_slippage_when_book_fills_trade(self):
        asks = [[100.0, 100.0]]
        rows = token_analysis.simulate_market_buy_slippage(asks, mid_price=99.0, trade_sizes=(1000,))
        assert rows[0]["omitted"] is False
        assert rows[0]["pct"] is not None
        assert rows[0]["pct"] > 0


class TestScoreToGrade:
    def test_maps_score_to_letter_grade(self):
        assert token_analysis.score_to_grade(90) == "A"
        assert token_analysis.score_to_grade(42) == "D"
        assert token_analysis.score_to_grade(10) == "F"


class TestBuildExtendedRawMetrics:
    def test_includes_depth_2pct_and_volume_skew(self):
        order_book = _order_book_with_depth()
        ticker = {
            "quoteVolume": 50_000.0,
            "bidVolume": 20_000.0,
            "askVolume": 30_000.0,
        }
        health = health_evaluation.evaluate_health(
            order_book,
            ticker,
            health_rules=health_fixtures.health_rules(),
            unhealthy_values=health_fixtures.unhealthy_values(),
            health_labels=health_label_fixtures.default_health_labels(),
            min_liquidity_score=health_fixtures.min_liquidity_score(),
        )
        raw_metrics = token_analysis.build_extended_raw_metrics(
            "mexc",
            "XYZ/USDT",
            "XYZ",
            order_book,
            ticker,
            health,
            "2026-06-12T00:00:00+00:00",
        )
        assert raw_metrics.depth_2pct_quote > 0
        assert raw_metrics.buy_volume_pct == pytest.approx(40.0)
        assert raw_metrics.max_fillable_buy_quote > 0


class TestSelectPeerSymbols:
    def test_selects_peers_in_same_volume_tier(self):
        target = token_analysis.ExtendedRawMetrics(
            exchange="mexc",
            symbol="AAA/USDT",
            full_name="AAA",
            mid_price=1.0,
            spread_pct=1.0,
            bid_levels=10,
            ask_levels=10,
            bid_depth_1pct_quote=100.0,
            ask_depth_1pct_quote=100.0,
            depth_1pct_quote=200.0,
            depth_2pct_quote=300.0,
            depth_10pct_quote=500.0,
            bid_larger_depth_quote=250.0,
            ask_larger_depth_quote=250.0,
            depth_2pct_capped=False,
            volume_quote=10_000.0,
            bid_volume_quote=5000.0,
            ask_volume_quote=5000.0,
            buy_volume_pct=50.0,
            sell_volume_pct=50.0,
            volume_depth_ratio=5.0,
            max_fillable_buy_quote=1000.0,
            liquidity_score=0.5,
            is_low_health=False,
            health_label_primary="",
            health_labels_other=[],
            slippage=[],
            fetched_at="2026-06-12T00:00:00+00:00",
        )
        peer_high_volume = token_analysis.ExtendedRawMetrics(
            **{**target.__dict__, "symbol": "BBB/USDT", "liquidity_score": 0.9, "volume_quote": 12_000.0},
        )
        peer_wrong_quote = token_analysis.ExtendedRawMetrics(
            **{**target.__dict__, "symbol": "CCC/BTC", "liquidity_score": 0.95},
        )
        peers = token_analysis.select_peer_symbols(
            target,
            [target, peer_high_volume, peer_wrong_quote],
        )
        assert len(peers) == 1
        assert peers[0].symbol == "BBB/USDT"


class TestBuildPairAnalysis:
    def test_produces_score_and_verdict(self):
        raw_metrics = token_analysis.ExtendedRawMetrics(
            exchange="mexc",
            symbol="XYZ/USDT",
            full_name="XYZ",
            mid_price=1.0,
            spread_pct=2.8,
            bid_levels=10,
            ask_levels=16,
            bid_depth_1pct_quote=100.0,
            ask_depth_1pct_quote=100.0,
            depth_1pct_quote=200.0,
            depth_2pct_quote=9_500.0,
            depth_10pct_quote=20_000.0,
            bid_larger_depth_quote=10_000.0,
            ask_larger_depth_quote=10_000.0,
            depth_2pct_capped=True,
            volume_quote=1_200_000.0,
            bid_volume_quote=120_000.0,
            ask_volume_quote=1_080_000.0,
            buy_volume_pct=10.0,
            sell_volume_pct=90.0,
            volume_depth_ratio=6000.0,
            max_fillable_buy_quote=25_000.0,
            liquidity_score=0.42,
            is_low_health=True,
            health_label_primary="wide_spread",
            health_labels_other=[],
            slippage=token_analysis.simulate_market_buy_slippage(
                [[1.0, 30_000.0]],
                mid_price=1.0,
            ),
            fetched_at="2026-06-12T00:00:00+00:00",
        )
        exchange_averages = {
            "exchange_avg_spread_pct": 0.5,
            "exchange_avg_depth_2pct": 100_000.0,
            "exchange_avg_slippage_10k": 1.0,
            "exchange_median_volume_depth_ratio": 10.0,
            "exchange_median_volume_quote": 500_000.0,
        }
        health_labels = health_label_fixtures.default_health_labels()
        pair_analysis = token_analysis.build_pair_analysis(
            raw_metrics,
            [raw_metrics],
            exchange_averages,
            health_labels,
        )
        assert pair_analysis["analysis"]["score_100"] == 42
        assert pair_analysis["analysis"]["score_breakdown"]["internal_100"] == 42
        assert pair_analysis["analysis"]["score_breakdown"]["peer_relative_100"] is None
        assert pair_analysis["analysis"]["grade"] == "D"
        assert "XYZ/USDT" in pair_analysis["analysis"]["verdict"]
        assert pair_analysis["analysis"]["root_causes"]


def _minimal_raw_metrics_for_scoring(**overrides) -> token_analysis.ExtendedRawMetrics:
    defaults = {
        "exchange": "mexc",
        "symbol": "AAA/USDT",
        "full_name": "AAA",
        "mid_price": 1.0,
        "spread_pct": 1.0,
        "bid_levels": 10,
        "ask_levels": 10,
        "bid_depth_1pct_quote": 100.0,
        "ask_depth_1pct_quote": 100.0,
        "depth_1pct_quote": 200.0,
        "depth_2pct_quote": 300.0,
        "depth_10pct_quote": 500.0,
        "bid_larger_depth_quote": 250.0,
        "ask_larger_depth_quote": 250.0,
        "depth_2pct_capped": False,
        "volume_quote": 10_000.0,
        "bid_volume_quote": 5000.0,
        "ask_volume_quote": 5000.0,
        "buy_volume_pct": 50.0,
        "sell_volume_pct": 50.0,
        "volume_depth_ratio": 5.0,
        "max_fillable_buy_quote": 1000.0,
        "liquidity_score": 0.5,
        "is_low_health": False,
        "health_label_primary": "",
        "health_labels_other": [],
        "slippage": [
            {"size": 1000, "pct": 2.0, "omitted": False, "fill_ratio": 1.0},
        ],
        "fetched_at": "2026-06-12T00:00:00+00:00",
    }
    defaults.update(overrides)
    return token_analysis.ExtendedRawMetrics(**defaults)


class TestComputePeerRelativeScore:
    def test_depth_half_of_peer_median_scores_point_five(self):
        target = _minimal_raw_metrics_for_scoring(depth_2pct_quote=500.0)
        peer_median = {"spread": 0.0, "depth": 1000.0, "slippage_pct": None}
        score = token_analysis.compute_peer_relative_score(target, peer_median)
        assert score == pytest.approx(0.5)

    def test_near_peer_median_depth_scores_one_with_deadband(self):
        target = _minimal_raw_metrics_for_scoring(depth_2pct_quote=960.0)
        peer_median = {"spread": 0.0, "depth": 1000.0, "slippage_pct": None}
        score = token_analysis.compute_peer_relative_score(target, peer_median)
        assert score == pytest.approx(1.0)

    def test_spread_twice_peer_median_scores_point_five(self):
        target = _minimal_raw_metrics_for_scoring(spread_pct=2.0)
        peer_median = {"spread": 1.0, "depth": 0.0, "slippage_pct": None}
        score = token_analysis.compute_peer_relative_score(target, peer_median)
        assert score == pytest.approx(0.5)

    def test_worse_slippage_than_peers_lowers_score(self):
        target = _minimal_raw_metrics_for_scoring(
            slippage=[{"size": 1000, "pct": 8.0, "omitted": False, "fill_ratio": 1.0}],
        )
        peer_median = {"spread": 0.0, "depth": 0.0, "slippage_pct": 2.0}
        score = token_analysis.compute_peer_relative_score(target, peer_median)
        assert score == pytest.approx(0.25)


class TestComputeCompositeScore:
    def test_no_peers_uses_internal_score_only(self):
        target = _minimal_raw_metrics_for_scoring(liquidity_score=0.8)
        composite, peer_relative = token_analysis.compute_composite_score(target, [target])
        assert composite == pytest.approx(0.8)
        assert peer_relative is None

    def test_high_internal_pulled_down_by_poor_peer_relative(self):
        target = _minimal_raw_metrics_for_scoring(
            symbol="TARGET/USDT",
            liquidity_score=1.0,
            depth_2pct_quote=100.0,
            spread_pct=2.0,
            slippage=[{"size": 1000, "pct": 10.0, "omitted": False, "fill_ratio": 1.0}],
            volume_quote=10_000.0,
        )
        peer = _minimal_raw_metrics_for_scoring(
            symbol="PEER/USDT",
            liquidity_score=0.5,
            depth_2pct_quote=1000.0,
            spread_pct=1.0,
            slippage=[{"size": 1000, "pct": 2.0, "omitted": False, "fill_ratio": 1.0}],
            volume_quote=12_000.0,
        )
        composite, peer_relative = token_analysis.compute_composite_score(
            target,
            [target, peer],
        )
        assert peer_relative is not None
        assert peer_relative < 0.5
        assert composite < 1.0
        assert composite == pytest.approx((1.0 + peer_relative) / 2)


class TestBuildPairAnalysisCompositeScore:
    def test_includes_peer_relative_when_peers_exist(self):
        target = _minimal_raw_metrics_for_scoring(
            symbol="TARGET/USDT",
            liquidity_score=1.0,
            depth_2pct_quote=100.0,
            spread_pct=2.0,
            slippage=[{"size": 1000, "pct": 10.0, "omitted": False, "fill_ratio": 1.0}],
        )
        peer = _minimal_raw_metrics_for_scoring(
            symbol="PEER/USDT",
            liquidity_score=0.5,
            depth_2pct_quote=1000.0,
            spread_pct=1.0,
            slippage=[{"size": 1000, "pct": 2.0, "omitted": False, "fill_ratio": 1.0}],
            volume_quote=12_000.0,
        )
        exchange_averages = {
            "exchange_avg_spread_pct": 1.0,
            "exchange_avg_depth_2pct": 500.0,
            "exchange_avg_slippage_10k": 2.0,
            "exchange_median_volume_depth_ratio": 5.0,
            "exchange_median_volume_quote": 10_000.0,
        }
        health_labels = health_label_fixtures.default_health_labels()
        payload = token_analysis.build_pair_analysis(
            target,
            [target, peer],
            exchange_averages,
            health_labels,
        )
        assert payload["analysis"]["score_100"] < 100
        assert payload["analysis"]["score_breakdown"]["internal_100"] == 100
        assert payload["analysis"]["score_breakdown"]["peer_relative_100"] is not None


class TestQualifiesForPerfectScore:
    def test_usdc_like_pair_scores_one_hundred(self):
        target = _minimal_raw_metrics_for_scoring(
            symbol="USDC/USDT",
            liquidity_score=0.75,
            bid_levels=50,
            ask_levels=50,
            spread_pct=0.001,
            depth_2pct_quote=47_413_109.0,
            volume_quote=28_963_294.0,
            volume_depth_ratio=0.61,
            slippage=[{"size": 10_000, "pct": 0.0005, "omitted": False, "fill_ratio": 1.0}],
        )
        peer = _minimal_raw_metrics_for_scoring(
            symbol="TRX/USDT",
            liquidity_score=0.6,
            depth_2pct_quote=5_305_387.0,
            spread_pct=0.03,
            volume_quote=25_000_000.0,
            slippage=[{"size": 10_000, "pct": 0.015, "omitted": False, "fill_ratio": 1.0}],
        )
        exchange_averages = {
            "exchange_avg_spread_pct": 0.36,
            "exchange_avg_depth_2pct": 3_800.0,
            "exchange_avg_slippage_10k": 1.07,
            "exchange_median_volume_depth_ratio": 27.4,
            "exchange_median_volume_quote": 10_000_000.0,
        }
        health_labels = health_label_fixtures.default_health_labels()
        payload = token_analysis.build_pair_analysis(
            target,
            [target, peer],
            exchange_averages,
            health_labels,
        )
        assert payload["analysis"]["score_100"] == 100
        assert all(issue["ok"] for issue in payload["analysis"]["issues"])
        assert all(
            row["severity"] == "Low" for row in payload["analysis"]["health_dashboard"]
        )

    def test_low_health_pair_does_not_floor_to_one_hundred(self):
        target = _minimal_raw_metrics_for_scoring(
            symbol="WEAK/USDT",
            liquidity_score=0.75,
            is_low_health=True,
            health_label_primary=health_evaluation.LABEL_WIDE_SPREAD,
            spread_pct=0.001,
            depth_2pct_quote=47_413_109.0,
            volume_quote=28_963_294.0,
            volume_depth_ratio=0.61,
            slippage=[{"size": 10_000, "pct": 0.0005, "omitted": False, "fill_ratio": 1.0}],
        )
        exchange_averages = {
            "exchange_avg_spread_pct": 0.36,
            "exchange_avg_depth_2pct": 3_800.0,
            "exchange_avg_slippage_10k": 1.07,
            "exchange_median_volume_depth_ratio": 27.4,
            "exchange_median_volume_quote": 10_000_000.0,
        }
        payload = token_analysis.build_pair_analysis(
            target,
            [target],
            exchange_averages,
            health_label_fixtures.default_health_labels(),
        )
        assert payload["analysis"]["score_100"] < 100


class TestBuildRankings:
    def test_ranking_order_follows_composite_not_internal_alone(self):
        stronger_internal = _minimal_raw_metrics_for_scoring(
            symbol="STRONG/USDT",
            liquidity_score=0.9,
            depth_2pct_quote=50.0,
            spread_pct=2.0,
            slippage=[{"size": 1000, "pct": 8.0, "omitted": False, "fill_ratio": 1.0}],
            volume_quote=10_000.0,
        )
        weaker_internal_better_peers = _minimal_raw_metrics_for_scoring(
            symbol="MID/USDT",
            liquidity_score=0.7,
            depth_2pct_quote=500.0,
            spread_pct=1.0,
            slippage=[{"size": 1000, "pct": 2.0, "omitted": False, "fill_ratio": 1.0}],
            volume_quote=11_000.0,
        )
        peer_for_strong = _minimal_raw_metrics_for_scoring(
            symbol="PEER/USDT",
            liquidity_score=0.5,
            depth_2pct_quote=1000.0,
            spread_pct=1.0,
            slippage=[{"size": 1000, "pct": 2.0, "omitted": False, "fill_ratio": 1.0}],
            volume_quote=12_000.0,
        )
        universe = [stronger_internal, weaker_internal_better_peers, peer_for_strong]
        rankings = token_analysis.build_rankings(universe, rankings_min_volume_quote=1000.0)
        symbols_by_rank = [row["symbol"] for row in rankings]
        assert symbols_by_rank.index("MID/USDT") < symbols_by_rank.index("STRONG/USDT")

    def test_includes_ineligible_pairs_with_zero_volume_and_null_rank(self):
        eligible = _minimal_raw_metrics_for_scoring(
            symbol="SOL/USDT",
            liquidity_score=0.8,
            volume_quote=10_000.0,
        )
        ineligible = _minimal_raw_metrics_for_scoring(
            symbol="ULX/USDT",
            liquidity_score=0.15,
            volume_quote=None,
        )
        rankings = token_analysis.build_rankings(
            [eligible, ineligible],
            rankings_min_volume_quote=1000.0,
        )
        assert len(rankings) == 2
        ulx_row = next(row for row in rankings if row["symbol"] == "ULX/USDT")
        assert ulx_row["volume_quote"] == 0
        assert ulx_row["rank"] is None
        sol_row = next(row for row in rankings if row["symbol"] == "SOL/USDT")
        assert sol_row["rank"] == 1


def _exchange_averages_for_volume_tests() -> dict[str, float]:
    return {
        "exchange_avg_spread_pct": 0.93,
        "exchange_avg_depth_2pct": 3_600.0,
        "exchange_avg_slippage_10k": 2.76,
        "exchange_median_volume_depth_ratio": 60.8,
    }


def _high_liquidity_raw_metrics(**overrides) -> token_analysis.ExtendedRawMetrics:
    defaults = {
        "exchange": "bitmart",
        "symbol": "BTC/USDT",
        "full_name": "Bitcoin",
        "mid_price": 64_210.0,
        "spread_pct": 0.00005,
        "bid_levels": 50,
        "ask_levels": 50,
        "bid_depth_1pct_quote": 6_306_349.0,
        "ask_depth_1pct_quote": 6_341_707.0,
        "depth_1pct_quote": 12_648_056.0,
        "depth_2pct_quote": 12_648_056.0,
        "depth_10pct_quote": 12_648_056.0,
        "bid_larger_depth_quote": 6_306_349.0,
        "ask_larger_depth_quote": 6_341_707.0,
        "depth_2pct_capped": True,
        "volume_quote": 233_048_420.0,
        "bid_volume_quote": 0.26,
        "ask_volume_quote": 0.33,
        "buy_volume_pct": 44.0,
        "sell_volume_pct": 56.0,
        "volume_depth_ratio": 18.4,
        "max_fillable_buy_quote": 6_341_707.0,
        "liquidity_score": 1.0,
        "is_low_health": False,
        "health_label_primary": "",
        "health_labels_other": [],
        "slippage": [
            {"size": 10_000, "pct": 0.00002, "omitted": False, "fill_ratio": 1.0},
        ],
        "fetched_at": "2026-06-13T14:48:32+00:00",
    }
    defaults.update(overrides)
    return token_analysis.ExtendedRawMetrics(**defaults)


class TestVolumeConsistencySeverityAndImpact:
    def test_exempts_high_liquidity_pair_with_elevated_vol_depth_ratio(self):
        raw_metrics = _high_liquidity_raw_metrics()
        severity, impact = token_analysis._volume_consistency_severity_and_impact(
            raw_metrics,
            _exchange_averages_for_volume_tests(),
        )
        assert severity == "Low"
        assert impact == "Within normal range"

    def test_flags_hollow_volume_when_liquidity_score_is_low(self):
        raw_metrics = _high_liquidity_raw_metrics(
            liquidity_score=0.42,
            volume_depth_ratio=6000.0,
            spread_pct=2.8,
            depth_2pct_quote=9_500.0,
            slippage=[
                {"size": 10_000, "pct": 8.2, "omitted": False, "fill_ratio": 1.0},
            ],
        )
        severity, impact = token_analysis._volume_consistency_severity_and_impact(
            raw_metrics,
            _exchange_averages_for_volume_tests(),
        )
        assert severity == "Critical"
        assert impact == "Hollow volume risk"

    def test_build_health_dashboard_uses_exemption_for_major_pair(self):
        raw_metrics = _high_liquidity_raw_metrics()
        cards = token_analysis.build_health_dashboard(
            raw_metrics,
            _exchange_averages_for_volume_tests(),
        )
        volume_card = next(card for card in cards if card["title"] == "Volume consistency")
        assert volume_card["severity"] == "Low"
        assert volume_card["impact"] == "Within normal range"


class TestComparisonImpactWording:
    def test_verdict_uses_positive_wording_when_slippage_is_better_than_average(self):
        raw_metrics = _high_liquidity_raw_metrics()
        verdict = token_analysis.build_verdict(
            raw_metrics,
            _exchange_averages_for_volume_tests(),
        )
        assert "at or better than" in verdict
        assert "0× worse" not in verdict

    def test_slippage_impact_uses_positive_wording_when_better_than_average(self):
        raw_metrics = _high_liquidity_raw_metrics()
        cards = token_analysis.build_health_dashboard(
            raw_metrics,
            _exchange_averages_for_volume_tests(),
        )
        slippage_card = next(card for card in cards if card["title"].startswith("Slippage"))
        assert slippage_card["impact"] == "Better than average"
        assert "worse than average" not in slippage_card["impact"].lower()


class TestOmittedSlippageAtTenThousand:
    def test_peer_row_keeps_null_instead_of_zero_when_ten_k_is_omitted(self):
        raw_metrics = token_analysis.ExtendedRawMetrics(
            exchange="mexc",
            symbol="XX/USDT",
            full_name="xx network",
            mid_price=0.004,
            spread_pct=0.7,
            bid_levels=40,
            ask_levels=40,
            bid_depth_1pct_quote=300.0,
            ask_depth_1pct_quote=10.0,
            depth_1pct_quote=310.0,
            depth_2pct_quote=310.0,
            depth_10pct_quote=1000.0,
            bid_larger_depth_quote=900.0,
            ask_larger_depth_quote=400.0,
            depth_2pct_capped=False,
            volume_quote=30_000.0,
            bid_volume_quote=100.0,
            ask_volume_quote=50.0,
            buy_volume_pct=66.0,
            sell_volume_pct=34.0,
            volume_depth_ratio=100.0,
            max_fillable_buy_quote=7000.0,
            liquidity_score=0.5,
            is_low_health=False,
            health_label_primary="",
            health_labels_other=[],
            slippage=[
                {"size": 1000, "pct": 8.36, "omitted": False, "fill_ratio": 1.0},
                {"size": 5000, "pct": 38.09, "omitted": False, "fill_ratio": 1.0},
                {"size": 10000, "pct": None, "omitted": True, "fill_ratio": 0.73},
            ],
            fetched_at="2026-06-13T00:00:00+00:00",
        )

        peer_row = token_analysis.peer_row_from_raw(raw_metrics, is_yours=True)

        assert peer_row["slippage_trade_size"] == 1000
        assert peer_row["slippage_pct"] == 8.36
        assert "slippage_10k" not in peer_row

    def test_investor_simulator_includes_unfillable_ten_k_row(self):
        raw_metrics = token_analysis.ExtendedRawMetrics(
            exchange="mexc",
            symbol="XX/USDT",
            full_name="xx network",
            mid_price=0.004,
            spread_pct=0.7,
            bid_levels=40,
            ask_levels=40,
            bid_depth_1pct_quote=300.0,
            ask_depth_1pct_quote=10.0,
            depth_1pct_quote=310.0,
            depth_2pct_quote=310.0,
            depth_10pct_quote=1000.0,
            bid_larger_depth_quote=900.0,
            ask_larger_depth_quote=400.0,
            depth_2pct_capped=False,
            volume_quote=30_000.0,
            bid_volume_quote=100.0,
            ask_volume_quote=50.0,
            buy_volume_pct=66.0,
            sell_volume_pct=34.0,
            volume_depth_ratio=100.0,
            max_fillable_buy_quote=7000.0,
            liquidity_score=0.5,
            is_low_health=False,
            health_label_primary="",
            health_labels_other=[],
            slippage=[
                {"size": 1000, "pct": 8.36, "omitted": False, "fill_ratio": 1.0},
                {"size": 10000, "pct": None, "omitted": True, "fill_ratio": 0.73},
            ],
            fetched_at="2026-06-13T00:00:00+00:00",
        )

        simulator_rows = token_analysis.build_investor_simulator(raw_metrics)
        one_k_row = next(row for row in simulator_rows if row["size"] == 1000)
        ten_k_row = next(row for row in simulator_rows if row["size"] == 10_000)

        assert len(simulator_rows) == 2
        assert [row["size"] for row in simulator_rows] == [10_000, 1000]
        assert one_k_row["highlight"] is True
        assert ten_k_row["omitted"] is True
        assert ten_k_row["fill_ratio"] == 0.73

    def test_investor_simulator_shows_top_three_largest_available(self):
        raw_metrics = token_analysis.ExtendedRawMetrics(
            exchange="mexc",
            symbol="XX/USDT",
            full_name="xx network",
            mid_price=0.004,
            spread_pct=0.7,
            bid_levels=40,
            ask_levels=40,
            bid_depth_1pct_quote=300.0,
            ask_depth_1pct_quote=10.0,
            depth_1pct_quote=310.0,
            depth_2pct_quote=310.0,
            depth_10pct_quote=1000.0,
            bid_larger_depth_quote=900.0,
            ask_larger_depth_quote=400.0,
            depth_2pct_capped=False,
            volume_quote=30_000.0,
            bid_volume_quote=100.0,
            ask_volume_quote=50.0,
            buy_volume_pct=66.0,
            sell_volume_pct=34.0,
            volume_depth_ratio=100.0,
            max_fillable_buy_quote=7000.0,
            liquidity_score=0.5,
            is_low_health=False,
            health_label_primary="",
            health_labels_other=[],
            slippage=[
                {"size": 1000, "pct": 8.36, "omitted": False, "fill_ratio": 1.0},
                {"size": 5000, "pct": 38.09, "omitted": False, "fill_ratio": 1.0},
                {"size": 10000, "pct": None, "omitted": True, "fill_ratio": 0.73},
                {"size": 25000, "pct": None, "omitted": True, "fill_ratio": 0.29},
            ],
            fetched_at="2026-06-13T00:00:00+00:00",
        )

        simulator_rows = token_analysis.build_investor_simulator(raw_metrics)

        assert len(simulator_rows) == 3
        assert [row["size"] for row in simulator_rows] == [10_000, 5_000, 1_000]
        one_k_row = next(row for row in simulator_rows if row["size"] == 1000)
        ten_k_row = next(row for row in simulator_rows if row["size"] == 10_000)

        assert one_k_row["highlight"] is True
        assert ten_k_row["omitted"] is True
        assert 25_000 not in {row["size"] for row in simulator_rows}

    def test_lost_opportunity_uses_resolved_display_size(self):
        raw_metrics = token_analysis.ExtendedRawMetrics(
            exchange="mexc",
            symbol="XX/USDT",
            full_name="xx network",
            mid_price=0.004,
            spread_pct=0.7,
            bid_levels=40,
            ask_levels=40,
            bid_depth_1pct_quote=300.0,
            ask_depth_1pct_quote=10.0,
            depth_1pct_quote=310.0,
            depth_2pct_quote=310.0,
            depth_10pct_quote=1000.0,
            bid_larger_depth_quote=900.0,
            ask_larger_depth_quote=400.0,
            depth_2pct_capped=False,
            volume_quote=30_000.0,
            bid_volume_quote=100.0,
            ask_volume_quote=50.0,
            buy_volume_pct=66.0,
            sell_volume_pct=34.0,
            volume_depth_ratio=100.0,
            max_fillable_buy_quote=7000.0,
            liquidity_score=0.5,
            is_low_health=False,
            health_label_primary="",
            health_labels_other=[],
            slippage=[
                {"size": 1000, "pct": 8.36, "omitted": False, "fill_ratio": 1.0},
                {"size": 5000, "pct": 38.09, "omitted": False, "fill_ratio": 1.0},
                {"size": 10000, "pct": None, "omitted": True, "fill_ratio": 0.73},
            ],
            fetched_at="2026-06-13T00:00:00+00:00",
        )

        lost_opportunity = token_analysis.build_lost_opportunity(raw_metrics)

        assert lost_opportunity["size"] == 1000
        assert lost_opportunity["cost"] == pytest.approx(83.6, rel=1e-2)
        assert lost_opportunity["range"] == "8.4–38.1%"

    def test_build_improvements_handles_null_median_slippage(self):
        raw_metrics = token_analysis.ExtendedRawMetrics(
            exchange="mexc",
            symbol="XX/USDT",
            full_name="xx network",
            mid_price=0.004,
            spread_pct=0.7,
            bid_levels=40,
            ask_levels=40,
            bid_depth_1pct_quote=300.0,
            ask_depth_1pct_quote=10.0,
            depth_1pct_quote=310.0,
            depth_2pct_quote=310.0,
            depth_10pct_quote=1000.0,
            bid_larger_depth_quote=900.0,
            ask_larger_depth_quote=400.0,
            depth_2pct_capped=False,
            volume_quote=30_000.0,
            bid_volume_quote=100.0,
            ask_volume_quote=50.0,
            buy_volume_pct=66.0,
            sell_volume_pct=34.0,
            volume_depth_ratio=100.0,
            max_fillable_buy_quote=7000.0,
            liquidity_score=0.5,
            is_low_health=False,
            health_label_primary="",
            health_labels_other=[],
            slippage=[
                {"size": 1000, "pct": 8.36, "omitted": False, "fill_ratio": 1.0},
                {"size": 10000, "pct": None, "omitted": True, "fill_ratio": 0.73},
            ],
            fetched_at="2026-06-13T00:00:00+00:00",
        )
        peer_median = {
            "name": "Median",
            "spread": 0.1,
            "depth": 14_000.0,
            "slippage_trade_size": None,
            "slippage_pct": None,
            "is_yours": False,
        }

        improvements = token_analysis.build_improvements(raw_metrics, peer_median)
        slippage_row = next(row for row in improvements if row["metric"].startswith("Slippage"))

        assert slippage_row["current"] == "8.4%"
        assert slippage_row["potential"] == "—"

    def test_resolve_slippage_display_prefers_ten_k_then_one_k_then_one_hundred(self):
        slippage_rows = [
            {"size": 100, "pct": 0.5, "omitted": False, "fill_ratio": 1.0},
            {"size": 1000, "pct": 2.0, "omitted": False, "fill_ratio": 1.0},
            {"size": 10000, "pct": None, "omitted": True, "fill_ratio": 0.5},
        ]
        trade_size, slippage_pct = token_analysis.resolve_slippage_display(slippage_rows)
        assert trade_size == 1000
        assert slippage_pct == 2.0

        slippage_rows_only_small = [
            {"size": 100, "pct": 0.5, "omitted": False, "fill_ratio": 1.0},
            {"size": 1000, "pct": None, "omitted": True, "fill_ratio": 0.5},
            {"size": 10000, "pct": None, "omitted": True, "fill_ratio": 0.2},
        ]
        trade_size, slippage_pct = token_analysis.resolve_slippage_display(slippage_rows_only_small)
        assert trade_size == 100
        assert slippage_pct == 0.5


def _peer_selection_settings(**overrides) -> token_analysis.PeerSelectionSettings:
    defaults = {
        "min_relevant_usdt_volume": 100.0,
        "peer_volume_tier_ratios": (5.0, 20.0, 100.0),
        "peer_count": 3,
    }
    defaults.update(overrides)
    return token_analysis.PeerSelectionSettings(**defaults)


def _peer_raw_metrics(**overrides) -> token_analysis.ExtendedRawMetrics:
    defaults = {
        "exchange": "bitmart",
        "symbol": "AAA/USDT",
        "full_name": "AAA",
        "mid_price": 1.0,
        "spread_pct": 1.0,
        "bid_levels": 10,
        "ask_levels": 10,
        "bid_depth_1pct_quote": 100.0,
        "ask_depth_1pct_quote": 100.0,
        "depth_1pct_quote": 200.0,
        "depth_2pct_quote": 300.0,
        "depth_10pct_quote": 500.0,
        "bid_larger_depth_quote": 250.0,
        "ask_larger_depth_quote": 250.0,
        "depth_2pct_capped": False,
        "volume_quote": 10_000.0,
        "bid_volume_quote": 5000.0,
        "ask_volume_quote": 5000.0,
        "buy_volume_pct": 50.0,
        "sell_volume_pct": 50.0,
        "volume_depth_ratio": 5.0,
        "max_fillable_buy_quote": 1000.0,
        "liquidity_score": 0.5,
        "is_low_health": False,
        "health_label_primary": "",
        "health_labels_other": [],
        "slippage": [],
        "fetched_at": "2026-06-12T00:00:00+00:00",
    }
    defaults.update(overrides)
    return token_analysis.ExtendedRawMetrics(**defaults)


class TestResolvePeerVolume:
    def test_uses_quote_volume_when_present(self):
        raw_metrics = _peer_raw_metrics(volume_quote=12_345.0, bid_volume_quote=1.0, ask_volume_quote=2.0)
        assert token_analysis.resolve_peer_volume(raw_metrics) == 12_345.0

    def test_uses_bid_ask_sum_when_quote_volume_missing(self):
        raw_metrics = _peer_raw_metrics(
            volume_quote=None,
            bid_volume_quote=1_790_254.0,
            ask_volume_quote=427_383.0,
        )
        assert token_analysis.resolve_peer_volume(raw_metrics) == pytest.approx(2_217_637.0)

    def test_returns_zero_when_all_volume_fields_missing(self):
        raw_metrics = _peer_raw_metrics(
            volume_quote=None,
            bid_volume_quote=None,
            ask_volume_quote=None,
        )
        assert token_analysis.resolve_peer_volume(raw_metrics) == 0.0


class TestSelectPeerSymbolsWithFallback:
    def test_ulx_like_proxy_volume_matches_volume_5x_tier(self):
        target = _peer_raw_metrics(
            symbol="ULX/USDT",
            volume_quote=None,
            bid_volume_quote=1_790_254.0,
            ask_volume_quote=427_383.0,
            liquidity_score=0.15,
        )
        peer_close = _peer_raw_metrics(
            symbol="BBB/USDT",
            volume_quote=2_000_000.0,
            liquidity_score=0.8,
        )
        peers, tier, _criteria = token_analysis.select_peer_symbols_with_fallback(
            target,
            [target, peer_close],
            _peer_selection_settings(),
        )
        assert len(peers) == 1
        assert peers[0].symbol == "BBB/USDT"
        assert tier == "volume_5x"

    def test_micro_bucket_matches_only_micro_volume_peers(self):
        target = _peer_raw_metrics(
            symbol="MICRO/USDT",
            volume_quote=None,
            bid_volume_quote=30.0,
            ask_volume_quote=20.0,
            liquidity_score=0.2,
        )
        micro_peer = _peer_raw_metrics(
            symbol="MICRO2/USDT",
            volume_quote=50.0,
            liquidity_score=0.7,
        )
        peers, tier, _criteria = token_analysis.select_peer_symbols_with_fallback(
            target,
            [target, micro_peer],
            _peer_selection_settings(),
        )
        assert [peer.symbol for peer in peers] == ["MICRO2/USDT"]
        assert tier == "volume_micro_bucket"

    def test_widens_to_20x_when_5x_insufficient(self):
        target = _peer_raw_metrics(symbol="TARGET/USDT", volume_quote=10_000.0)
        peer_5x = _peer_raw_metrics(symbol="PEER5/USDT", volume_quote=40_000.0, liquidity_score=0.9)
        peer_15x = _peer_raw_metrics(symbol="PEER15/USDT", volume_quote=150_000.0, liquidity_score=0.8)
        peers, tier, _criteria = token_analysis.select_peer_symbols_with_fallback(
            target,
            [target, peer_5x, peer_15x],
            _peer_selection_settings(peer_count=2),
        )
        assert {peer.symbol for peer in peers} == {"PEER5/USDT", "PEER15/USDT"}
        assert tier == "volume_20x"

    def test_closest_market_cap_fallback(self):
        target = _peer_raw_metrics(
            symbol="TARGET/USDT",
            volume_quote=10_000.0,
            liquidity_score=0.2,
        )
        near_cap_peer = _peer_raw_metrics(
            symbol="NEAR/USDT",
            volume_quote=9_000_000.0,
            liquidity_score=0.7,
        )
        far_cap_peer = _peer_raw_metrics(
            symbol="FAR/USDT",
            volume_quote=8_000_000.0,
            liquidity_score=0.9,
        )
        market_cap_by_symbol = {
            "TARGET/USDT": 1_000_000.0,
            "NEAR/USDT": 2_000_000.0,
            "FAR/USDT": 1_000_000_000.0,
        }
        peers, tier, _criteria = token_analysis.select_peer_symbols_with_fallback(
            target,
            [target, near_cap_peer, far_cap_peer],
            _peer_selection_settings(),
            market_cap_by_symbol,
        )
        assert peers[0].symbol == "NEAR/USDT"
        assert tier == "marketcap_closest"

    def test_unknown_market_cap_uses_micro_bucket_pool(self):
        target = _peer_raw_metrics(
            symbol="TARGET/USDT",
            volume_quote=None,
            bid_volume_quote=10.0,
            ask_volume_quote=10.0,
            liquidity_score=0.2,
        )
        unknown_peer = _peer_raw_metrics(
            symbol="UNKNOWN/USDT",
            volume_quote=None,
            bid_volume_quote=5.0,
            ask_volume_quote=5.0,
            liquidity_score=0.6,
        )
        market_cap_by_symbol = {
            "TARGET/USDT": None,
            "UNKNOWN/USDT": None,
        }
        peers, tier, _criteria = token_analysis.select_peer_symbols_with_fallback(
            target,
            [target, unknown_peer],
            _peer_selection_settings(),
            market_cap_by_symbol,
        )
        assert peers[0].symbol == "UNKNOWN/USDT"
        assert tier == "volume_micro_bucket"

    def test_last_resort_uses_liquidity_score(self):
        target = _peer_raw_metrics(symbol="TARGET/USDT", volume_quote=10_000.0)
        best_peer = _peer_raw_metrics(symbol="BEST/USDT", volume_quote=9_000_000.0, liquidity_score=0.99)
        peers, tier, _criteria = token_analysis.select_peer_symbols_with_fallback(
            target,
            [target, best_peer],
            _peer_selection_settings(),
        )
        assert peers[0].symbol == "BEST/USDT"
        assert tier == "liquidity_score"

    def test_no_same_quote_peers_returns_none_tier(self):
        target = _peer_raw_metrics(symbol="ONLY/USDT")
        peers, tier, criteria = token_analysis.select_peer_symbols_with_fallback(
            target,
            [target],
            _peer_selection_settings(),
        )
        assert peers == []
        assert tier == "none"
        assert criteria == token_analysis.PEER_TIER_CRITERIA["none"]

    def test_excludes_self_and_wrong_quote(self):
        target = _peer_raw_metrics(symbol="AAA/USDT", volume_quote=10_000.0)
        usdt_peer = _peer_raw_metrics(symbol="BBB/USDT", volume_quote=12_000.0, liquidity_score=0.9)
        btc_peer = _peer_raw_metrics(symbol="CCC/BTC", volume_quote=12_000.0, liquidity_score=0.95)
        peers, _tier, _criteria = token_analysis.select_peer_symbols_with_fallback(
            target,
            [target, usdt_peer, btc_peer],
            _peer_selection_settings(),
        )
        assert len(peers) == 1
        assert peers[0].symbol == "BBB/USDT"


class TestBuildPeerMedianEmpty:
    def test_returns_none_without_peer_rows(self):
        yours_row = token_analysis.peer_row_from_raw(_peer_raw_metrics(), is_yours=True)
        assert token_analysis.build_peer_median([yours_row]) is None


class TestBuildImprovementsNoPeers:
    def test_uses_em_dash_potential_when_peer_median_missing(self):
        raw_metrics = _peer_raw_metrics(spread_pct=66.7, depth_2pct_quote=0.0)
        improvements = token_analysis.build_improvements(raw_metrics, None)
        assert improvements[0]["potential"] == "—"
        assert improvements[1]["potential"] == "—"


class TestBuildPairAnalysisPeerFallback:
    def test_includes_peer_tier_metadata_and_non_zero_median_for_proxy_volume(self):
        target = _peer_raw_metrics(
            symbol="ULX/USDT",
            volume_quote=None,
            bid_volume_quote=1_790_254.0,
            ask_volume_quote=427_383.0,
            spread_pct=66.7,
            depth_2pct_quote=0.0,
            liquidity_score=0.15,
            is_low_health=True,
            health_label_primary="wide_spread",
        )
        peer = _peer_raw_metrics(
            symbol="PEER/USDT",
            volume_quote=2_000_000.0,
            spread_pct=1.0,
            depth_2pct_quote=5_000.0,
            liquidity_score=0.8,
        )
        exchange_averages = {
            "exchange_avg_spread_pct": 0.82,
            "exchange_avg_depth_2pct": 5_400.0,
            "exchange_avg_slippage_10k": 2.28,
            "exchange_median_volume_depth_ratio": 60.0,
        }
        payload = token_analysis.build_pair_analysis(
            target,
            [target, peer],
            exchange_averages,
            health_label_fixtures.default_health_labels(),
            peer_selection_settings=_peer_selection_settings(),
        )
        peers_block = payload["analysis"]["peers"]
        assert peers_block["tier"] == "volume_5x"
        assert peers_block["median"] is not None
        assert peers_block["median"]["depth"] == 5_000.0
        assert len([row for row in peers_block["rows"] if not row["is_yours"] and row["name"] != "Median"]) == 1
        assert payload["analysis"]["score_breakdown"]["peer_relative_100"] is not None
