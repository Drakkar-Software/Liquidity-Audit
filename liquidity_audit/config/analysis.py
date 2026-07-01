import dataclasses

import liquidity_audit.config._validators as config_validators


@dataclasses.dataclass
class AnalysisConfig:
    output_dir: str
    rankings_min_volume_quote: float
    checkpoint_every_n_pairs: int
    delisted_retention_days: int


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
    return AnalysisConfig(
        output_dir=config_validators.require_string(analysis_raw, "output_dir"),
        rankings_min_volume_quote=config_validators.require_non_negative_float(
            analysis_raw, "rankings_min_volume_quote",
        ),
        checkpoint_every_n_pairs=checkpoint_every_n_pairs,
        delisted_retention_days=delisted_retention_days,
    )
