import csv
import io
import json
import xml.etree.ElementTree as ET
from typing import Any

import requests
from sqlalchemy.orm import Session

from . import models, schemas
from .detector import detect_signals
from .scoring import score_candidate


FIELD_ALIASES = {
    "canton": ("canton", "kanton", "kt", "ct", "canton_code"),
    "municipality": ("municipality", "gemeinde", "commune", "comune", "municipalite", "bfs_name", "gemname"),
    "parcel_number": ("parcel_number", "parzellennummer", "parzelle", "grundstuecknummer", "grundstücknummer", "nummer", "number", "egrid", "liegenschaftsnummer"),
    "area_sqm": ("area_sqm", "flaeche", "fläche", "area", "shape_area", "flaeche_m2", "m2"),
    "land_type": ("land_type", "type", "art", "bodenbedeckung", "nutzung", "zone", "objektart"),
    "public_owner_text": ("public_owner_text", "owner", "eigentuemer", "eigentümer", "proprietaire", "propriétaire", "proprietario", "bemerkung", "hinweis"),
    "source_url": ("source_url", "url", "source", "quelle"),
    "is_protected_land": ("is_protected_land", "protected", "schutz", "schutzgebiet"),
}


def _first_value(data: dict, aliases: tuple[str, ...], default=None):
    lowered = {str(k).strip().lower(): v for k, v in data.items()}
    for alias in aliases:
        value = lowered.get(alias)
        if value not in (None, ""):
            return value
    return default


def _centroid_from_coordinates(coords):
    points = []

    def walk(value):
        if isinstance(value, list) and len(value) >= 2 and all(isinstance(x, (int, float)) for x in value[:2]):
            points.append((value[0], value[1]))
            return
        if isinstance(value, list):
            for child in value:
                walk(child)

    walk(coords)
    if not points:
        return None, None
    lon = sum(point[0] for point in points) / len(points)
    lat = sum(point[1] for point in points) / len(points)
    return lon, lat


def normalize_ingest_row(item: dict, fallback_source_url: str | None = None):
    return {
        "canton": _first_value(item, FIELD_ALIASES["canton"], ""),
        "municipality": _first_value(item, FIELD_ALIASES["municipality"], ""),
        "parcel_number": str(_first_value(item, FIELD_ALIASES["parcel_number"], "")),
        "latitude": _first_value(item, ("latitude", "lat", "y")),
        "longitude": _first_value(item, ("longitude", "lon", "lng", "x")),
        "area_sqm": _first_value(item, FIELD_ALIASES["area_sqm"]),
        "land_type": _first_value(item, FIELD_ALIASES["land_type"]),
        "public_owner_text": _first_value(item, FIELD_ALIASES["public_owner_text"]),
        "source_url": _first_value(item, FIELD_ALIASES["source_url"], fallback_source_url or "manual-import"),
        "is_protected_land": _normalize_bool(_first_value(item, FIELD_ALIASES["is_protected_land"], False)),
    }


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "ja"}


def create_candidate_record(payload: schemas.ParcelIngest, db: Session):
    signals = detect_signals(payload.public_owner_text or "", payload.land_type or "")
    canton = db.query(models.Canton).filter(models.Canton.code == payload.canton).first()
    notes = canton.notes if canton else ""
    conf, risk = score_candidate(signals, payload.area_sqm, payload.land_type, payload.is_protected_land, notes)
    ai = (
        f"Flagged due to: {', '.join(signals) if signals else 'no direct ownerless wording'}. "
        "Art. 658 ZGB requires registry confirmation."
    )
    row = models.ParcelCandidate(
        **payload.model_dump(),
        candidate_signals=json.dumps(signals),
        confidence_score=conf,
        risk_score=risk,
        ai_explanation=ai,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def parse_csv_rows(content: bytes):
    decoded = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    rows = []
    for raw in reader:
        clean = {}
        for k, v in raw.items():
            nk = (k or "").replace("\ufeff", "").strip().lower()
            clean[nk] = v
        rows.append(clean)
    return rows


def parse_geojson_rows(content: bytes):
    doc = json.loads(content.decode("utf-8"))
    rows = []
    for f in doc.get("features", []):
        p = f.get("properties", {})
        g = f.get("geometry", {})
        lon, lat = _centroid_from_coordinates(g.get("coordinates") or [])
        row = normalize_ingest_row(p)
        row["latitude"] = row["latitude"] or lat
        row["longitude"] = row["longitude"] or lon
        rows.append(row)
    return rows


def ingest_rows(rows: list[dict], db: Session):
    created = 0
    for item in rows:
        row = normalize_ingest_row(item)
        payload = schemas.ParcelIngest(
            canton=row.get("canton"),
            municipality=row.get("municipality"),
            parcel_number=row.get("parcel_number"),
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            area_sqm=row.get("area_sqm"),
            land_type=row.get("land_type"),
            public_owner_text=row.get("public_owner_text"),
            source_url=row.get("source_url"),
            is_protected_land=row.get("is_protected_land"),
        )
        create_candidate_record(payload, db)
        created += 1
    return created


def fetch_wfs_metadata(url: str):
    params = {"service": "WFS", "request": "GetCapabilities"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)

    namespaces = {
        "wfs20": "http://www.opengis.net/wfs/2.0",
        "wfs11": "http://www.opengis.net/wfs",
        "ows": "http://www.opengis.net/ows/1.1",
    }
    feature_types = []
    seen = set()
    for path, prefix in ((".//wfs20:FeatureType", "wfs20"), (".//wfs11:FeatureType", "wfs11")):
        for ft in root.findall(path, namespaces):
            name = ft.findtext(f"{prefix}:Name", default="", namespaces=namespaces).strip()
            title = ft.findtext(f"{prefix}:Title", default="", namespaces=namespaces).strip()
            if name and name not in seen:
                feature_types.append({"name": name, "title": title})
                seen.add(name)
    return {"service": "WFS", "source": r.url, "feature_types": feature_types}


def fetch_wms_metadata(url: str):
    params = {"service": "WMS", "request": "GetCapabilities"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)

    layers = []
    for layer in root.findall(".//{http://www.opengis.net/wms}Layer"):
        name = layer.findtext("{http://www.opengis.net/wms}Name", default="")
        title = layer.findtext("{http://www.opengis.net/wms}Title", default="")
        if name:
            layers.append({"name": name, "title": title})
    return {"service": "WMS", "source": r.url, "layers": layers}


def fetch_wfs_geojson_rows(url: str, type_name: str, limit: int = 200):
    params = {
        "service": "WFS",
        "request": "GetFeature",
        "typeNames": type_name,
        "outputFormat": "application/json",
        "count": limit,
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    doc = r.json()
    rows = []
    for f in doc.get("features", []):
        p = f.get("properties", {})
        g = f.get("geometry", {})
        lon, lat = _centroid_from_coordinates(g.get("coordinates") or [])
        row = normalize_ingest_row(p, fallback_source_url=r.url)
        row["latitude"] = row["latitude"] or lat
        row["longitude"] = row["longitude"] or lon
        rows.append(row)
    return rows
