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
        coords = (g.get("coordinates") or [None, None])
        rows.append(
            {
                "canton": p.get("canton"),
                "municipality": p.get("municipality"),
                "parcel_number": p.get("parcel_number"),
                "latitude": coords[1],
                "longitude": coords[0],
                "area_sqm": p.get("area_sqm"),
                "land_type": p.get("land_type"),
                "public_owner_text": p.get("public_owner_text"),
                "source_url": p.get("source_url"),
                "is_protected_land": p.get("is_protected_land", False),
            }
        )
    return rows


def ingest_rows(rows: list[dict], db: Session):
    created = 0
    for item in rows:
        payload = schemas.ParcelIngest(
            canton=item.get("canton"),
            municipality=item.get("municipality"),
            parcel_number=str(item.get("parcel_number")),
            latitude=item.get("latitude"),
            longitude=item.get("longitude"),
            area_sqm=item.get("area_sqm"),
            land_type=item.get("land_type"),
            public_owner_text=item.get("public_owner_text"),
            source_url=item.get("source_url"),
            is_protected_land=_normalize_bool(item.get("is_protected_land")),
        )
        create_candidate_record(payload, db)
        created += 1
    return created


def fetch_wfs_metadata(url: str):
    params = {"service": "WFS", "request": "GetCapabilities"}
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)

    ns = {
        "wfs": "http://www.opengis.net/wfs/2.0",
        "ows": "http://www.opengis.net/ows/1.1",
    }
    feature_types = []
    for ft in root.findall(".//wfs:FeatureType", ns):
        name = ft.findtext("wfs:Name", default="", namespaces=ns)
        title = ft.findtext("wfs:Title", default="", namespaces=ns)
        feature_types.append({"name": name, "title": title})
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
        coords = g.get("coordinates") or [None, None]
        lon, lat = (None, None)
        if isinstance(coords, list) and len(coords) >= 2 and isinstance(coords[0], (int, float)):
            lon, lat = coords[0], coords[1]
        rows.append(
            {
                "canton": p.get("canton", ""),
                "municipality": p.get("municipality", ""),
                "parcel_number": p.get("parcel_number", p.get("number", "")),
                "latitude": lat,
                "longitude": lon,
                "area_sqm": p.get("area_sqm", p.get("area")),
                "land_type": p.get("land_type", p.get("type")),
                "public_owner_text": p.get("public_owner_text", p.get("owner", "")),
                "source_url": r.url,
                "is_protected_land": p.get("is_protected_land", False),
            }
        )
    return rows
