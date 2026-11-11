FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/worker ./apps/worker
COPY apps/analyzer ./apps/analyzer
COPY packages ./packages

ENV PYTHONPATH=/app

CMD ["celery", "-A", "apps.worker.main.celery_app", "worker", "--loglevel=info"]
