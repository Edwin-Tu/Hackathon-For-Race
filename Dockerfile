# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS runtime

ARG PRELOAD_WHISPER_MODEL=small
ARG PRELOAD_WHISPER=true
ARG INSTALL_BILINGUAL_VOICE=false
ARG PRELOAD_BREEZE=false
ARG PRELOAD_TAIWANESE_TTS=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    WHISPER_DOWNLOAD_ROOT=/opt/models \
    HF_HOME=/opt/models/huggingface \
    TRANSFORMERS_CACHE=/opt/models/huggingface \
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
    && if [ "$INSTALL_BILINGUAL_VOICE" = "true" ]; then \
         python -m pip install ".[bilingual-voice]"; \
       else \
         python -m pip install ".[voice]"; \
       fi \
    && if [ "$PRELOAD_WHISPER" = "true" ]; then \
         python -c "from faster_whisper import WhisperModel; WhisperModel('${PRELOAD_WHISPER_MODEL}', device='cpu', compute_type='int8', download_root='/opt/models')"; \
       fi \
    && if [ "$PRELOAD_BREEZE" = "true" ]; then \
         python -c "from transformers import pipeline; pipeline('automatic-speech-recognition', model='MediaTek-Research/Breeze-ASR-26', device=-1)"; \
       fi \
    && if [ "$PRELOAD_TAIWANESE_TTS" = "true" ]; then \
         python -c "from transformers import AutoTokenizer, VitsModel; AutoTokenizer.from_pretrained('facebook/mms-tts-nan'); VitsModel.from_pretrained('facebook/mms-tts-nan')"; \
       fi \
    && useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app /opt/models

USER appuser
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
