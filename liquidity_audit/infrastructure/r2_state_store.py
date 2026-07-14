import dataclasses
import os
import pathlib

import boto3
import botocore.exceptions

_REQUIRED_ENV_VARS = (
    "R2_ENDPOINT",
    "R2_STATE_BUCKET",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
)

_ANALYSIS_REQUIRED_ENV_VARS = (
    "R2_ENDPOINT",
    "R2_ANALYSIS_BUCKET",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
)

_INVALID_OBJECT_KEY_BASENAMES = frozenset({".", ".."})


@dataclasses.dataclass(frozen=True)
class R2Settings:
    endpoint_url: str
    bucket: str
    access_key_id: str
    secret_access_key: str
    region_name: str


class R2ConfigurationError(ValueError):
    pass


def validate_object_key(object_key: str) -> str:
    stripped_object_key = object_key.strip()
    if not stripped_object_key:
        raise ValueError("--download-remote-listings requires a non-empty OBJECT_KEY")
    object_basename = pathlib.Path(stripped_object_key).name
    if not object_basename or object_basename in _INVALID_OBJECT_KEY_BASENAMES:
        raise ValueError(
            f"Invalid R2 object key '{object_key}': basename must be a non-empty filename",
        )
    return stripped_object_key


def load_r2_settings() -> R2Settings:
    return _load_r2_settings_for_bucket("R2_STATE_BUCKET", _REQUIRED_ENV_VARS)


def load_r2_analysis_settings() -> R2Settings:
    return _load_r2_settings_for_bucket("R2_ANALYSIS_BUCKET", _ANALYSIS_REQUIRED_ENV_VARS)


def _load_r2_settings_for_bucket(bucket_env_var: str, required_env_vars: tuple[str, ...]) -> R2Settings:
    missing_env_vars = [
        env_var_name
        for env_var_name in required_env_vars
        if not os.environ.get(env_var_name, "").strip()
    ]
    if missing_env_vars:
        raise R2ConfigurationError(
            "Missing required environment variable(s) for R2: "
            f"{', '.join(missing_env_vars)}. "
            "Set them as in Projects-Finder/.env.template or "
            "Liquidity-Audit/.github/workflows/update-analysis-data.yml.",
        )
    region_name = os.environ.get("AWS_DEFAULT_REGION", "auto").strip() or "auto"
    return R2Settings(
        endpoint_url=os.environ["R2_ENDPOINT"].strip(),
        bucket=os.environ[bucket_env_var].strip(),
        access_key_id=os.environ["AWS_ACCESS_KEY_ID"].strip(),
        secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"].strip(),
        region_name=region_name,
    )


def _download_object_with_settings(
    settings: R2Settings,
    object_key: str,
    destination_path: pathlib.Path,
) -> None:
    validated_key = validate_object_key(object_key)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    client = _s3_client(settings)
    try:
        client.download_file(settings.bucket, validated_key, str(destination_path))
    except botocore.exceptions.ClientError as error:
        error_code = error.response.get("Error", {}).get("Code", "")
        if error_code in {"404", "NoSuchKey", "NotFound"}:
            raise RuntimeError(
                f"R2 object '{validated_key}' not found in bucket '{settings.bucket}' "
                f"(endpoint {settings.endpoint_url})",
            ) from error
        raise RuntimeError(
            f"R2 download failed for s3://{settings.bucket}/{validated_key} "
            f"(endpoint {settings.endpoint_url}): {error_code or error}",
        ) from error


def download_object(object_key: str, destination_path: pathlib.Path) -> None:
    settings = load_r2_settings()
    _download_object_with_settings(settings, object_key, destination_path)


def download_pair_analysis(
    exchange: str,
    symbol: str,
    destination_path: pathlib.Path,
    *,
    object_prefix: str = "pairs",
) -> None:
    import liquidity_audit.domain.analysis.pair_analysis as pair_analysis

    symbol_slug = pair_analysis.symbol_to_slug(symbol)
    object_key = f"{object_prefix}/{exchange.lower()}/{symbol_slug}.json"
    settings = load_r2_analysis_settings()
    _download_object_with_settings(settings, object_key, destination_path)


def upload_object(source_path: pathlib.Path, object_key: str) -> None:
    settings = load_r2_settings()
    if not source_path.is_file():
        raise RuntimeError(
            f"Cannot upload to R2: local file does not exist: {source_path}",
        )
    client = _s3_client(settings)
    try:
        client.upload_file(str(source_path), settings.bucket, object_key)
    except botocore.exceptions.ClientError as error:
        error_code = error.response.get("Error", {}).get("Code", "")
        raise RuntimeError(
            f"R2 upload failed for {source_path} -> "
            f"s3://{settings.bucket}/{object_key} "
            f"(endpoint {settings.endpoint_url}): {error_code or error}",
        ) from error


def _s3_client(settings: R2Settings):
    return boto3.client(
        "s3",
        endpoint_url=settings.endpoint_url,
        region_name=settings.region_name,
        aws_access_key_id=settings.access_key_id,
        aws_secret_access_key=settings.secret_access_key,
    )
