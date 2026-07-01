class ConfigError(Exception):
    pass


def require_string(config: dict, key: str) -> str:
    value = config.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"config key {key!r} must be a non-empty string")
    return value


def require_positive_int(config: dict, key: str) -> int:
    value = config.get(key)
    if not isinstance(value, int) or value <= 0:
        raise ConfigError(f"config key {key!r} must be a positive integer")
    return value


def require_positive_float(config: dict, key: str) -> float:
    value = config.get(key)
    if not isinstance(value, (int, float)) or value <= 0:
        raise ConfigError(f"config key {key!r} must be a positive number")
    return float(value)


def require_non_negative_float(config: dict, key: str) -> float:
    value = config.get(key)
    if not isinstance(value, (int, float)) or value < 0:
        raise ConfigError(f"config key {key!r} must be a non-negative number")
    return float(value)
