import os

import liquidity_audit.infrastructure.dotenv_loader as dotenv_loader


class TestLoadProjectDotenv:
    def test_loads_env_file_without_overriding_existing_values(
        self,
        tmp_path,
        monkeypatch,
    ):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "R2_STATE_BUCKET=from-dotenv\nAWS_ACCESS_KEY_ID=dotenv-key\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "shell-key")
        monkeypatch.delenv("R2_STATE_BUCKET", raising=False)
        monkeypatch.setattr(dotenv_loader, "_PROJECT_ROOT", tmp_path)

        dotenv_loader.load_project_dotenv()

        assert os.environ["R2_STATE_BUCKET"] == "from-dotenv"
        assert os.environ["AWS_ACCESS_KEY_ID"] == "shell-key"

    def test_missing_env_file_is_ignored(self, tmp_path, monkeypatch):
        monkeypatch.setattr(dotenv_loader, "_PROJECT_ROOT", tmp_path)
        monkeypatch.delenv("R2_STATE_BUCKET", raising=False)

        dotenv_loader.load_project_dotenv()

        assert "R2_STATE_BUCKET" not in os.environ
