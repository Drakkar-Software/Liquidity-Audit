import logging
import urllib.parse

import aiohttp
import liquidity_audit.domain.models as models
import liquidity_audit.domain.website.website_resolution as website_resolution
import liquidity_audit.infrastructure.listings_store as listings_store

_LOGGER = logging.getLogger(__name__)

_MATTERMOST_WEBHOOK_ENV_VAR = "MATTERMOST_WEBHOOK_URL"


class MattermostConfigurationError(ValueError):
    pass


def load_mattermost_webhook_url() -> str:
    import os

    webhook_url = os.environ.get(_MATTERMOST_WEBHOOK_ENV_VAR, "").strip()
    if not webhook_url:
        raise MattermostConfigurationError(
            f"Missing required environment variable {_MATTERMOST_WEBHOOK_ENV_VAR}. "
            "Set it in your shell or see Liquidity-Audit/.env.template.",
        )
    return webhook_url


def _format_topic(selection: models.DailyProjectSelection) -> str:
    if selection.is_new_listing:
        return "new listing"
    return "bad health"


def _format_rounded_liquidity_score(score: float | None) -> str:
    if score is None:
        return "unknown"
    rounded_score = round(score, 2)
    formatted_score = f"{rounded_score:.2f}".rstrip("0").rstrip(".")
    return formatted_score


def _website_or_status_text(record: models.ListingRecord) -> str | None:
    if record.website:
        return record.website
    status = record.website_resolution_status
    if status == website_resolution.COINGECKO_NAME_MISMATCH:
        return "CoinGecko mismatch (@domain)"
    if status == website_resolution.COINGECKO_AMBIGUOUS_NAME_MATCH:
        return "CoinGecko ambiguous (@domain)"
    return None


def _format_selected_project_message(selection: models.DailyProjectSelection) -> str:
    record = selection.record
    header_line = f"{record.base} · {record.exchange} · {_format_topic(selection)}"
    health_label = record.health_label_primary or "unknown"
    detail_parts = [
        record.symbol,
        health_label,
        _format_rounded_liquidity_score(record.liquidity_score),
    ]
    website_or_status = _website_or_status_text(record)
    if website_or_status is not None:
        detail_parts.append(website_or_status)
    detail_line = " · ".join(detail_parts)
    return f"{header_line}\n{detail_line}"


def _selection_base(record: models.ListingRecord) -> str:
    if record.base:
        return record.base
    base, _quote = listings_store.parse_base_quote_from_symbol(record.symbol)
    return base


def _website_host_for_whitelist(website: str) -> str | None:
    stripped_website = website.strip()
    if not stripped_website:
        return None
    if "://" not in stripped_website:
        stripped_website = f"https://{stripped_website}"
    parsed = urllib.parse.urlparse(stripped_website)
    host = parsed.netloc.lower()
    if not host and parsed.path:
        host = parsed.path.lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def format_projects_whitelist_arg(
    daily_selections: list[models.DailyProjectSelection],
) -> str:
    project_entries: list[str] = []
    for selection in daily_selections:
        record = selection.record
        exchange = record.exchange.lower()
        base = _selection_base(record).upper()
        website_host = _website_host_for_whitelist(record.website or "")
        if website_host:
            project_entries.append(f"{exchange}:{base}@{website_host}")
        else:
            project_entries.append(f"{exchange}:{base}")
    return ",".join(project_entries)


def _format_daily_selections_section(
    daily_selections: list[models.DailyProjectSelection],
) -> str | None:
    if not daily_selections:
        return None
    section_lines = [
        f"Selections ({len(daily_selections)})",
    ]
    for selection in daily_selections:
        section_lines.append(_format_selected_project_message(selection))
    return "\n\n".join(section_lines)


def _format_enrich_selected_section(
    daily_selections: list[models.DailyProjectSelection],
) -> str | None:
    if not daily_selections:
        return None
    projects_whitelist_arg = format_projects_whitelist_arg(daily_selections)
    return f'--projects-whitelist "{projects_whitelist_arg}"'


def _format_run_summary_message(run_summary: models.RunSummary) -> str:
    return (
        "**Run summary**\n"
        f"- New listings: {run_summary.new_listings_total} "
        f"({run_summary.new_low_health_count} low-health)\n"
        f"- Daily selections proposed: {run_summary.selections_proposed_total} "
        f"({run_summary.selections_proposed_new} new, "
        f"{run_summary.selections_proposed_existing} existing)\n"
        f"- Websites resolved: {run_summary.websites_resolved_count}\n"
        f"- Failed registrations: {run_summary.failed_enrichments_count}"
    )


async def _post_mattermost_message(webhook_url: str, text: str) -> None:
    payload = {"text": text}
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=payload) as response:
            if response.status >= 400:
                response_body = await response.text()
                _LOGGER.error(
                    "Mattermost webhook failed with status %s: %s",
                    response.status,
                    response_body,
                )
                raise RuntimeError(
                    f"Mattermost webhook failed with status {response.status}: {response_body}"
                )


def format_run_notification_text(
    run_summary: models.RunSummary,
    daily_selections: list[models.DailyProjectSelection],
) -> str:
    message_sections: list[str] = []
    selections_section = _format_daily_selections_section(daily_selections)
    if selections_section is not None:
        message_sections.append(selections_section)
    enrich_section = _format_enrich_selected_section(daily_selections)
    if enrich_section is not None:
        message_sections.append(enrich_section)
    return "\n\n".join(message_sections)


async def send_run_notifications(
    run_summary: models.RunSummary,
    daily_selections: list[models.DailyProjectSelection],
    post: bool = True,
) -> None:
    _LOGGER.info("Mattermost run summary:\n%s", _format_run_summary_message(run_summary))
    notification_text = format_run_notification_text(run_summary, daily_selections)
    _LOGGER.info("Mattermost notification payload:\n%s", notification_text)
    if not post:
        _LOGGER.info("Mattermost notification skipped (identify-selected-only)")
        return
    webhook_url = load_mattermost_webhook_url()
    await _post_mattermost_message(webhook_url, notification_text)
