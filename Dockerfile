ARG DATABRICKS_RUNTIME_IMAGE=databricksruntime/ml:14.3-LTS

FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip build \
  && python -m build --wheel --outdir /dist

FROM ${DATABRICKS_RUNTIME_IMAGE} AS runtime

USER root

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    tini \
  && rm -rf /var/lib/apt/lists/* \
  && useradd --create-home --shell /bin/bash appuser

WORKDIR /opt/iposto-mlops

COPY --from=builder /dist /tmp/dist
COPY src ./src
COPY databricks_assets ./databricks_assets
COPY scripts ./scripts
COPY pyproject.toml README.md ./

RUN python -m pip install --upgrade pip \
  && python -m pip install ".[ml,quality]" \
  && rm -rf /tmp/dist

USER appuser

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "scripts/generate_mock_bronze.py", "--output-dir", "/dbfs/tmp/iposto-mlops/bronze"]
