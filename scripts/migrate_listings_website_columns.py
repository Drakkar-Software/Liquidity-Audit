#!/usr/bin/env python3
"""Add website resolution columns to listings.csv if missing."""

import argparse
import csv
import pathlib
import sys

WEBSITE_COLUMNS = [
    "website",
    "coingecko_id",
    "website_resolution_status",
    "coingecko_candidates_json",
]


def migrate_listings_csv(listings_path: pathlib.Path) -> None:
    if not listings_path.is_file():
        print(f"Listings file not found: {listings_path}", file=sys.stderr)
        sys.exit(1)

    with listings_path.open(encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            print("Listings CSV has no header", file=sys.stderr)
            sys.exit(1)
        fieldnames = list(reader.fieldnames)
        rows = list(reader)

    missing_columns = [column for column in WEBSITE_COLUMNS if column not in fieldnames]
    if not missing_columns:
        print(f"No migration needed for {listings_path}")
        return

    for column in missing_columns:
        fieldnames.append(column)
    for row in rows:
        for column in missing_columns:
            row[column] = ""

    with listings_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Added columns {missing_columns} to {listings_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate listings.csv website columns")
    parser.add_argument(
        "--listings-csv",
        default="data/listings.csv",
        help="Path to listings.csv",
    )
    args = parser.parse_args()
    migrate_listings_csv(pathlib.Path(args.listings_csv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
