import json

from .letters import DISCLAIMER


def build_candidate_dossier(candidate):
    try:
        signals = json.loads(candidate.candidate_signals or "[]")
    except json.JSONDecodeError:
        signals = []
    owner_text = (candidate.public_owner_text or "").lower()
    land_type = (candidate.land_type or "").lower()

    red_flags = []
    if candidate.is_protected_land:
        red_flags.append("Schutz- oder Sondernutzungsflaeche moeglich")
    if any(term in land_type for term in ["road", "path", "weg", "strasse"]):
        red_flags.append("Verkehrs- oder Wegparzelle kann oeffentlich gebunden sein")
    if any(term in land_type for term in ["forest", "wald"]):
        red_flags.append("Forstflaeche kann spezialgesetzlich eingeschraenkt sein")
    if any(term in land_type for term in ["water", "gewaesser"]):
        red_flags.append("Gewaesserflaechen sind regelmaessig unpraktisch oder ausgeschlossen")
    if "no owner listed" in owner_text:
        red_flags.append("'No owner listed' ist nur ein schwaches Signal und kein Eigentumsnachweis")
    if candidate.area_sqm and candidate.area_sqm < 25:
        red_flags.append("Sehr kleine Parzelle mit begrenztem praktischen Nutzen")
    if candidate.risk_score >= 70:
        red_flags.append("Erhoehtes Gesamt-Risiko laut interner Einstufung")
    if not red_flags:
        red_flags.append("Keine harten Ausschlussgruende aus den aktuellen oeffentlichen Daten erkannt")

    practical_score = max(0, min(100, int(candidate.confidence_score - (candidate.risk_score * 0.45))))

    if candidate.confidence_score >= 70 and candidate.risk_score <= 40:
        caution_level = "niedrig"
        registry_readiness = "Bereit fuer formelle Grundbuchanfrage"
    elif candidate.confidence_score >= 45 and candidate.risk_score <= 65:
        caution_level = "mittel"
        registry_readiness = "Vorher weitere Akten und Kartenspuren sammeln"
    else:
        caution_level = "hoch"
        registry_readiness = "Vor Anfrage erst Risiko und Quellenlage absichern"

    next_steps = [
        "Grundbuchamt schriftlich fragen, ob die Parzelle im Register ausdruecklich als herrenlos eingetragen ist",
        "Abklaeren, ob kantonale oder kommunale Vorkaufs-, Bewilligungs- oder Zweckbindungsrechte bestehen",
        "Kataster-, Zonen- und Schutzinformationen mit Datum dokumentieren",
        "Vor jeder weiteren Handlung einen schriftlichen Registernachweis ablegen",
    ]

    evidence_checklist = [
        "Screenshot oder Export der genutzten Geoportal-/Katasterquelle",
        "Parzellennummer, Gemeinde, Koordinaten und Flaeche konsistent dokumentiert",
        "Notiz zum Wortlaut der Eigentuemerangabe aus der oeffentlichen Quelle",
        "Datum der Recherche und Quelle mit URL oder Aktenhinweis abgelegt",
        "Antwort oder Aktenzeichen des Grundbuchamts abgelegt",
    ]

    registry_questions = [
        "Ist die Parzelle im Grundbuch ausdruecklich als herrenlos eingetragen?",
        "Ist eine Aneignung nach Art. 658 ZGB fuer diese konkrete Parzelle grundsaetzlich denkbar?",
        "Bestehen kantonale oder kommunale Vorrechte, Genehmigungspflichten oder Sperrgruende?",
        "Sind Wegrechte, Dienstbarkeiten, Schutzbindungen oder oeffentliche Nutzungen eingetragen?",
    ]

    source_provenance = [
        f"Quelle: {candidate.source_url}",
        f"Letzte Pruefung: {candidate.date_checked}",
        f"Landtyp: {candidate.land_type or 'unbekannt'}",
        f"Oeffentlicher Eigentumshinweis: {candidate.public_owner_text or 'kein Text vorhanden'}",
    ]

    summary = (
        f"Praktische Prioritaet {practical_score}/100. "
        f"Confidence {candidate.confidence_score}/100 bei Risiko {candidate.risk_score}/100. "
        f"Relevanz entsteht erst, wenn das Grundbuch die Parzelle ausdruecklich als herrenlos bestaetigt."
    )

    return {
        "candidate_id": candidate.id,
        "practical_score": practical_score,
        "caution_level": caution_level,
        "summary": summary,
        "registry_readiness": registry_readiness,
        "red_flags": red_flags,
        "next_steps": next_steps,
        "evidence_checklist": evidence_checklist,
        "registry_questions": registry_questions,
        "source_provenance": source_provenance,
        "legal_guardrail": DISCLAIMER,
    }
