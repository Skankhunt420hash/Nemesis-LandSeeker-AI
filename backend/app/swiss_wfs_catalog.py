"""Curated Swiss WFS source catalog and lightweight scanner.

The catalog intentionally stores *candidate service endpoints*, not a guarantee
that a layer proves ownership. The scanner only helps users discover relevant
parcel/cadastre layers faster; every result still needs Grundbuch verification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .ingestion import fetch_wfs_metadata


@dataclass(frozen=True)
class WfsSource:
    canton: str
    title: str
    wfs_url: str
    geoportal_url: str
    expected_terms: tuple[str, ...]
    notes: str
    language: str
    status: str = "candidate"


@dataclass(frozen=True)
class WfsLayerMatch:
    name: str
    title: str
    score: int
    matched_terms: tuple[str, ...]
    import_ready: bool
    caution: str


PARCEL_LAYER_TERMS = (
    "grundstueck",
    "grundstück",
    "liegenschaft",
    "parzell",
    "parcel",
    "parcelle",
    "parcella",
    "biens_fonds",
    "bien_fonds",
    "egrid",
    "amtliche_vermessung",
    "av_",
    "mo_",
)

CADASTRE_CONTEXT_TERMS = (
    "oereb",
    "öreb",
    "nutzungsplanung",
    "bauzone",
    "wald",
    "gewaesser",
    "gewässer",
    "schutz",
    "bodenbedeckung",
)

SWISS_WFS_CATALOG: tuple[WfsSource, ...] = (
    WfsSource("AG", "Kanton Aargau Geoportal", "https://geoservices.ag.ch/wfs", "https://www.ag.ch/geoportal", ("grundstueck", "parzell", "liegenschaft", "av_"), "Amtliche-Vermessung und Kataster-Layer pruefen; Layernamen koennen je nach Dienst variieren.", "de"),
    WfsSource("AI", "Appenzell Innerrhoden Geoinformation", "https://www.geoportal.ch/wfs", "https://www.ai.ch/themen/bauen-und-raumplanung/geoinformation", ("grundstueck", "parzell", "liegenschaft", "appenzell"), "Kleiner Kanton im Geoportal-Verbund: Layer im Portal bestaetigen, dann WFS-Metadaten scannen.", "de", "portal_first"),
    WfsSource("AR", "Appenzell Ausserrhoden Geoportal", "https://www.geoportal.ch/wfs", "https://www.geoportal.ch/", ("grundstueck", "parzell", "liegenschaft", "appenzell"), "Geoportal-Verbund: Kanton/Layerscope sauber pruefen, bevor importiert wird.", "de", "portal_first"),
    WfsSource("BE", "Kanton Bern Geoportal", "https://www.geoservice.apps.be.ch/geoservice2/services/a42geo/a42geo_wfs_daten/MapServer/WFSServer", "https://www.geo.apps.be.ch/", ("grundstueck", "parzell", "liegenschaft", "bien_fonds"), "Deutsch/franzoesischer Kanton: deutsche und franzoesische Layerbegriffe pruefen.", "de/fr"),
    WfsSource("BL", "GeoView BL", "https://geoview.bl.ch/geoservice/ows", "https://geoview.bl.ch/", ("grundstueck", "parzell", "liegenschaft"), "OWS-Endpunkt kann WMS/WFS kombiniert anbieten; Metadaten zuerst lesen.", "de"),
    WfsSource("BS", "Geoportal Basel-Stadt", "https://www.geo.bs.ch/ows", "https://www.geo.bs.ch/", ("grundstueck", "parzell", "liegenschaft"), "Staedtische Parzellen- und Kontextdaten priorisieren.", "de"),
    WfsSource("FR", "Geoportal Freiburg", "https://map.geo.fr.ch/arcgis/services/OpenData/MapServer/WFSServer", "https://map.geo.fr.ch/", ("parcelle", "bien_fonds", "cadastre", "mensuration"), "Franzoesische/deutsche Begriffe scannen; Import nur nach Layerpruefung.", "fr/de"),
    WfsSource("GE", "SITG Geneve", "https://ge.ch/sitgags2/rest/services/VECTOR/SITG_OPENDATA_01/MapServer/WFSServer", "https://www.ge.ch/organisation/sitg", ("parcelle", "cadastre", "mensuration"), "SITG Open-Data-Layer koennen stark thematisch getrennt sein.", "fr"),
    WfsSource("GL", "Geoportal Glarus", "https://map.geo.gl.ch/ows", "https://map.geo.gl.ch/", ("grundstueck", "parzell", "liegenschaft"), "Kleiner Kanton: falls WFS leer ist, Geoportal manuell ueber Source Hunter nutzen.", "de"),
    WfsSource("GR", "Geoportal Graubuenden", "https://map.geo.gr.ch/ows", "https://map.geo.gr.ch/", ("grundstueck", "parzell", "parcella", "liegenschaft"), "Mehrsprachig: DE/IT/RM-Begriffe beruecksichtigen.", "de/it/rm"),
    WfsSource("JU", "Geoportal Jura", "https://geo.jura.ch/arcgis/services/Hosted/OpenData/MapServer/WFSServer", "https://geo.jura.ch/", ("parcelle", "cadastre", "mensuration"), "Franzoesische Layerbegriffe priorisieren.", "fr"),
    WfsSource("LU", "Geoportal Luzern", "https://www.geo.lu.ch/map/wfs", "https://www.geo.lu.ch/", ("grundstueck", "parzell", "liegenschaft"), "Falls Dienst Pfad aendert: ueber geo.lu.ch Capabilities-Link neu kopieren.", "de"),
    WfsSource("NE", "SITN Neuchatel", "https://sitn.ne.ch/services/wfs", "https://sitn.ne.ch/", ("parcelle", "cadastre", "mensuration"), "Franzoesische Kataster-/Mensuration-Layer suchen.", "fr"),
    WfsSource("NW", "GIS Nidwalden", "https://www.gis-daten.ch/wfs", "https://www.gis-daten.ch/", ("grundstueck", "parzell", "liegenschaft", "nidwalden"), "Zentralschweizer GIS-Verbund: Portal-Layer und WFS-Metadaten abgleichen.", "de", "portal_first"),
    WfsSource("OW", "GIS Obwalden", "https://www.gis-daten.ch/wfs", "https://www.gis-daten.ch/", ("grundstueck", "parzell", "liegenschaft", "obwalden"), "Zentralschweizer GIS-Verbund: Portal-Layer und WFS-Metadaten abgleichen.", "de", "portal_first"),
    WfsSource("SG", "Geoportal Ostschweiz / St. Gallen", "https://wfs.geo.sg.ch", "https://www.geoportal.ch/", ("grundstueck", "parzell", "liegenschaft"), "Geoportal.ch bedient mehrere Kantone; Kanton im Layernamen pruefen.", "de"),
    WfsSource("SH", "Kanton Schaffhausen GIS", "https://map.geo.sh.ch/ows", "https://map.geo.sh.ch/", ("grundstueck", "parzell", "liegenschaft"), "Metadaten gegen Portal-Layer abgleichen.", "de"),
    WfsSource("SO", "Geoportal Solothurn", "https://geo.so.ch/api/wfs", "https://geo.so.ch/", ("grundstueck", "parzell", "liegenschaft"), "API/WFS kann je nach Version Parameter streng validieren.", "de"),
    WfsSource("SZ", "WebGIS Schwyz", "https://map.geo.sz.ch/ows", "https://map.geo.sz.ch/", ("grundstueck", "parzell", "liegenschaft"), "Manuelle Portalpruefung bleibt wichtig, falls WFS keine AV-Layer ausgibt.", "de"),
    WfsSource("TG", "ThurGIS Thurgau", "https://map.geo.tg.ch/ows", "https://map.geo.tg.ch/", ("grundstueck", "parzell", "liegenschaft"), "Layernamen im Thurgauer Portal gegen WFS-Matches pruefen.", "de"),
    WfsSource("TI", "Geoportal Ticino", "https://map.geo.ti.ch/ows", "https://map.geo.ti.ch/", ("particella", "parcella", "catasto", "misurazione"), "Italienische Katasterbegriffe priorisieren.", "it"),
    WfsSource("UR", "GIS Uri", "https://www.gis-daten.ch/wfs", "https://www.gis-daten.ch/", ("grundstueck", "parzell", "liegenschaft", "uri"), "Zentralschweizer GIS-Verbund: Portal-Layer und WFS-Metadaten abgleichen.", "de", "portal_first"),
    WfsSource("VD", "Geoportail Vaud", "https://www.geo.vd.ch/arcgis/services/Hosted/OpenData/MapServer/WFSServer", "https://www.geo.vd.ch/", ("parcelle", "cadastre", "mensuration"), "Offene Geodaten koennen Kontext liefern; Eigentum bleibt Grundbuchfrage.", "fr"),
    WfsSource("VS", "SIT Valais/Wallis", "https://sitonline.vs.ch/arcgis/services/Hosted/OpenData/MapServer/WFSServer", "https://sitonline.vs.ch/", ("parcelle", "parzell", "cadastre", "grundstueck"), "Zweisprachig scannen; Gemeinde-/Bezirk-Kontext sauber dokumentieren.", "fr/de"),
    WfsSource("ZG", "ZugMap", "https://services.geo.zg.ch/ows", "https://zugmap.ch/", ("grundstueck", "parzell", "liegenschaft"), "ZugMap-Layer zuerst als Kontext/Evidenzquelle nutzen.", "de"),
    WfsSource("ZH", "GIS-ZH", "https://maps.zh.ch/wfs", "https://maps.zh.ch/", ("grundstueck", "parzell", "liegenschaft", "av_"), "GIS-ZH hat viele Layer; nur eindeutig passende AV-/Parzellen-Layer importieren.", "de"),
)


def catalog_as_dict(canton: str | None = None) -> list[dict]:
    sources = get_wfs_sources_by_canton(canton) if canton else SWISS_WFS_CATALOG
    return [asdict(source) for source in sources]


def get_wfs_sources_by_canton(canton: str | None) -> tuple[WfsSource, ...]:
    code = (canton or "").upper()
    return tuple(source for source in SWISS_WFS_CATALOG if source.canton == code)


def _score_feature_type(feature: dict, expected_terms: Iterable[str]) -> WfsLayerMatch:
    name = str(feature.get("name") or "")
    title = str(feature.get("title") or "")
    haystack = f"{name} {title}".lower()
    terms = tuple(dict.fromkeys((*expected_terms, *PARCEL_LAYER_TERMS)))
    matched = tuple(term for term in terms if term.lower() in haystack)
    context_matches = tuple(term for term in CADASTRE_CONTEXT_TERMS if term.lower() in haystack)
    score = min(100, len(matched) * 18 + len(context_matches) * 8)
    import_ready = score >= 18 and bool(name)
    caution = (
        "Guter Parzellen-/Kataster-Kandidat; kleine Stichprobe importieren und Felder pruefen."
        if import_ready
        else "Kein klarer Parzellenlayer. Nur als Kontext nutzen oder manuell im Geoportal pruefen."
    )
    return WfsLayerMatch(name=name, title=title, score=score, matched_terms=matched + context_matches, import_ready=import_ready, caution=caution)


def scan_wfs_source(source: WfsSource) -> dict:
    metadata = fetch_wfs_metadata(source.wfs_url)
    matches = [_score_feature_type(feature, source.expected_terms) for feature in metadata.get("feature_types", [])]
    matches.sort(key=lambda item: item.score, reverse=True)
    return {
        "source": asdict(source),
        "metadata_source": metadata.get("source"),
        "feature_type_count": len(metadata.get("feature_types", [])),
        "matches": [asdict(match) for match in matches[:25]],
        "guardrail": "WFS-Layer identifizieren nur Geodaten. Herrenlosigkeit muss beim Grundbuchamt bestaetigt werden.",
    }


def scan_catalog(canton: str | None = None, max_sources: int = 3) -> dict:
    sources = get_wfs_sources_by_canton(canton) if canton else SWISS_WFS_CATALOG[:max_sources]
    results = []
    errors = []
    for source in sources[:max_sources]:
        try:
            results.append(scan_wfs_source(source))
        except Exception as exc:  # network/service errors are part of WFS reality
            errors.append({"source": asdict(source), "error": str(exc)})
    return {
        "scanned": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
        "guardrail": "Scanner-Ergebnisse sind Recherchehinweise, keine Eigentums- oder Aneignungsnachweise.",
    }
