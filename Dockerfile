# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS runtime

ARG PRELOAD_WHISPER_MODEL=small
ARG PRELOAD_WHISPER=true

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WHISPER_DOWNLOAD_ROOT=/opt/models \
    DATABASE_SSL_CA=/opt/aws/rds-global-bundle.pem \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/aws /opt/models /app \
    && curl -fsSL "https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem" \
       -o /opt/aws/rds-global-bundle.pem \
    && chmod 0444 /opt/aws/rds-global-bundle.pem

WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app
COPY secretguard ./secretguard
COPY scripts ./scripts

RUN python -m pip install --upgrade pip \
    && python -m pip install ".[voice]" \
    && if [ "$PRELOAD_WHISPER" = "true" ]; then \
         python -c "from faster_whisper import WhisperModel; WhisperModel('${PRELOAD_WHISPER_MODEL}', device='cpu', compute_type='int8', download_root='/opt/models')"; \
       fi \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app /opt/models

USER appuser
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
