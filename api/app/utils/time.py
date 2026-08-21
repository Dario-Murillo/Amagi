from datetime import datetime, timezone


def utcnow() -> datetime:
    """Timezone-aware UTC now, used as the default for every `created_at` column."""
    return datetime.now(timezone.utc)
