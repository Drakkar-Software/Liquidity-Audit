import os

import pytest

import tests.fixtures.scoring_benchmark.loader as scoring_benchmark_loader


def _benchmark_context():
    config = scoring_benchmark_loader.load_app_config()
    anchors = scoring_benchmark_loader.load_anchor_raw_metrics()
    universes = scoring_benchmark_loader.build_exchange_universes(anchors)
    exchange_averages_by_exchange = {
        exchange: scoring_benchmark_loader.compute_exchange_averages_for_universe(
            universe,
            config,
        )
        for exchange, universe in universes.items()
    }
    return config, anchors, universes, exchange_averages_by_exchange


class TestScoringFormulaAnchorGolden:
    @pytest.mark.parametrize(
        "anchor_key",
        list(scoring_benchmark_loader.load_expected().keys()),
    )
    def test_matches_golden_scores(self, anchor_key: str):
        expected_by_key = scoring_benchmark_loader.load_expected()
        config, anchors, universes, exchange_averages_by_exchange = _benchmark_context()
        analysis_payload = scoring_benchmark_loader.build_anchor_analysis(
            anchor_key,
            anchors,
            universes,
            exchange_averages_by_exchange,
            config.health_labels,
            config=config,
        )
        actual = scoring_benchmark_loader.golden_fields_from_analysis(analysis_payload)
        golden = expected_by_key[anchor_key]
        assert actual == golden, (
            f"Golden drift for {anchor_key}: "
            f"expected {golden}, got {actual}"
        )


class TestScoringFormulaAnchorInvariants:
    def test_perfect_qualification_implies_score_100(self):
        expected_by_key = scoring_benchmark_loader.load_expected()
        for anchor_key, golden in expected_by_key.items():
            if golden["qualifies_perfect"]:
                assert golden["score_100"] == 100, anchor_key

    def test_low_health_excludes_perfect_qualification(self):
        expected_by_key = scoring_benchmark_loader.load_expected()
        for anchor_key, golden in expected_by_key.items():
            if golden["is_low_health"]:
                assert golden["qualifies_perfect"] is False, anchor_key

    def test_failed_issue_chips_exclude_perfect_qualification(self):
        config, anchors, universes, exchange_averages_by_exchange = _benchmark_context()
        for anchor_key in anchors:
            analysis_payload = scoring_benchmark_loader.build_anchor_analysis(
                anchor_key,
                anchors,
                universes,
                exchange_averages_by_exchange,
                config.health_labels,
                config=config,
            )
            issues = analysis_payload["analysis"]["issues"]
            golden = scoring_benchmark_loader.load_expected()[anchor_key]
            if any(not issue.get("ok") for issue in issues):
                assert golden["qualifies_perfect"] is False, anchor_key

    def test_non_low_dashboard_severity_excludes_perfect_qualification(self):
        config, anchors, universes, exchange_averages_by_exchange = _benchmark_context()
        for anchor_key in anchors:
            analysis_payload = scoring_benchmark_loader.build_anchor_analysis(
                anchor_key,
                anchors,
                universes,
                exchange_averages_by_exchange,
                config.health_labels,
                config=config,
            )
            health_dashboard = analysis_payload["analysis"]["health_dashboard"]
            golden = scoring_benchmark_loader.load_expected()[anchor_key]
            if any(row.get("severity") != "Low" for row in health_dashboard):
                assert golden["qualifies_perfect"] is False, anchor_key

    def test_scores_stay_within_valid_range(self):
        expected_by_key = scoring_benchmark_loader.load_expected()
        for anchor_key, golden in expected_by_key.items():
            assert 0 <= golden["score_100"] <= 100, anchor_key
            peer_relative_100 = golden["peer_relative_100"]
            if peer_relative_100 is not None:
                assert 0 <= peer_relative_100 <= 100, anchor_key


@pytest.mark.skipif(
    os.environ.get("UPDATE_SCORING_GOLDEN") != "1",
    reason="Set UPDATE_SCORING_GOLDEN=1 to regenerate scoring benchmark golden files",
)
class TestUpdateScoringFormulaGolden:
    def test_regenerates_expected_json(self):
        import scripts.generate_scoring_benchmark_fixtures as generate_scoring_benchmark_fixtures

        expected = generate_scoring_benchmark_fixtures.generate_fixtures()
        loaded = scoring_benchmark_loader.load_expected()
        assert loaded == expected
