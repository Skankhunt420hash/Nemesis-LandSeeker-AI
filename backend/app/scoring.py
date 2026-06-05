from typing import List

def score_candidate(signals: List[str], area_sqm: float | None, land_type: str | None, is_protected_land: bool, canton_notes: str | None):
    confidence = 5
    risk = 20

    strong = [s for s in signals if s.startswith("strong:")]
    medium = [s for s in signals if s.startswith("medium:")]
    weak = [s for s in signals if s.startswith("weak:")]

    confidence += len(strong) * 35
    confidence += len(medium) * 15
    confidence += len(weak) * 5

    if weak:
        risk += 10  # weak evidence only
    if area_sqm and area_sqm < 25:
        confidence -= 8
        risk += 15
    if land_type and any(x in land_type.lower() for x in ["road", "path", "forest", "water", "protected"]):
        risk += 25
    if is_protected_land:
        risk += 30
    if canton_notes and "restrictive" in canton_notes.lower():
        confidence -= 10
        risk += 10

    confidence = max(0, min(100, confidence))
    risk = max(0, min(100, risk))
    return confidence, risk

