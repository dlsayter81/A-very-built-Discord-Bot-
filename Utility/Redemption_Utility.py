# redemption_utils.py

import discord
import random
import asyncio
from datetime import datetime, timedelta, timezone

from Utility.general_utils import (
    load_json,
    save_json,
    TIMEOUT_CODES_FILE,
    RANDOM_CODES_FILE,
    HARDLOCKS_FILE,
    PERMANENT_SEALS_FILE
)

# ⏳ Timer utility
from Utility.timer_utils import (
    start_guess_timer,
    cancel_guess_timer,
    has_timer_expired,
    get_time_left
)

# =========================================================
# 🔒 SEAL & UNSEAL LOGIC
# =========================================================

def is_sealed(user_id: str) -> float | str | None:
    now = datetime.now(timezone.utc).timestamp()
    hardlocked = load_json(HARDLOCKS_FILE, default={}).get(user_id)
    if hardlocked and hardlocked.get("hardlock_until", 0) > now:
        return hardlocked["hardlock_until"] - now

    permanent_seals = load_json(PERMANENT_SEALS_FILE, default={})
    if user_id in permanent_seals:
        return "permanent"

    return None

def unseal_user(user_id: str) -> bool:
    hardlocks = load_json(HARDLOCKS_FILE, default={})
    if user_id in hardlocks:
        hardlocks.pop(user_id)
        save_json(HARDLOCKS_FILE, hardlocks)
        return True
    return False

def track_misuse(user_id: str, reason: str):
    data = load_json(HARDLOCKS_FILE, default={})
    entry = data.setdefault(user_id, {})
    entry["misuse_attempts"] = entry.get("misuse_attempts", 0) + 1
    if entry["misuse_attempts"] >= 2:
        entry["hardlock_until"] = datetime.now(timezone.utc).timestamp() + 43200  # 12h
        entry["hardlock_reason"] = reason
    data[user_id] = entry
    save_json(HARDLOCKS_FILE, data)

# =========================================================
# 🔑 REDEMPTION CODE DM HANDLING
# =========================================================

async def store_dm_message(user: discord.User, message: discord.Message, user_id: str, file: str = TIMEOUT_CODES_FILE):
    """Store DM message ID for deletion later."""
    data = load_json(file, default={})
    entry = data.get(user_id)
    if entry:
        entry["dm_message_id"] = message.id
        data[user_id] = entry
        save_json(file, data)

async def delete_dm_message(bot, user_id: str, file: str = TIMEOUT_CODES_FILE):
    """Delete DM message if it exists in storage."""
    data = load_json(file, default={})
    entry = data.get(user_id)
    if entry and "dm_message_id" in entry:
        try:
            user = await bot.fetch_user(int(user_id))
            dm_channel = user.dm_channel or await user.create_dm()
            msg = await dm_channel.fetch_message(entry["dm_message_id"])
            await msg.delete()
        except Exception:
            pass
        # Remove reference
        entry.pop("dm_message_id", None)
        data[user_id] = entry
        save_json(file, data)

# =========================================================
# 🔑 REDEMPTION CODE VALIDATION
# =========================================================

def validate_code(user_id: str, submitted_code: str) -> dict | None:
    if is_sealed(user_id):
        return None

    # Load entry from timeout file
    data = load_json(TIMEOUT_CODES_FILE, default={})
    entry = data.get(user_id)
    source_file = TIMEOUT_CODES_FILE

    if not entry:
        data = load_json(RANDOM_CODES_FILE, default={})
        entry = data.get(user_id)
        source_file = RANDOM_CODES_FILE

    if not entry:
        track_misuse(user_id, "Too many invalid redemption attempts")
        return None

    entry["failed_attempts"] = entry.get("failed_attempts", 0)

    # Expired code
    if "expires_at" in entry and datetime.now(timezone.utc).timestamp() > entry["expires_at"]:
        data.pop(user_id, None)
        save_json(source_file, data)
        return None

    # Wrong code
    if entry.get("code") != submitted_code:
        entry["failed_attempts"] += 1
        track_misuse(user_id, "Too many invalid redemption attempts")
        if entry["failed_attempts"] >= 2:
            data.pop(user_id, None)
        else:
            data[user_id] = entry
        save_json(source_file, data)
        return None

    # Valid code
    entry["failed_attempts"] = 0
    data[user_id] = entry
    save_json(source_file, data)
    return entry

