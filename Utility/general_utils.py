import json
import os
from datetime import datetime, timedelta, timezone

# File paths
FULL_DURATION_FILE = "data/full_duration.json"
TIMEOUT_CODES_FILE = "data/timeout_codes.json"
CLEANUP_FILE = "data/cleanup.json"
GUESS_STATUS_FILE = "data/guess_status.json"
HARDLOCKS_FILE = "data/hardlocks.json"
RANDOM_CODES_FILE = "data/random_timout_codes.json"
PERMANENT_SEALS_FILE = "data/permanent_seals.json"
JOIN_CODES_FILE = "data/join_codes.json"
FAILURE_LOG_FILE = "data/Onboarding_failure.json"




# Ensure the data directory exists
os.makedirs("data", exist_ok=True)

def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def is_expired(timestamp):
    now = int(datetime.now(timezone.utc).timestamp())
    return timestamp < now

def add_minutes(minutes):
    future = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return int(future.timestamp())
