"""
ML-based complaint and suggestion categorizer.

Uses TF-IDF cosine similarity against labelled category seed sentences.
No training data needed – works zero-shot via keyword-rich prototypes.
Falls back to keyword scoring if sklearn is not installed.
"""

import re

# ─── Category seed sentences ─────────────────────────────────────────────────
# Each entry = (category_key, [representative sentences])

CATEGORY_SEEDS = {
    "electrical": [
        "light not working fan not working switch broken electric shock",
        "power cut electricity problem socket not working bulb fused",
        "wiring short circuit MCB tripped tube light flickering",
        "electrical fault voltage fluctuation generator issue inverter",
    ],
    "plumbing": [
        "water leaking pipe burst tap dripping no water supply",
        "bathroom blocked drain clogged toilet overflow sink problem",
        "water pressure low hot water not coming flush not working",
        "water tank empty overhead tank leakage washroom wet floor",
    ],
    "carpentry": [
        "door not closing window broken hinge loose lock stuck",
        "furniture damaged table broken chair broken cupboard shelf",
        "bed broken wardrobe door handle missing almirah",
        "wooden frame damaged desk rack bookshelf broken",
    ],
    "cleaning": [
        "room dirty not cleaned garbage waste not collected",
        "cockroach mosquito pest rat insects hygiene bathroom dirty",
        "dustbin full sweeping not done mopping not done",
        "washroom unclean foul smell toilet dirty corridor dirty",
    ],
    "network": [
        "wifi not working internet slow no signal connection problem",
        "network down broadband disconnected router issue hotspot",
        "internet speed very slow no internet access in room",
        "wifi password WiFi dropout connectivity issue Ethernet",
    ],
    "food": [
        "food quality bad taste not good food not fresh undercooked",
        "mess food portion less food cold not served properly",
        "dining hall canteen menu change food suggestion breakfast lunch dinner",
        "food expired unhygienic stale diet nutrition meal",
    ],
    "safety": [
        "theft stolen lost item security guard absent cctv not working",
        "gate open after hours visitor unauthorized entry unsafe",
        "fire extinguisher emergency exit safety lock main gate",
        "accident injury first aid medicine emergency",
    ],
    "general": [
        "general feedback other issue request suggestion meeting schedule timing",
        "meeting time schedule timetable before 9 morning evening study hours",
        "rules regulations hostel timing curfew permission visiting hours",
        "administrative notice announcement event activity program",
        "study quiet hours lights off common room recreation",
        "warden staff communication request feedback improvement service",
        "hostel management request change policy procedure general",
    ],
}

# ─── Type detection ───────────────────────────────────────────────────────────
SUGGESTION_KEYWORDS = [
    "suggest", "suggestion", "recommend", "idea", "improve", "enhancement",
    "request", "would be good", "please add", "should have", "if possible",
    "consider", "propose", "it would be better", "why not", "can you",
    "please provide", "upgrade", "update", "change", "add",
]

COMPLAINT_KEYWORDS = [
    "broken", "not working", "damaged", "problem", "issue", "complaint",
    "bad", "dirty", "smell", "failed", "didn't", "doesn't", "no water",
    "no light", "request repair", "fix", "repair", "replace", "leak",
    "stuck", "blocked", "pain", "hurt", "trouble", "urgent", "immediately",
]


def _cosine_sim_sklearn(text: str, prototype: str) -> float:
    """TF-IDF cosine similarity between text and a prototype string."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vect = TfidfVectorizer().fit_transform([text, prototype])
    return cosine_similarity(vect[0], vect[1])[0][0]


def _keyword_score(text: str, keywords: list) -> int:
    """Simple keyword hit count."""
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def detect_type(message: str) -> str:
    """Returns 'suggestion' or 'complaint'."""
    msg = message.lower()
    sug_score = _keyword_score(msg, SUGGESTION_KEYWORDS)
    cmp_score  = _keyword_score(msg, COMPLAINT_KEYWORDS)
    return "suggestion" if sug_score > cmp_score else "complaint"


MIN_CONFIDENCE = 0.07  # Below this threshold → classify as 'general'

def detect_category(message: str) -> str:
    """
    Returns the best matching category key from CATEGORY_SEEDS.
    Tries sklearn TF-IDF cosine similarity first, falls back to keyword count.
    If confidence is too low, returns 'general'.
    """
    msg_clean = re.sub(r'[^\w\s]', ' ', message.lower())

    try:
        best_cat = "general"
        best_score = 0.0
        for cat, seeds in CATEGORY_SEEDS.items():
            if cat == "general":
                continue  # Evaluate general last as fallback
            prototype = " ".join(seeds)
            score = _cosine_sim_sklearn(msg_clean, prototype)
            if score > best_score:
                best_score = score
                best_cat = cat
        # Fall back to general if no strong match
        if best_score < MIN_CONFIDENCE:
            return "general"
        return best_cat

    except ImportError:
        # Fallback: keyword hit count per category
        best_cat = "general"
        best_score = 0
        cat_keywords = {
            "electrical": ["light","fan","switch","power","electric","socket","bulb","wiring","circuit","voltage","generator"],
            "plumbing":   ["water","pipe","tap","drain","leak","bathroom","toilet","flush","tank","pressure","sink"],
            "carpentry":  ["door","window","furniture","chair","table","bed","cupboard","shelf","hinge","lock","wardrobe","wooden"],
            "cleaning":   ["dirty","clean","garbage","waste","cockroach","mosquito","pest","rat","hygiene","smell","sweep","mop"],
            "network":    ["wifi","internet","network","signal","connection","broadband","router","speed","connectivity"],
            "food":       ["food","meal","mess","breakfast","lunch","dinner","taste","quality","menu","diet","canteen"],
            "safety":     ["theft","stolen","security","guard","cctv","gate","fire","accident","injury","unsafe","emergency"],
        }
        for cat, kws in cat_keywords.items():
            score = _keyword_score(msg_clean, kws)
            if score > best_score:
                best_score = score
                best_cat = cat
        return best_cat


def classify_complaint(message: str) -> dict:
    """
    Returns {'complaint_type': '...', 'category': '...'} for a given message.
    """
    return {
        "complaint_type": detect_type(message),
        "category": detect_category(message),
    }
