import json
import pathlib

import liquidity_audit.infrastructure.analysis_store as analysis_store


class TestAnalysisStorePairJsonPath:
    def test_symbol_slug_replaces_slash(self, tmp_path: pathlib.Path):
        store = analysis_store.AnalysisStore(tmp_path)
        assert store.pair_json_path("mexc", "XYZ/USDT") == (
            tmp_path / "pairs" / "mexc" / "XYZ_USDT.json"
        )


class TestAnalysisStoreSavePairAnalysis:
    def test_writes_json_file(self, tmp_path: pathlib.Path):
        store = analysis_store.AnalysisStore(tmp_path)
        payload = {"symbol": "XYZ/USDT", "analysis": {"score_100": 42}}
        store.save_pair_analysis("mexc", "XYZ/USDT", payload)
        written_path = store.pair_json_path("mexc", "XYZ/USDT")
        assert written_path.is_file()
        with written_path.open(encoding="utf-8") as json_file:
            assert json.load(json_file)["analysis"]["score_100"] == 42


class TestAnalysisStoreSaveExchangeRankings:
    def test_writes_rankings_json(self, tmp_path: pathlib.Path):
        store = analysis_store.AnalysisStore(tmp_path)
        store.save_exchange_rankings("mexc", {
            "exchange": "mexc",
            "updated_at": "2026-06-12T00:00:00+00:00",
            "pairs": [],
        })
        rankings_path = store.rankings_json_path("mexc")
        assert rankings_path.is_file()


class TestAnalysisStoreDeletePairAnalysis:
    def test_deletes_existing_pair_json(self, tmp_path: pathlib.Path):
        store = analysis_store.AnalysisStore(tmp_path)
        store.save_pair_analysis("bitmart", "PITCH/USDT", {"symbol": "PITCH/USDT"})
        pair_path = store.pair_json_path("bitmart", "PITCH/USDT")
        assert pair_path.is_file()
        assert store.delete_pair_analysis("bitmart", "PITCH/USDT") is True
        assert not pair_path.is_file()

    def test_returns_false_when_missing(self, tmp_path: pathlib.Path):
        store = analysis_store.AnalysisStore(tmp_path)
        assert store.delete_pair_analysis("bitmart", "PITCH/USDT") is False
