import liquidity_audit.config as app_config
import liquidity_audit.domain.health.evaluation as health_evaluation
import liquidity_audit.domain.models as models


async def check_listing_health(
    client,
    symbol: str,
    order_book_limit: int,
    health_rules: app_config.HealthRules,
    unhealthy_values: app_config.UnhealthyValues,
    health_labels: app_config.HealthLabelsConfig,
    min_liquidity_score: float,
) -> models.HealthResult:
    order_book = await client.fetch_order_book(symbol, limit=order_book_limit)
    ticker = await client.fetch_ticker(symbol)
    return health_evaluation.evaluate_health(
        order_book,
        ticker,
        health_rules,
        unhealthy_values,
        health_labels,
        min_liquidity_score,
        order_book_limit,
    )
