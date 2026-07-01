import csv
import datetime
import logging
import pathlib
import typing

import liquidity_audit.domain.select.cooldown as select_cooldown
import liquidity_audit.domain.select.health_issues as select_health_issues
import liquidity_audit.domain.models as models

_LOGGER = logging.getLogger(__name__)


SELECTED_HISTORY_CSV_COLUMNS = [
    "selected_at",
    "exchange",
    "symbol",
    "full_name",
    "is_new_listing",
    "selection_tier",
    "is_low_health",
    "health_label_primary",
    "health_labels_other",
    "issue_count",
    "bid_levels",
    "ask_levels",
    "bid_depth_quote",
    "ask_depth_quote",
    "bid_larger_depth_quote",
    "ask_larger_depth_quote",
    "bid_total_depth_quote",
    "ask_total_depth_quote",
    "volume_quote",
    "bid_ask_spread_ratio",
    "liquidity_score",
    "website",
    "coingecko_id",
    "website_resolution_status",
]


def _parse_optional_int(value: str) -> typing.Optional[int]:
    if value == "":
        return None
    return int(value)


def _parse_optional_float(value: str) -> typing.Optional[float]:
    if value == "":
        return None
    return float(value)


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def _parse_health_labels_other(value: str) -> list[str]:
    if value == "":
        return []
    return [label for label in value.split(";") if label]


def selected_history_record_from_selection(
    selection: models.DailyProjectSelection,
    selected_at: str,
) -> models.SelectedHistoryRecord:
    listing = selection.record
    return models.SelectedHistoryRecord(
        selected_at=selected_at,
        exchange=listing.exchange,
        symbol=listing.symbol,
        full_name=listing.full_name,
        is_new_listing=selection.is_new_listing,
        selection_tier=selection.selection_tier,
        is_low_health=listing.is_low_health,
        health_label_primary=listing.health_label_primary,
        health_labels_other=list(listing.health_labels_other or []),
        issue_count=select_health_issues.count_health_issues(listing),
        bid_levels=listing.bid_levels,
        ask_levels=listing.ask_levels,
        bid_depth_quote=listing.bid_depth_quote,
        ask_depth_quote=listing.ask_depth_quote,
        bid_larger_depth_quote=listing.bid_larger_depth_quote,
        ask_larger_depth_quote=listing.ask_larger_depth_quote,
        bid_total_depth_quote=listing.bid_total_depth_quote,
        ask_total_depth_quote=listing.ask_total_depth_quote,
        volume_quote=listing.volume_quote,
        bid_ask_spread_ratio=listing.bid_ask_spread_ratio,
        liquidity_score=listing.liquidity_score,
        website=listing.website,
        coingecko_id=listing.coingecko_id,
        website_resolution_status=listing.website_resolution_status,
    )


def parse_selected_at(selected_at: str) -> datetime.datetime:
    return select_cooldown.parse_contacted_at(selected_at)


def is_within_cooldown(
    selected_at: str,
    cooldown_days: int,
    now: datetime.datetime | None = None,
) -> bool:
    return select_cooldown.is_within_cooldown(selected_at, cooldown_days, now=now)


def _record_to_row(record: models.SelectedHistoryRecord) -> dict[str, str]:
    return {
        "selected_at": record.selected_at,
        "exchange": record.exchange,
        "symbol": record.symbol,
        "full_name": record.full_name,
        "is_new_listing": "true" if record.is_new_listing else "false",
        "selection_tier": record.selection_tier,
        "is_low_health": "true" if record.is_low_health else "false",
        "health_label_primary": record.health_label_primary or "",
        "health_labels_other": (
            "" if not record.health_labels_other else ";".join(record.health_labels_other)
        ),
        "issue_count": str(record.issue_count),
        "bid_levels": "" if record.bid_levels is None else str(record.bid_levels),
        "ask_levels": "" if record.ask_levels is None else str(record.ask_levels),
        "bid_depth_quote": "" if record.bid_depth_quote is None else str(record.bid_depth_quote),
        "ask_depth_quote": "" if record.ask_depth_quote is None else str(record.ask_depth_quote),
        "bid_larger_depth_quote": (
            "" if record.bid_larger_depth_quote is None else str(record.bid_larger_depth_quote)
        ),
        "ask_larger_depth_quote": (
            "" if record.ask_larger_depth_quote is None else str(record.ask_larger_depth_quote)
        ),
        "bid_total_depth_quote": (
            "" if record.bid_total_depth_quote is None else str(record.bid_total_depth_quote)
        ),
        "ask_total_depth_quote": (
            "" if record.ask_total_depth_quote is None else str(record.ask_total_depth_quote)
        ),
        "volume_quote": "" if record.volume_quote is None else str(record.volume_quote),
        "bid_ask_spread_ratio": (
            "" if record.bid_ask_spread_ratio is None else str(record.bid_ask_spread_ratio)
        ),
        "liquidity_score": "" if record.liquidity_score is None else str(record.liquidity_score),
        "website": record.website or "",
        "coingecko_id": record.coingecko_id or "",
        "website_resolution_status": record.website_resolution_status or "",
    }


