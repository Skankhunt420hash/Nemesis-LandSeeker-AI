import re
from typing import List

SIGNALS = {
    "strong": [
        "herrenlos", "dereliktion", "ohne eigentümer", "ohne eigentuemer",
        "sans maître", "sans maitre", "senza padrone", "res nullius",
    ],
    "medium": [
        "abandoned parcel", "old access road", "path parcel", "unused road parcel",
        "unknown ownership", "unbekannter eigentümer", "unbekannter eigentuemer",
        "sans propriétaire", "sans proprietaire", "senza proprietario",
    ],
    "weak": [
        "no owner listed", "kein eigentümer aufgeführt", "kein eigentuemer aufgefuehrt",
        "nicht erfasst", "unbekannt", "n/a",
    ],
}

def detect_signals(owner_text: str, land_type: str) -> List[str]:
    text = f"{owner_text or ''} {land_type or ''}".lower()
    hits = []
    for weight, words in SIGNALS.items():
        for w in words:
            if re.search(rf"\b{re.escape(w)}\b", text):
                hits.append(f"{weight}:{w}")
    return sorted(set(hits))

