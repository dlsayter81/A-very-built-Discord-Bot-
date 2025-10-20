import regex
from Utility.general_utils import load_json, is_expired, JOIN_CODES_FILE

# 🔡 Emoji-to-character maps (global and alias-safe)
letter_map = {
    "🇦": "A", ":regional_indicator_a:": "A",
    "🇧": "B", ":regional_indicator_b:": "B",
    "🇨": "C", ":regional_indicator_c:": "C",
    "🇩": "D", ":regional_indicator_d:": "D",
    "🇪": "E", ":regional_indicator_e:": "E",
    "🇫": "F", ":regional_indicator_f:": "F",
    "🇬": "G", ":regional_indicator_g:": "G",
    "🇭": "H", ":regional_indicator_h:": "H",
    "🇮": "I", ":regional_indicator_i:": "I",
    "🇯": "J", ":regional_indicator_j:": "J",
    "🇰": "K", ":regional_indicator_k:": "K",
    "🇱": "L", ":regional_indicator_l:": "L",
    "🇲": "M", ":regional_indicator_m:": "M",
    "🇳": "N", ":regional_indicator_n:": "N",
    "🇴": "O", ":regional_indicator_o:": "O",
    "🇵": "P", ":regional_indicator_p:": "P",
    "🇶": "Q", ":regional_indicator_q:": "Q",
    "🇷": "R", ":regional_indicator_r:": "R",
    "🇸": "S", ":regional_indicator_s:": "S",
    "🇹": "T", ":regional_indicator_t:": "T",
    "🇺": "U", ":regional_indicator_u:": "U",
    "🇻": "V", ":regional_indicator_v:": "V",
    "🇼": "W", ":regional_indicator_w:": "W",
    "🇽": "X", ":regional_indicator_x:": "X",
    "🇾": "Y", ":regional_indicator_y:": "Y",
    "🇿": "Z", ":regional_indicator_z:": "Z"
}

number_map = {
    "0️⃣": "0", "1️⃣": "1", "2️⃣": "2", "3️⃣": "3", "4️⃣": "4",
    "5️⃣": "5", "6️⃣": "6", "7️⃣": "7", "8️⃣": "8", "9️⃣": "9",
    ":zero:": "0", ":one:": "1", ":two:": "2", ":three:": "3", ":four:": "4",
    ":five:": "5", ":six:": "6", ":seven:": "7", ":eight:": "8", ":nine:": "9"
}

def decode_emoji_sequence(emojis: list[str]) -> str:
    result = ""
    for emoji in emojis:
        if emoji in letter_map:
            result += letter_map[emoji]
        elif emoji in number_map:
            result += number_map[emoji]
        else:
            continue  # Skip invalid emojis
    return result

def extract_emojis(text: str) -> list[str]:
    emoji_pattern = regex.compile(r'\X', flags=regex.UNICODE)
    valid_emojis = set(letter_map.keys()) | set(number_map.keys())
    return [char for char in emoji_pattern.findall(text) if char in valid_emojis]

def validate_emojiized_code(user_id: str, raw_text: str) -> bool:
    emojis = extract_emojis(raw_text)
    decoded = decode_emoji_sequence(emojis)
    data = load_json(JOIN_CODES_FILE, default={})
    entry = data.get(user_id)
    if not entry or is_expired(entry["expires_at"]):
        return False
    return decoded == entry["code"]
