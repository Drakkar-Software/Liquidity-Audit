import json
import pathlib

import liquidity_audit.domain.models as models
import cli as liquidity_audit_cli


class TestCliRunNotifications:
    def test_run_posts_mattermost_when_daily_run_returns_result(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        config_path = tmp_path / "config.json"
        config_path.write_text("{}", encoding="utf-8")
        loaded_config = liquidity_audit_cli.app_config.load_config(
            pathlib.Path(__file__).resolve().parents[2] / "config.example.json",
        )
        notification_calls: list[tuple[object, object, bool]] = []

        def fake_load_config(path):
            return loaded_config

        async def fake_daily_run(config, identify_only=False):
            return models.DailyRunResult(
                run_summary=models.RunSummary(
                    new_listings_total=1,
                    new_low_health_count=0,
                    selections_proposed_total=1,
                    selections_proposed_new=1,
                    selections_proposed_existing=0,
                    failed_enrichments_count=0,
                ),
                daily_selections=[],
                new_listings=[],
                failed_enrichments=[],
            )

        async def fake_send_run_notifications(run_summary, daily_selections, post=True):
            notification_calls.append((run_summary, daily_selections, post))

        monkeypatch.setattr(liquidity_audit_cli.app_config, "load_config", fake_load_config)
        monkeypatch.setattr(liquidity_audit_cli.daily_run_workflow, "run", fake_daily_run)
        monkeypatch.setattr(
            liquidity_audit_cli.mattermost_notifier,
            "send_run_notifications",
            fake_send_run_notifications,
        )

        exit_code = liquidity_audit_cli.main([
            "--config",
            str(config_path),
            "run",
        ])

        assert exit_code == 0
        assert len(notification_calls) == 1
        assert notification_calls[0][2] is True

    def test_run_skips_mattermost_on_identify_only(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        config_path = tmp_path / "config.json"
        config_path.write_text("{}", encoding="utf-8")
        loaded_config = liquidity_audit_cli.app_config.load_config(
            pathlib.Path(__file__).resolve().parents[2] / "config.example.json",
        )
        notification_called = False

        def fake_load_config(path):
            return loaded_config

        async def fake_daily_run(config, identify_only=False):
            return None

        async def fake_send_run_notifications(run_summary, daily_selections, post=True):
            nonlocal notification_called
            notification_called = True

        monkeypatch.setattr(liquidity_audit_cli.app_config, "load_config", fake_load_config)
        monkeypatch.setattr(liquidity_audit_cli.daily_run_workflow, "run", fake_daily_run)
        monkeypatch.setattr(
            liquidity_audit_cli.mattermost_notifier,
            "send_run_notifications",
            fake_send_run_notifications,
        )

        exit_code = liquidity_audit_cli.main([
            "--config",
            str(config_path),
            "run",
            "--identify-only",
        ])

        assert exit_code == 0
        assert notification_called is False


class TestCliUpdateWebsites:
    def test_update_websites_runs_resolve_workflow(
        self,
        tmp_path: pathlib.Path,
        monkeypatch,
    ):
        config_path = tmp_path / "config.json"
        config_path.write_text("{}", encoding="utf-8")
        loaded_config = liquidity_audit_cli.app_config.load_config(
            pathlib.Path(__file__).resolve().parents[2] / "config.example.json",
        )
        captured: dict[str, object] = {}

        def fake_load_config(path):
            return loaded_config

        async def fake_update_websites(config):
            captured["config"] = config
            return 3

        monkeypatch.setattr(liquidity_audit_cli.app_config, "load_config", fake_load_config)
        monkeypatch.setattr(
            liquidity_audit_cli.resolve_websites_workflow,
            "run",
            fake_update_websites,
        )

        exit_code = liquidity_audit_cli.main([
            "--config",
            str(config_path),
            "update-websites",
        ])

        assert exit_code == 0
        assert captured["config"] is loaded_config
