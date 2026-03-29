from datetime import datetime, timezone


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def truncate_text(value: str, max_len: int = 240) -> str:
    if len(value) <= max_len:
        return value
    return value[: max_len - 3] + '...'
