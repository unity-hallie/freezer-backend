import json
from typing import List, Optional

KEYWORD_EMOJI = [
    # meats
    ("chicken", "🍗"), ("beef", "🥩"), ("steak", "🥩"), ("pork", "🥓"), ("meatball", "🍝"),
    # dairy
    ("yogurt", "🥛"), ("milk", "🥛"), ("cheese", "🧀"), ("butter", "🧈"),
    # bakery / carbs
    ("bread", "🍞"), ("pizza", "🍕"), ("toast", "🍞"), ("roll", "🥐"), ("pasta", "🍝"), ("rice", "🍚"),
    # produce
    ("vegetable", "🥦"), ("veggie", "🥦"), ("broccoli", "🥦"), ("carrot", "🥕"), ("apple", "🍎"), ("banana", "🍌"),
    # frozen
    ("frozen", "❄️"), ("ice cream", "🍨"),
    # beverages
    ("beer", "🍺"), ("wine", "🍷"), ("soda", "🥤"),
    # leftovers
    ("leftover", "📦"),
]

def parse_tags(raw_tags: Optional[str]) -> List[str]:
    if not raw_tags:
        return []
    try:
        v = json.loads(raw_tags)
        if isinstance(v, list):
            return [str(x).lower() for x in v]
    except Exception:
        pass
    # fallback simple comma/space split
    parts = [p.strip().lower() for p in str(raw_tags).replace("["," ").replace("]"," ").split(",")]
    return [p for p in parts if p]

def suggest_emoji(name: Optional[str], tags: Optional[str]) -> Optional[str]:
    nm = (name or "").lower()
    tag_list = parse_tags(tags)
    # prefer explicit matches in name or tags
    for key, emo in KEYWORD_EMOJI:
        if key in nm:
            return emo
        if any(key in t for t in tag_list):
            return emo
    return None

