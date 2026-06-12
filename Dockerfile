FROM python:3.11-slim

ARG AMAZINGDATA_SDK_REPO=https://gitee.com/cgs2026/xysz.git
ARG AMAZINGDATA_VERSION=1.1.8
ARG TGW_VERSION=1.0.8.7

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=prod \
    APP_HOST=0.0.0.0 \
    APP_PORT=8867

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser \
    && apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src

RUN python -m pip install --upgrade pip \
    && git clone --depth 1 "$AMAZINGDATA_SDK_REPO" /tmp/xysz-sdk \
    && python -m pip install \
        "/tmp/xysz-sdk/xysz/xysz_tools/tgw-${TGW_VERSION}-py3-none-any.whl" \
        "/tmp/xysz-sdk/xysz/xysz_tools/AmazingData/AmazingData-${AMAZINGDATA_VERSION}-cp311-none-any.whl" \
    && rm -rf /tmp/xysz-sdk \
    && python -m pip install .

USER appuser

EXPOSE 8867

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.getenv('APP_PORT', '8867'), timeout=5).read()" || exit 1

CMD ["t-alpha-api"]
