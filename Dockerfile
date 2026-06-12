FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=prod \
    APP_HOST=0.0.0.0 \
    APP_PORT=8867

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY pyproject.toml ./
COPY src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip install .

USER appuser

EXPOSE 8867

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.getenv('APP_PORT', '8867'), timeout=5).read()" || exit 1

CMD ["t-alpha-api"]
