import asyncio
from datetime import datetime, timezone, timedelta

# In-memory storage for timers (reset on restart)
# A more robust solution could use Redis or JSON if persistence is needed
_user_timers = {}

def start_guess_timer(user_id: str, seconds: int = 30):
    """Start or reset the countdown timer for a user."""
    _user_timers[user_id] = {
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=seconds),
        "seconds": seconds
    }

def cancel_guess_timer(user_id: str):
    """Cancel timer if guess succeeded or user failed early."""
    _user_timers.pop(user_id, None)

def has_timer_expired(user_id: str) -> bool:
    """Check if the timer has expired for a user."""
    info = _user_timers.get(user_id)
    if not info:
        return True  # No timer = treat as expired
    return datetime.now(timezone.utc) >= info["expires_at"]

def get_time_left(user_id: str) -> int:
    """Return seconds remaining, or 0 if expired."""
    info = _user_timers.get(user_id)
    if not info:
        return 0
    delta = (info["expires_at"] - datetime.now(timezone.utc)).total_seconds()
    return max(0, int(delta))
