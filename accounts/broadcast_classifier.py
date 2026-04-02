"""
Broadcast message classifier.

Categorises a broadcast message into one of:
  general | announcement | urgent | meeting

Uses TF-IDF cosine similarity (sklearn) with keyword-rich seed sentences,
falls back to keyword scoring if sklearn is unavailable.
"""

import re

# ─── Seed sentences ───────────────────────────────────────────────────────────
BROADCAST_SEED = {
    "urgent": [
        "emergency immediately danger warning alert fire drill lockdown",
        "urgent action required critical situation danger threat hazard",
        "fire alarm evacuation medical emergency ambulance police",
        "immediate attention required ASAP right now crisis disaster",
        "power outage water main burst dangerous do not leave hostel",
        "urgent notice compulsory mandatory all students must assemble now",
    ],
    "meeting": [
        "meeting schedule gathering assembly seminar session warden meeting",
        "attend compulsory meeting hall room tomorrow today time venue",
        "parent teacher meeting block meeting warden student meet",
        "discussion agenda session scheduled at hostel conference room",
        "please gather meeting will be held all are requested to attend",
        "hostel committee meeting annual general meeting program schedule",
    ],
    "announcement": [
        "announcement notice result event festival holiday program celebration",
        "inform students that hostel notice board announcement new rule",
        "application form last date deadline submission scholarship",
        "sports day cultural event competition registration open",
        "exam timetable date sheet test schedule semester result",
        "new policy updated rule fee payment electricity water facility",
        "happy birthday glad to announce congratulation achievement award",
    ],
    "general": [
        "general reminder daily routine information update note message",
        "please ensure lights off quiet hours common area clean",
        "reminder to all students gate timing laundry room mess timing",
        "good morning good evening greetings daily update",
        "please note information for your knowledge kindly be informed",
        "hostel routine regular notice no special event just update",
    ],
}

# ─── Keyword fallback ─────────────────────────────────────────────────────────
KEYWORD_MAP = {
    "urgent": [
        "emergency", "urgent", "immediately", "danger", "warning", "alert",
        "fire", "lockdown", "crisis", "critical", "hazard", "threat",
        "ambulance", "police", "evacuation", "disaster", "compulsory now",
        "right now", "asap", "do not leave",
    ],
    "meeting": [
        "meeting", "assembly", "attend", "gather", "seminar", "session",
        "warden meet", "parent meet", "venue", "hall", "conference",
        "agenda", "discussion", "committee", "scheduled at", "be present",
    ],
    "announcement": [
        "announcement", "notice", "result", "event", "festival", "holiday",
        "program", "celebration", "deadline", "registration", "scholarship",
        "timetable", "exam", "competition", "policy", "rule", "fee",
        "award", "achievement", "inform", "congratulation",
    ],
}


def _cosine_sim(text: str, prototype: str) -> float:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vect = TfidfVectorizer().fit_transform([text, prototype])
    return cosine_similarity(vect[0], vect[1])[0][0]


def _keyword_score(text: str, keywords: list) -> int:
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


MIN_CONFIDENCE = 0.05


def classify_broadcast(message: str) -> str:
    """
    Returns 'general' | 'announcement' | 'urgent' | 'meeting'
    for the given broadcast message string.
    """
    clean = re.sub(r'[^\w\s]', ' ', message.lower())

    try:
        best_cat = "general"
        best_score = 0.0
        for cat, seeds in BROADCAST_SEED.items():
            if cat == "general":
                continue
            prototype = " ".join(seeds)
            score = _cosine_sim(clean, prototype)
            if score > best_score:
                best_score = score
                best_cat = cat
        return best_cat if best_score >= MIN_CONFIDENCE else "general"

    except ImportError:
        # Fallback: keyword scoring
        scores = {cat: _keyword_score(clean, kws) for cat, kws in KEYWORD_MAP.items()}
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "general"
