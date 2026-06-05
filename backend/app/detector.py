import re
from typing import List

SIGNALS = {
    "strong": ["herrenlos", "ohne eigentümer", "sans maître", "senza padrone", "derelict", "dereliktion"],
    "medium": ["abandoned parcel", "old access road", "path parcel", "unused road parcel", "unknown ownership"],
    "weak": ["no owner listed"],
}

def detect_signals(owner_text: str, land_type: str) -> List[str]:
    text = f"{owner_text or ''} {land_type or ''}".lower()
    hits = []
    for weight, words in SIGNALS.items():
        for w in words:
            if re.search(rf"\b{re.escape(w)}\b", text):
                hits.append(f"{weight}:{w}")
    return sorted(set(hits))