# =========================================================
# 🔓 GUESSING LOGIC
# =========================================================

def unlock_guess(user_id: str, bot: discord.Bot | discord.Client = None) -> bool:
    if is_sealed(user_id):
        return False

    data = load_json(TIMEOUT_CODES_FILE, default={})
    entry = data.get(user_id)
    source_file = TIMEOUT_CODES_FILE

    if not entry:
        data = load_json(RANDOM_CODES_FILE, default={})
        entry = data.get(user_id)
        source_file = RANDOM_CODES_FILE

    if entry:
        entry["can_guess"] = True
        if "secret_number" not in entry:
            entry["secret_number"] = random.randint(1, 100)

        # 🔥 Invalidate code immediately
        entry.pop("code", None)
        entry.pop("expires_at", None)

        data[user_id] = entry
        save_json(source_file, data)

        # ⏳ Start 30 second timer
        start_guess_timer(user_id, 30)

        # Delete DM message if bot reference provided
        if bot:
            asyncio.create_task(delete_dm_message(bot, user_id, source_file))

        return True
    return False

def handle_guess(user_id: str, guess: int, member: discord.Member | None = None) -> dict:
    if is_sealed(user_id):
        track_misuse(user_id, "Guess attempt while sealed")
        return {"error": "You are sealed. Guessing is forbidden."}

    if has_timer_expired(user_id):
        for file in [TIMEOUT_CODES_FILE, RANDOM_CODES_FILE]:
            data = load_json(file, default={})
            if user_id in data:
                data.pop(user_id, None)
                save_json(file, data)
        cancel_guess_timer(user_id)

        if member:
            try:
                asyncio.create_task(member.send("⏳ Time's up! You failed to guess in time."))
            except Exception:
                pass
        return {"error": "⏳ Time's up! You failed to guess in time."}

    data = load_json(TIMEOUT_CODES_FILE, default={})
    entry = data.get(user_id)
    source_file = TIMEOUT_CODES_FILE

    if not entry or not entry.get("can_guess"):
        data = load_json(RANDOM_CODES_FILE, default={})
        entry = data.get(user_id)
        source_file = RANDOM_CODES_FILE

    if not entry or not entry.get("can_guess"):
        track_misuse(user_id, "Unauthorized guess")
        return {"error": "Guessing not unlocked."}

    if entry["attempts_left"] <= 0:
        data.pop(user_id, None)
        save_json(source_file, data)
        cancel_guess_timer(user_id)
        return {"error": "No attempts left."}

    secret = entry["secret_number"]
    delta = abs(guess - secret)
    entry["attempts_left"] -= 1

    if entry["attempts_left"] > 0:
        start_guess_timer(user_id, 30)
    else:
        cancel_guess_timer(user_id)

    # 🎯 Evaluate guess
    if delta <= 10:
        reduction = entry["reduction_percent"]
        result = "full"
        cancel_guess_timer(user_id)  # ⏳ Ritual closure
        data.pop(user_id, None)
    elif entry["attempts_left"] == 0:
        cancel_guess_timer(user_id)  # <— cancel the active timer
        reduction = entry["reduction_percent"] // 2
        result = "half"
        data.pop(user_id, None)
        cancel_guess_timer(user_id)  # <— cancel the active timer
    else:
        data[user_id] = entry
        save_json(source_file, data)
        return {
            "error": None,
            "result": "miss",
            "attempts_left": entry["attempts_left"],
            "time_left": get_time_left(user_id)
        }

    save_json(source_file, data)
    return {
        "error": None,
        "result": result,
        "reduction": reduction,
        "secret": secret
    }

# =========================================================
# ⏳ APPLY TIMEOUT REDUCTION
# =========================================================

async def apply_reduction(member: discord.Member, percent: int) -> str:
    if not member.communication_disabled_until:
        return "User is not currently timed out."

    remaining = (member.communication_disabled_until - discord.utils.utcnow()).total_seconds()
    reduced = int(remaining * (1 - percent / 100))
    new_timeout = discord.utils.utcnow() + timedelta(seconds=reduced)

    try:
        await member.edit(
            communication_disabled_until=new_timeout,
            reason="Mute reduced via redemption"
        )
        return f"Timeout reduced by {percent}%. New duration: {int(reduced)} seconds."
    except discord.Forbidden:
        return "Missing permission to edit member."
    except discord.HTTPException as e:
        return f"Failed to apply timeout: {e}"
