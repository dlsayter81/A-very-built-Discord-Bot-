from datetime import datetime, timedelta
from typing import Union

def get_lockout_timestamp(duration: Union[int, timedelta] = 15) -> str:
    """Return an ISO timestamp for when the lockout expires."""
    if isinstance(duration, int):
        lockout_time = datetime.utcnow() + timedelta(hours=duration)
    elif isinstance(duration, timedelta):
        lockout_time = datetime.utcnow() + duration
    else:
        raise TypeError(f"Expected int or timedelta, got {type(duration).__name__}")
    return lockout_time.isoformat()

def is_locked_out(locked_until: str) -> bool:
    """Return True if the current time is still before the lockout expiration."""
    return datetime.utcnow() < datetime.fromisoformat(locked_until)

def get_remaining_lockout(locked_until: str) -> tuple[int, int]:
    """Return (hours, minutes) remaining in the lockout period."""
    remaining = datetime.fromisoformat(locked_until) - datetime.utcnow()
    if remaining.total_seconds() < 0:
        return 0, 0
    hours = int(remaining.total_seconds() // 3600)
    minutes = int((remaining.total_seconds() % 3600) // 60)
    return hours, minutes
