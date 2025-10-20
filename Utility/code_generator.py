import random
from Utility.general_utils import add_minutes

def generate_code(user_id: str, length=6, expires_in=15) -> dict:
    code = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=length))
    expires_at = add_minutes(expires_in)
    return {
        "user_id": user_id,
        "code": code,
        "expires_at": expires_at
    }