def _row_to_record(row: dict[str, str]) -> models.SelectedHistoryRecord:
    selected_at = row.get("selected_at") or row.get("contacted_at", "")
    return models.SelectedHistoryRecord(
        selected_at=selected_at,
        exchange=row["exchange"],
        symbol=row["symbol"],
        full_name=row["full_name"],
        is_new_listing=_parse_bool(row.get("is_new_listing", "false")),
        selection_tier=row["selection_tier"],
        is_low_health=_parse_bool(row.get("is_low_health", "false")),
        health_label_primary=row.get("health_label_primary") or None,
        health_labels_other=_parse_health_labels_other(row.get("health_labels_other", "")),
        issue_count=int(row.get("issue_count", "0")),
        bid_levels=_parse_optional_int(row.get("bid_levels", "")),
        ask_levels=_parse_optional_int(row.get("ask_levels", "")),
        bid_depth_quote=_parse_optional_float(row.get("bid_depth_quote", "")),
        ask_depth_quote=_parse_optional_float(row.get("ask_depth_quote", "")),
        bid_larger_depth_quote=_parse_optional_float(row.get("bid_larger_depth_quote", "")),
        ask_larger_depth_quote=_parse_optional_float(row.get("ask_larger_depth_quote", "")),
        bid_total_depth_quote=_parse_optional_float(row.get("bid_total_depth_quote", "")),
        ask_total_depth_quote=_parse_optional_float(row.get("ask_total_depth_quote", "")),
        volume_quote=_parse_optional_float(row.get("volume_quote", "")),
        bid_ask_spread_ratio=_parse_optional_float(row.get("bid_ask_spread_ratio", "")),
        liquidity_score=_parse_optional_float(row.get("liquidity_score", "")),
        website=row.get("website") or None,
        coingecko_id=row.get("coingecko_id") or None,
        website_resolution_status=row.get("website_resolution_status") or None,
    )


class SelectedHistoryStore:
    def __init__(self, csv_path: str | pathlib.Path) -> None:
        self.csv_path = pathlib.Path(csv_path)

    def load_all(self) -> list[models.SelectedHistoryRecord]:
        if not self.csv_path.is_file():
            _LOGGER.info("Selected history CSV not found at %s, starting empty", self.csv_path)
            return []

        records: list[models.SelectedHistoryRecord] = []
        with self.csv_path.open(encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                records.append(_row_to_record(row))
        _LOGGER.info("Loaded %s selected history row(s) from %s", len(records), self.csv_path)
        return records

    def load_recent_by_key(self) -> dict[tuple[str, str], models.SelectedHistoryRecord]:
        recent_by_key: dict[tuple[str, str], models.SelectedHistoryRecord] = {}
        for record in self.load_all():
            listing_key = record.key()
            existing = recent_by_key.get(listing_key)
            if existing is None or parse_selected_at(record.selected_at) > parse_selected_at(
                existing.selected_at,
            ):
                recent_by_key[listing_key] = record
        return recent_by_key

    def append(self, records: list[models.SelectedHistoryRecord]) -> None:
        if not records:
            return

        write_header = not self.csv_path.is_file()
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("a", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=SELECTED_HISTORY_CSV_COLUMNS)
            if write_header:
                writer.writeheader()
            for record in records:
                writer.writerow(_record_to_row(record))
        _LOGGER.info(
            "Appended %s selected history row(s) to %s",
            len(records),
            self.csv_path,
        )
