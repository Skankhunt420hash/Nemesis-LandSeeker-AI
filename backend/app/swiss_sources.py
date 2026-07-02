"""Official-source guidance for Swiss parcel research.

The app must not pretend that public map layers prove ownerless land. In
Switzerland the decisive source is the land register (Grundbuch / registre
foncier / registro fondiario). This module gives users a practical, canton-aware
research cockpit: where to look first, what evidence to collect, and which terms
are worth scanning for before a formal registry request.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SwissResearchSource:
    key: str
    title: str
    kind: str
    url: str
    purpose: str
    evidence_value: str
    caution: str


@dataclass(frozen=True)
class CantonResearchProfile:
    canton: str
    language: str
    geoportal_url: str
    registry_hint: str
    search_terms: tuple[str, ...]
    recommended_layers: tuple[str, ...]


NATIONAL_SOURCES: tuple[SwissResearchSource, ...] = (
    SwissResearchSource(
        key="cadastre_ch",
        title="cadastre.ch - Amtliche Vermessung und Kataster-Portal",
        kind="national_portal",
        url="https://www.cadastre.ch/",
        purpose="Startpunkt fuer amtliche Vermessung, Katasterinformationen und kantonale Weiterleitungen.",
        evidence_value="hoch fuer Parzellenidentifikation, nicht ausreichend fuer Herrenlosigkeit",
        caution="Eigentuemer- oder Herrenlos-Status muss beim Grundbuch bestaetigt werden.",
    ),
    SwissResearchSource(
        key="geo_admin",
        title="map.geo.admin.ch - Bundes-Geodatenviewer",
        kind="national_map",
        url="https://map.geo.admin.ch/",
        purpose="Bundesweite Kartenebenen: Schutzgebiete, Wald, Gewaesser, Nutzungs- und Risiko-Layer.",
        evidence_value="hoch fuer Red-Flags und Kontext, nicht fuer Eigentumsnachweis",
        caution="Bundeslayer koennen kantonale Registerdaten nicht ersetzen.",
    ),
    SwissResearchSource(
        key="amtliche_vermessung",
        title="Amtliche Vermessung Schweiz",
        kind="cadastre",
        url="https://www.cadastre.ch/de/amtliche-vermessung.html",
        purpose="Parzellengrenzen, Flaechen, Lage, Gebaeude- und Bodenbedeckungsinformationen pruefen.",
        evidence_value="hoch fuer Objektidentifikation",
        caution="Parzelle gefunden bedeutet nicht herrenlos.",
    ),
    SwissResearchSource(
        key="zgb_658",
        title="Art. 658 ZGB - Herrenlose Grundstuecke",
        kind="legal_basis",
        url="https://www.fedlex.admin.ch/eli/cc/24/233_245_233/de#art_658",
        purpose="Rechtsgrundlage fuer Aneignung nur bei ausdruecklichem Grundbucheintrag als herrenlos.",
        evidence_value="entscheidend fuer rechtliche Leitplanke",
        caution="Keine automatische Aneignung, keine Rechtsberatung.",
    ),
)


LANG_BY_CANTON = {
    "AG": "de", "AI": "de", "AR": "de", "BE": "de/fr", "BL": "de", "BS": "de", "FR": "fr/de",
    "GE": "fr", "GL": "de", "GR": "de/it/rm", "JU": "fr", "LU": "de", "NE": "fr", "NW": "de",
    "OW": "de", "SG": "de", "SH": "de", "SO": "de", "SZ": "de", "TG": "de", "TI": "it",
    "UR": "de", "VD": "fr", "VS": "fr/de", "ZG": "de", "ZH": "de",
}


CANTON_GEO_URLS = {
    "AG": "https://www.ag.ch/geoportal", "AI": "https://www.ai.ch/themen/bauen-und-raumplanung/geoinformation",
    "AR": "https://www.geoportal.ch/", "BE": "https://www.geo.apps.be.ch/", "BL": "https://geoview.bl.ch/",
    "BS": "https://www.geo.bs.ch/", "FR": "https://map.geo.fr.ch/", "GE": "https://www.ge.ch/organisation/sitG",
    "GL": "https://map.geo.gl.ch/", "GR": "https://map.geo.gr.ch/", "JU": "https://geo.jura.ch/",
    "LU": "https://www.geo.lu.ch/", "NE": "https://sitn.ne.ch/", "NW": "https://www.gis-daten.ch/",
    "OW": "https://www.gis-daten.ch/", "SG": "https://www.geoportal.ch/", "SH": "https://map.geo.sh.ch/",
    "SO": "https://geo.so.ch/", "SZ": "https://map.geo.sz.ch/", "TG": "https://map.geo.tg.ch/",
    "TI": "https://map.geo.ti.ch/", "UR": "https://www.gis-daten.ch/", "VD": "https://www.geo.vd.ch/",
    "VS": "https://sitonline.vs.ch/", "ZG": "https://zugmap.ch/", "ZH": "https://maps.zh.ch/",
}


BASE_SEARCH_TERMS = (
    "herrenlos", "Dereliktion", "ohne Eigentuemer", "unbekannter Eigentuemer",
    "sans maitre", "sans proprietaire", "abandon", "senza padrone", "senza proprietario",
)


RECOMMENDED_LAYERS = (
    "Amtliche Vermessung / Liegenschaften",
    "Grundstuecksnummer / Parzellennummer",
    "Bodenbedeckung: Wald, Weg, Gewaesser, Gebaeude",
    "Nutzungsplanung / Bauzonen / Landwirtschaftszonen",
    "Schutzgebiete: Wald, Gewaesserraum, Natur- und Heimatschutz",
    "Oeffentlich-rechtliche Eigentumsbeschraenkungen (OEREB), falls verfuegbar",
)


def canton_profile(canton: str) -> CantonResearchProfile:
    code = (canton or "").upper()
    return CantonResearchProfile(
        canton=code,
        language=LANG_BY_CANTON.get(code, "de/fr/it"),
        geoportal_url=CANTON_GEO_URLS.get(code, "https://www.cadastre.ch/"),
        registry_hint="Zustaendiges Grundbuchamt/Kreisgrundbuchamt ueber Kanton oder Gemeinde ermitteln.",
        search_terms=BASE_SEARCH_TERMS,
        recommended_layers=RECOMMENDED_LAYERS,
    )


def build_search_plan(canton: str | None = None, municipality: str | None = None):
    profile = canton_profile(canton or "")
    area = f"{municipality}, {profile.canton}" if municipality and profile.canton else municipality or profile.canton or "Schweiz"
    steps = [
        "Parzelle in amtlicher Vermessung eindeutig identifizieren: Nummer, EGRID falls vorhanden, Flaeche, Koordinaten.",
        "Geoportal-/OEREB-Kontext sichern: Zone, Wald, Gewaesser, Schutz, Wege, Dienstbarkeits-Hinweise falls sichtbar.",
        "Oeffentliche Hinweise auf Eigentuemertext nur als Signal behandeln, nie als Beweis.",
        "Kandidaten mit hohem Score priorisieren, aber Red-Flags vor der Anfrage dokumentieren.",
        "Beim Grundbuchamt schriftlich fragen, ob die Parzelle ausdruecklich als herrenlos eingetragen ist.",
    ]
    return {
        "area": area,
        "profile": asdict(profile),
        "national_sources": [asdict(source) for source in NATIONAL_SOURCES],
        "steps": steps,
        "must_have_evidence": [
            "Parzellennummer oder EGRID",
            "Gemeinde und Kanton",
            "Quelle/URL und Recherchedatum",
            "Screenshot oder Export der Karten-/Katasteransicht",
            "Schriftliche Antwort oder Aktenzeichen des Grundbuchamts",
        ],
        "killer_question": "Ist diese konkrete Parzelle im Grundbuch ausdruecklich als herrenlos eingetragen?",
        "legal_guardrail": "Art. 658 ZGB: Nur der Grundbucheintrag kann Herrenlosigkeit rechtlich tragen.",
    }
