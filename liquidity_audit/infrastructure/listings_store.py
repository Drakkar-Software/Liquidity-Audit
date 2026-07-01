import csv
import logging
import pathlib
import typing

import liquidity_audit.domain.models as models

_LOGGER = logging.getLogger(__name__)


CSV_COLUMNS = [
    "exchange",
    "symbol",
    "full_name",
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
    "is_low_health",
    "health_label_primary",
    "health_labels_other",
    "delisting_risk",
    "first_seen_at",
    "last_checked_at",
    "last_analyzed_at",
    "score_100",
    "spread_pct",
    "depth_2pct_quote",
    "bid_volume_quote",
    "ask_volume_quote",
    "max_fillable_buy_quote",
    "slippage_10k_pct",
    "analysis_json_path",
    "delisted_at",
    "website",
    "coingecko_id",
    "website_resolution_status",
    "coingecko_candidates_json",
]


def _parse_optional_int(value: str) -> typing.Optional[int]:
    if value == "":
        return None
    return int(value)


def _normalize_float_string(value: str) -> str:
    stripped = value.strip()
    if "," in stripped and "." not in stripped:
        return stripped.replace(",", ".")
    return stripped


def _parse_optional_float(value: str) -> typing.Optional[float]:
    if value == "":
        return None
    return float(_normalize_float_string(value))


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def _parse_health_labels_other(value: str) -> list[str]:
    if value == "":
        return []
    return [label for label in value.split(";") if label]


def parse_base_quote_from_symbol(symbol: str) -> tuple[str, str]:
    if "/" not in symbol:
        return "", ""
    base, quote = symbol.split("/", 1)
    return base, quote


def _record_to_row(record: models.ListingRecord) -> dict[str, str]:
    return {
        "exchange": record.exchange,
        "symbol": record.symbol,
        "full_name": record.full_name,
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
        "is_low_health": "true" if record.is_low_health else "false",
        "health_label_primary": record.health_label_primary or "",
        "health_labels_other": (
            "" if not record.health_labels_other else ";".join(record.health_labels_other)
        ),
        "delisting_risk": "" if not record.delisting_risk else ";".join(record.delisting_risk),
        "first_seen_at": record.first_seen_at or "",
        "last_checked_at": record.last_checked_at or "",
        "last_analyzed_at": record.last_analyzed_at or "",
        "score_100": "" if record.score_100 is None else str(record.score_100),
        "spread_pct": "" if record.spread_pct is None else str(record.spread_pct),
        "depth_2pct_quote": "" if record.depth_2pct_quote is None else str(record.depth_2pct_quote),
        "bid_volume_quote": "" if record.bid_volume_quote is None else str(record.bid_volume_quote),
        "ask_volume_quote": "" if record.ask_volume_quote is None else str(record.ask_volume_quote),
        "max_fillable_buy_quote": (
            "" if record.max_fillable_buy_quote is None else str(record.max_fillable_buy_quote)
        ),
        "slippage_10k_pct": "" if record.slippage_10k_pct is None else str(record.slippage_10k_pct),
        "analysis_json_path": record.analysis_json_path or "",
        "delisted_at": record.delisted_at or "",
        "website": record.website or "",
        "coingecko_id": record.coingecko_id or "",
        "website_resolution_status": record.website_resolution_status or "",
        "coingecko_candidates_json": record.coingecko_candidates_json or "",
    }


def _row_to_record(row: dict[str, str]) -> models.ListingRecord:
    symbol = row["symbol"]
    base_from_symbol, quote_from_symbol = parse_base_quote_from_symbol(symbol)
    legacy_base = row.get("base", "").strip()
    legacy_quote = row.get("quote", "").strip()
    return models.ListingRecord(
        exchange=row["exchange"],
        symbol=symbol,
        base=legacy_base or base_from_symbol,
        quote=legacy_quote or quote_from_symbol,
        full_name=row["full_name"],
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
        is_low_health=_parse_bool(row.get("is_low_health", "false")),
        health_label_primary=row.get("health_label_primary") or None,
        health_labels_other=_parse_health_labels_other(row.get("health_labels_other", "")),
        delisting_risk=_parse_health_labels_other(row.get("delisting_risk", "")) or None,
        first_seen_at=row.get("first_seen_at") or None,
        last_checked_at=row.get("last_checked_at") or None,
        last_analyzed_at=row.get("last_analyzed_at") or None,
        score_100=_parse_optional_int(row.get("score_100", "")),
        spread_pct=_parse_optional_float(row.get("spread_pct", "")),
        depth_2pct_quote=_parse_optional_float(row.get("depth_2pct_quote", "")),
        bid_volume_quote=_parse_optional_float(row.get("bid_volume_quote", "")),
        ask_volume_quote=_parse_optional_float(row.get("ask_volume_quote", "")),
        max_fillable_buy_quote=_parse_optional_float(row.get("max_fillable_buy_quote", "")),
        slippage_10k_pct=_parse_optional_float(row.get("slippage_10k_pct", "")),
        analysis_json_path=row.get("analysis_json_path") or None,
        delisted_at=row.get("delisted_at") or None,
        website=row.get("website") or None,
        coingecko_id=row.get("coingecko_id") or None,
        website_resolution_status=row.get("website_resolution_status") or None,
        coingecko_candidates_json=row.get("coingecko_candidates_json") or None,
    )


class ListingsStore:
    def __init__(self, csv_path: str | pathlib.Path) -> None:
        self.csv_path = pathlib.Path(csv_path)

    def load_known_keys(self) -> set[tuple[str, str]]:
        return set(self.load_all().keys())

    def load_all(self) -> dict[tuple[str, str], models.ListingRecord]:
        if not self.csv_path.is_file():
            _LOGGER.info("Listings CSV not found at %s, starting empty", self.csv_path)
            return {}

        records: dict[tuple[str, str], models.ListingRecord] = {}
        with self.csv_path.open(encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                record = _row_to_record(row)
                records[record.key()] = record
        _LOGGER.info("Loaded %s listing(s) from %s", len(records), self.csv_path)
        return records

    def append_or_update(self, records: list[models.ListingRecord]) -> None:
        existing = self.load_all()
        for record in records:
            existing[record.key()] = record

        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with self.csv_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for record in existing.values():
                writer.writerow(_record_to_row(record))
        _LOGGER.info(
            "Saved %s listing(s) to %s (%s updated this run)",
            len(existing),
            self.csv_path,
            len(records),
        )
