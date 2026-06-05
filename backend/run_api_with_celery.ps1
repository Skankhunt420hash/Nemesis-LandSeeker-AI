$env:USE_CELERY="1"
uvicorn app.main:app --reload --port 8000
