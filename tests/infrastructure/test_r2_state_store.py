import pathlib

import mock
import pytest

import liquidity_audit.infrastructure.r2_state_store as r2_state_store


def _set_r2_env(monkeypatch) -> None:
    monkeypatch.setenv("R2_ENDPOINT", "https://account.r2.cloudflarestorage.com")
    monkeypatch.setenv("R2_STATE_BUCKET", "state-bucket")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "access-key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret-key")


class TestValidateObjectKey:
    def test_rejects_empty_object_key(self):
        with pytest.raises(ValueError, match="non-empty OBJECT_KEY"):
            r2_state_store.validate_object_key("   ")

    def test_rejects_invalid_basename(self):
        with pytest.raises(ValueError, match="Invalid R2 object key"):
            r2_state_store.validate_object_key("..")


class TestLoadR2Settings:
    def test_builds_settings_from_env(self, monkeypatch):
        _set_r2_env(monkeypatch)
        monkeypatch.setenv("AWS_DEFAULT_REGION", "auto")
        settings = r2_state_store.load_r2_settings()
        assert settings.endpoint_url == "https://account.r2.cloudflarestorage.com"
        assert settings.bucket == "state-bucket"
        assert settings.access_key_id == "access-key"
        assert settings.secret_access_key == "secret-key"
        assert settings.region_name == "auto"

    def test_lists_all_missing_env_vars(self, monkeypatch):
        for env_var_name in (
            "R2_ENDPOINT",
            "R2_STATE_BUCKET",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
        ):
            monkeypatch.delenv(env_var_name, raising=False)
        with pytest.raises(r2_state_store.R2ConfigurationError) as error_info:
            r2_state_store.load_r2_settings()
        error_message = str(error_info.value)
        assert "R2_ENDPOINT" in error_message
        assert "R2_STATE_BUCKET" in error_message
        assert "AWS_ACCESS_KEY_ID" in error_message
        assert "AWS_SECRET_ACCESS_KEY" in error_message


class TestDownloadObject:
    def test_downloads_to_destination(self, monkeypatch, tmp_path: pathlib.Path):
        _set_r2_env(monkeypatch)
        fake_client = mock.MagicMock()
        monkeypatch.setattr(r2_state_store.boto3, "client", lambda *args, **kwargs: fake_client)
        destination_path = tmp_path / "remote" / "listings.csv"
        r2_state_store.download_object("listings.csv", destination_path)
        fake_client.download_file.assert_called_once_with(
            "state-bucket",
            "listings.csv",
            str(destination_path),
        )

    def test_raises_explicit_error_for_missing_object(self, monkeypatch, tmp_path: pathlib.Path):
        _set_r2_env(monkeypatch)
        fake_client = mock.MagicMock()
        fake_client.download_file.side_effect = r2_state_store.botocore.exceptions.ClientError(
            {"Error": {"Code": "NoSuchKey", "Message": "missing"}},
            "GetObject",
        )
        monkeypatch.setattr(r2_state_store.boto3, "client", lambda *args, **kwargs: fake_client)
        with pytest.raises(RuntimeError, match="not found in bucket 'state-bucket'"):
            r2_state_store.download_object(
                "listings.csv",
                tmp_path / "remote" / "listings.csv",
            )


class TestUploadObject:
    def test_uploads_existing_file(self, monkeypatch, tmp_path: pathlib.Path):
        _set_r2_env(monkeypatch)
        source_path = tmp_path / "listings.csv"
        source_path.write_text("exchange,symbol\n", encoding="utf-8")
        fake_client = mock.MagicMock()
        monkeypatch.setattr(r2_state_store.boto3, "client", lambda *args, **kwargs: fake_client)
        r2_state_store.upload_object(source_path, "listings.csv")
        fake_client.upload_file.assert_called_once_with(
            str(source_path),
            "state-bucket",
            "listings.csv",
        )

    def test_raises_when_local_file_missing(self, monkeypatch, tmp_path: pathlib.Path):
        _set_r2_env(monkeypatch)
        missing_path = tmp_path / "missing.csv"
        with pytest.raises(RuntimeError, match="local file does not exist"):
            r2_state_store.upload_object(missing_path, "listings.csv")

    def test_raises_explicit_error_on_upload_failure(self, monkeypatch, tmp_path: pathlib.Path):
        _set_r2_env(monkeypatch)
        source_path = tmp_path / "listings.csv"
        source_path.write_text("exchange,symbol\n", encoding="utf-8")
        fake_client = mock.MagicMock()
        fake_client.upload_file.side_effect = r2_state_store.botocore.exceptions.ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "denied"}},
            "PutObject",
        )
        monkeypatch.setattr(r2_state_store.boto3, "client", lambda *args, **kwargs: fake_client)
        with pytest.raises(RuntimeError, match="R2 upload failed"):
            r2_state_store.upload_object(source_path, "listings.csv")
