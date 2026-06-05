from pathlib import Path
import csv
import io
import json
import os

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from . import models, schemas
from .database import Base, engine, get_db
from .ingestion import (
    create_candidate_record,
    fetch_wfs_geojson_rows,
    fetch_wfs_metadata,
    fetch_wms_metadata,
    ingest_rows,
    parse_csv_rows,
    parse_geojson_rows,
)
from .intelligence import build_candidate_dossier
from .letters import DISCLAIMER, letter_de, letter_fr, letter_it
from .seed import seed_cantons

Base.metadata.create_all(bind=engine)

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

app = FastAPI(title="LandSeeker AI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USE_CELERY = os.getenv("USE_CELERY", "1") == "1"


def _serialize_candidate(row: models.ParcelCandidate):
    return {**row.__dict__, "candidate_signals": json.loads(row.candidate_signals)}


@app.on_event("startup")
def startup_seed():
    db = next(get_db())
    seed_cantons(db)
    if db.query(models.ParcelCandidate).count() == 0:
        seed = schemas.ParcelIngest(
            canton="VS",
            municipality="Sion",
            parcel_number="1452",
            latitude=46.233,
            longitude=7.36,
            area_sqm=42,
            land_type="old access road",
            public_owner_text="no owner listed; possible derelict",
            source_url="https://example.ch/parcel/1452",
            is_protected_land=False,
        )
        create_candidate_record(seed, db)


@app.get("/health")
def health():
    return {"ok": True, "disclaimer": DISCLAIMER, "celery_enabled": USE_CELERY}


@app.get("/cantons", response_model=list[schemas.CantonOut])
def get_cantons(db: Session = Depends(get_db)):
    return db.query(models.Canton).order_by(models.Canton.code).all()


@app.post("/candidates", response_model=schemas.ParcelOut)
def create_candidate(payload: schemas.ParcelIngest, db: Session = Depends(get_db)):
    row = create_candidate_record(payload, db)
    return _serialize_candidate(row)


@app.get("/candidates", response_model=list[schemas.ParcelOut])
def list_candidates(
    canton: str | None = None,
    status: str | None = None,
    min_score: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(models.ParcelCandidate)
    if canton:
        query = query.filter(models.ParcelCandidate.canton == canton)
    if status:
        query = query.filter(models.ParcelCandidate.verification_status == status)
    query = query.filter(models.ParcelCandidate.confidence_score >= min_score)
    rows = query.order_by(models.ParcelCandidate.confidence_score.desc()).all()
    return [_serialize_candidate(row) for row in rows]


@app.patch("/candidates/{candidate_id}/status", response_model=schemas.ParcelOut)
def update_status(candidate_id: int, body: schemas.ParcelUpdateStatus, db: Session = Depends(get_db)):
    row = db.query(models.ParcelCandidate).filter(models.ParcelCandidate.id == candidate_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    row.verification_status = body.verification_status
    db.commit()
    db.refresh(row)
    return _serialize_candidate(row)


@app.get("/candidates/{candidate_id}/letter")
def generate_letter(candidate_id: int, lang: str = "de", db: Session = Depends(get_db)):
    row = db.query(models.ParcelCandidate).filter(models.ParcelCandidate.id == candidate_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    letter_fn = {"de": letter_de, "fr": letter_fr, "it": letter_it}.get(lang, letter_de)
    return {"language": lang, "text": letter_fn(row)}


@app.get("/candidates/{candidate_id}/dossier", response_model=schemas.CandidateDossierOut)
def generate_dossier(candidate_id: int, db: Session = Depends(get_db)):
    row = db.query(models.ParcelCandidate).filter(models.ParcelCandidate.id == candidate_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return build_candidate_dossier(row)


@app.post("/ingest/upload")
async def ingest_upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    name = (file.filename or "").lower()

    if name.endswith(".csv"):
        rows = parse_csv_rows(content)
    elif name.endswith(".geojson"):
        rows = parse_geojson_rows(content)
    else:
        raise HTTPException(status_code=400, detail="Supported formats: CSV, GeoJSON")

    if USE_CELERY:
        from .tasks import ingest_rows_task

        task = ingest_rows_task.delay(rows)
        return {"accepted": len(rows), "mode": "celery", "task_id": task.id}

    created = ingest_rows(rows, db)
    return {"accepted": len(rows), "created": created, "mode": "direct"}


@app.post("/ingest/wfs/metadata")
def ingest_wfs_metadata(payload: schemas.ServiceMetadataRequest):
    return fetch_wfs_metadata(payload.url)


@app.post("/ingest/wms/metadata")
def ingest_wms_metadata(payload: schemas.ServiceMetadataRequest):
    return fetch_wms_metadata(payload.url)


@app.post("/ingest/wfs/features")
def ingest_wfs_features(payload: schemas.WfsImportRequest, db: Session = Depends(get_db)):
    rows = fetch_wfs_geojson_rows(payload.url, payload.type_name, payload.limit)

    if USE_CELERY:
        from .tasks import ingest_rows_task

        task = ingest_rows_task.delay(rows)
        return {"accepted": len(rows), "mode": "celery", "task_id": task.id}

    created = ingest_rows(rows, db)
    return {"accepted": len(rows), "created": created, "mode": "direct"}


@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    if not USE_CELERY:
        raise HTTPException(status_code=400, detail="Celery mode not enabled")
    from .tasks import celery_app

    result = celery_app.AsyncResult(task_id)
    return {"task_id": task_id, "state": result.state, "result": result.result if result.ready() else None}


@app.get("/export/csv")
def export_csv(db: Session = Depends(get_db)):
    rows = db.query(models.ParcelCandidate).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "canton", "municipality", "parcel_number", "confidence", "risk", "status", "source"])
    for row in rows:
        writer.writerow(
            [
                row.id,
                row.canton,
                row.municipality,
                row.parcel_number,
                row.confidence_score,
                row.risk_score,
                row.verification_status,
                row.source_url,
            ]
        )
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=landseeker_export.csv"},
    )


@app.get("/export/pdf")
def export_pdf(db: Session = Depends(get_db)):
    rows = db.query(models.ParcelCandidate).order_by(models.ParcelCandidate.confidence_score.desc()).all()
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(40, 800, "LandSeeker AI Candidate Report")
    pdf.drawString(40, 785, "Disclaimer: Every candidate must be verified with the responsible Grundbuchamt.")
    y = 760
    for row in rows[:30]:
        pdf.drawString(
            40,
            y,
            f"#{row.id} {row.canton}-{row.municipality} Parcel {row.parcel_number} Score {row.confidence_score} Risk {row.risk_score}",
        )
        y -= 16
        if y < 60:
            pdf.showPage()
            y = 800
    pdf.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=landseeker_report.pdf"},
    )


if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/manifest.webmanifest", include_in_schema=False)
    def manifest_file():
        return FileResponse(FRONTEND_DIST / "manifest.webmanifest")

    @app.get("/sw.js", include_in_schema=False)
    def service_worker():
        return FileResponse(FRONTEND_DIST / "sw.js")

    @app.get("/icon.svg", include_in_schema=False)
    def app_icon():
        return FileResponse(FRONTEND_DIST / "icon.svg")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_entry(full_path: str):
        requested = FRONTEND_DIST / full_path
        if full_path and requested.exists() and requested.is_file():
            return FileResponse(requested)
        return FileResponse(FRONTEND_DIST / "index.html")
