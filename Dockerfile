FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged system user for security
RUN useradd -m -u 1000 appuser

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/
RUN chown -R appuser:appuser /app

USER appuser

RUN python manage.py collectstatic --noinput

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health/ || exit 1

CMD ["sh", "-c", "python manage.py migrate && if [ \"${DJANGO_SEED_DB:-false}\" = \"true\" ]; then python seed_db.py; fi && gunicorn sumia.wsgi:application --bind 0.0.0.0:${PORT} --workers 3"]

