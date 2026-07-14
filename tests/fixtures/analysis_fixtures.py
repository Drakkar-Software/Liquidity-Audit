import liquidity_audit.config as app_config


def default_analysis_config() -> app_config.AnalysisConfig:
    return app_config.AnalysisConfig(
        output_dir="data/analysis",
        rankings_min_volume_quote=1000.0,
        checkpoint_every_n_pairs=50,
        delisted_retention_days=30,
        min_relevant_usdt_volume=100.0,
        peer_volume_tier_ratios=(5.0, 20.0, 100.0),
    )
