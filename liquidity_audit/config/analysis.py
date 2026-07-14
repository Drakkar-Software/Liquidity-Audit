import dataclasses

import liquidity_audit.config._validators as config_validators

DEFAULT_MIN_RELEVANT_USDT_VOLUME = 100.0
DEFAULT_PEER_VOLUME_TIER_RATIOS = (5.0, 20.0, 100.0)


@dataclasses.dataclass
class AnalysisConfig:
    output_dir: str
    rankings_min_volume_quote: float
    checkpoint_every_n_pairs: int
    delisted_retention_days: int
    min_relevant_usdt_volume: float = DEFAULT_MIN_RELEVANT_USDT_VOLUME
    peer_volume_tier_ratios: tuple[float, ...] = DEFAULT_PEER_VOLUME_TIER_RATIOS


def _load_peer_volume_tier_ratios(analysis_raw: dict) -> tuple[float, ...]:
    raw_ratios = analysis_raw.get("peer_volume_tier_ratios", list(DEFAULT_PEER_VOLUME_TIER_RATIOS))
    if not isinstance(raw_ratios, list) or not raw_ratios:
        raise config_validators.ConfigError(
            "config key analysis.peer_volume_tier_ratios must be a non-empty list of numbers",
        )
    ratios: list[float] = []
    for index, ratio in enumerate(raw_ratios):
        if not isinstance(ratio, (int, float)) or ratio <= 0:
            raise config_validators.ConfigError(
                f"config key analysis.peer_volume_tier_ratios[{index}] must be a positive number",
            )
        ratios.append(float(ratio))
    return tuple(ratios)


def load_analysis_config(analysis_raw: dict | None) -> AnalysisConfig:
    if analysis_raw is None:
        return AnalysisConfig(
            output_dir="data/analysis",
            rankings_min_volume_quote=1000.0,
            checkpoint_every_n_pairs=50,
            delisted_retention_days=30,
        )
    if not isinstance(analysis_raw, dict):
        raise config_validators.ConfigError("config key 'analysis' must be an object")
    checkpoint_every_n_pairs = config_validators.require_positive_int(
        analysis_raw, "checkpoint_every_n_pairs",
    )
    delisted_retention_days = analysis_raw.get("delisted_retention_days", 30)
    if not isinstance(delisted_retention_days, int) or delisted_retention_days <= 0:
        raise config_validators.ConfigError("config key analysis.delisted_retention_days must be a positive integer")
    min_relevant_usdt_volume = analysis_raw.get(
        "min_relevant_usdt_volume",
        DEFAULT_MIN_RELEVANT_USDT_VOLUME,
    )
    if not isinstance(min_relevant_usdt_volume, (int, float)) or min_relevant_usdt_volume < 0:
        raise config_validators.ConfigError(
            "config key analysis.min_relevant_usdt_volume must be a non-negative number",
        )
    return AnalysisConfig(
        output_dir=config_validators.require_string(analysis_raw, "output_dir"),
        rankings_min_volume_quote=config_validators.require_non_negative_float(
            analysis_raw, "rankings_min_volume_quote",
        ),
        checkpoint_every_n_pairs=checkpoint_every_n_pairs,
        delisted_retention_days=delisted_retention_days,
        min_relevant_usdt_volume=float(min_relevant_usdt_volume),
        peer_volume_tier_ratios=_load_peer_volume_tier_ratios(analysis_raw),
    )
