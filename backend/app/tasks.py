from .celery_app import celery_app
from .database import SessionLocal
from .ingestion import ingest_rows


@celery_app.task(name="ingest_rows_task")
def ingest_rows_task(rows: list[dict]):
    db = SessionLocal()
    try:
        created = ingest_rows(rows, db)
        return {"created": created, "accepted": len(rows)}
    finally:
        db.close()
