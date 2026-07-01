import logging

_LOGGER = logging.getLogger(__name__)


def enrichment_progress_log_interval(total_listings: int) -> int:
    if total_listings <= 10:
        return 1
    return max(10, total_listings // 20)


def format_enrichment_progress(completed: int, total: int) -> str:
    percentage = round(100 * completed / total) if total else 100
    return f"{completed}/{total} ({percentage}%)"


def maybe_log_enrichment_progress(label: str, completed: int, total: int) -> None:
    interval = enrichment_progress_log_interval(total)
    if completed == 1 or completed == total or completed % interval == 0:
        _LOGGER.info(
            "%s enrichment progress: %s",
            label,
            format_enrichment_progress(completed, total),
        )
