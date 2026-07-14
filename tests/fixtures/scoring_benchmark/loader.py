"""Load scoring benchmark anchor fixtures and build per-exchange universes."""

import json
import pathlib
import typing

import liquidity_audit.config as app_config
import liquidity_audit.domain.analysis.pair_analysis as pair_analysis

_FIXTURE_DIR = pathlib.Path(__file__).resolve().parent
_CONFIG_PATH = _FIXTURE_DIR.parents[2] / "config.example.json"


def fixture_dir() -> pathlib.Path:
    return _FIXTURE_DIR


def load_manifest() -> dict[str, typing.Any]:
    return json.loads((_FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))


def load_expected() -> dict[str, dict[str, typing.Any]]:
    return json.loads((_FIXTURE_DIR / "expected.json").read_text(encoding="utf-8"))


def _pair_fixture_path(exchange: str, symbol: str) -> pathlib.Path:
    slug = pair_analysis.symbol_to_slug(symbol)
    return _FIXTURE_DIR / "pairs" / f"{exchange}_{slug}.json"


def load_anchor_raw_metrics() -> dict[str, pair_analysis.ExtendedRawMetrics]:
    anchors: dict[str, pair_analysis.ExtendedRawMetrics] = {}
    for anchor in load_manifest()["anchors"]:
        exchange, symbol = anchor["key"].split("|", 1)
        pair_payload = json.loads(_pair_fixture_path(exchange, symbol).read_text(encoding="utf-8"))
        raw_metrics = pair_analysis.ExtendedRawMetrics(**pair_payload["raw"])
        anchors[anchor["key"]] = raw_metrics
    return anchors


def build_exchange_universes(
    anchors: dict[str, pair_analysis.ExtendedRawMetrics],
) -> dict[str, list[pair_analysis.ExtendedRawMetrics]]:
    universes: dict[str, list[pair_analysis.ExtendedRawMetrics]] = {}
    for raw_metrics in anchors.values():
        universes.setdefault(raw_metrics.exchange, []).append(raw_metrics)
    return universes


def load_app_config() -> app_config.AppConfig:
    return app_config.load_config(_CONFIG_PATH)


def compute_exchange_averages_for_universe(
    universe: list[pair_analysis.ExtendedRawMetrics],
    config: app_config.AppConfig,
) -> dict[str, typing.Optional[float]]:
    return pair_analysis.compute_exchange_averages(
        universe,
        config.analysis.rankings_min_volume_quote,
    )


def build_anchor_analysis(
    key: str,
    anchors: dict[str, pair_analysis.ExtendedRawMetrics],
    universes: dict[str, list[pair_analysis.ExtendedRawMetrics]],
    exchange_averages_by_exchange: dict[str, dict[str, typing.Optional[float]]],
    health_labels: app_config.HealthLabelsConfig,
    *,
    config: typing.Optional[app_config.AppConfig] = None,
) -> dict[str, typing.Any]:
    raw_metrics = anchors[key]
    exchange_averages = exchange_averages_by_exchange[raw_metrics.exchange]
    peer_selection_settings = None
    if config is not None:
        peer_selection_settings = pair_analysis.peer_selection_settings_from_analysis_config(
            config.analysis,
        )
    return pair_analysis.build_pair_analysis(
        raw_metrics,
        universes[raw_metrics.exchange],
        exchange_averages,
        health_labels,
        peer_selection_settings=peer_selection_settings,
    )


def golden_fields_from_analysis(analysis_payload: dict[str, typing.Any]) -> dict[str, typing.Any]:
    analysis = analysis_payload["analysis"]
    issues = analysis["issues"]
    health_dashboard = analysis["health_dashboard"]
    raw_metrics = pair_analysis.ExtendedRawMetrics(**analysis_payload["raw"])
    breakdown = analysis["score_breakdown"]
    return {
        "score_100": analysis["score_100"],
        "internal_100": breakdown["internal_100"],
        "peer_relative_100": breakdown["peer_relative_100"],
        "grade": analysis["grade"],
        "status": analysis["status"],
        "qualifies_perfect": pair_analysis.qualifies_for_perfect_score(
            raw_metrics,
            issues,
            health_dashboard,
        ),
        "is_low_health": raw_metrics.is_low_health,
    }
