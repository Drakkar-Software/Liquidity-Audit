import json
import logging
import os
import pathlib
import typing

import liquidity_audit.domain.analysis.pair_analysis as token_analysis

_LOGGER = logging.getLogger(__name__)


def _atomic_write_json(target_path: pathlib.Path, payload: dict[str, typing.Any]) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = target_path.with_suffix(target_path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as json_file:
        json.dump(payload, json_file, indent=2)
        json_file.write("\n")
        json_file.flush()
        os.fsync(json_file.fileno())
    temporary_path.replace(target_path)


class AnalysisStore:
    def __init__(self, output_dir: str | pathlib.Path) -> None:
        self.output_dir = pathlib.Path(output_dir)

    def pair_json_path(self, exchange: str, symbol: str) -> pathlib.Path:
        symbol_slug = token_analysis.symbol_to_slug(symbol)
        return self.output_dir / "pairs" / exchange / f"{symbol_slug}.json"

    def pair_json_relative_path(self, exchange: str, symbol: str) -> str:
        return str(self.pair_json_path(exchange, symbol).relative_to(self.output_dir)).replace("\\", "/")

    def rankings_json_path(self, exchange: str) -> pathlib.Path:
        return self.output_dir / "rankings" / f"{exchange}.json"

    def manifest_json_path(self) -> pathlib.Path:
        return self.output_dir / "manifest.json"

    def save_pair_analysis(self, exchange: str, symbol: str, pair_analysis: dict[str, typing.Any]) -> None:
        target_path = self.pair_json_path(exchange, symbol)
        _atomic_write_json(target_path, pair_analysis)
        _LOGGER.debug("Wrote pair analysis to %s", target_path)

    def load_pair_analysis(self, exchange: str, symbol: str) -> typing.Optional[dict[str, typing.Any]]:
        target_path = self.pair_json_path(exchange, symbol)
        if not target_path.is_file():
            return None
        with target_path.open(encoding="utf-8") as json_file:
            return json.load(json_file)

    def save_exchange_rankings(self, exchange: str, rankings_payload: dict[str, typing.Any]) -> None:
        target_path = self.rankings_json_path(exchange)
        _atomic_write_json(target_path, rankings_payload)
        _LOGGER.info("Wrote rankings for %s to %s", exchange, target_path)

    def save_manifest(self, manifest_payload: dict[str, typing.Any]) -> None:
        _atomic_write_json(self.manifest_json_path(), manifest_payload)
        _LOGGER.info("Wrote analysis manifest to %s", self.manifest_json_path())

    def delete_pair_analysis(self, exchange: str, symbol: str) -> bool:
        target_path = self.pair_json_path(exchange, symbol)
        if not target_path.is_file():
            return False
        target_path.unlink()
        _LOGGER.info("Deleted expired delisted analysis at %s", target_path)
        return True
