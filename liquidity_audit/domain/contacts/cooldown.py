import datetime


def parse_contacted_at(contacted_at: str) -> datetime.datetime:
    parsed = datetime.datetime.fromisoformat(contacted_at)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=datetime.UTC)
    return parsed.astimezone(datetime.UTC)


def is_within_cooldown(
    contacted_at: str,
    cooldown_days: int,
    now: datetime.datetime | None = None,
) -> bool:
    if now is None:
        now = datetime.datetime.now(datetime.UTC)
    contacted_time = parse_contacted_at(contacted_at)
    elapsed = now - contacted_time
    return elapsed < datetime.timedelta(days=cooldown_days)
