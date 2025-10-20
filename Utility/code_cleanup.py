# code_cleanup.py
import asyncio
from datetime import datetime, timezone
from Utility.general_utils import load_json, save_json, TIMEOUT_CODES_FILE, RANDOM_CODES_FILE

async def cleanup_expired_codes(bot=None):
    while True:
        now_ts = datetime.now(timezone.utc).timestamp()

        for file in [TIMEOUT_CODES_FILE, RANDOM_CODES_FILE]:
            data = load_json(file, default={})
            changed = False
            for user_id, entry in list(data.items()):
                if "expires_at" in entry and entry["expires_at"] < now_ts:
                    data.pop(user_id)
                    changed = True
            if changed:
                save_json(file, data)
        await asyncio.sleep(30)
