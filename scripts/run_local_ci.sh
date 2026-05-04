#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
RUFF_BIN="${ROOT_DIR}/.venv/bin/ruff"
FALLBACK_RUNTIME_IMAGE="${FALLBACK_RUNTIME_IMAGE:-python:3.11-slim}"
RUN_DOCKER_CHECK=0

if [[ "${1:-}" == "--with-docker" ]]; then
  RUN_DOCKER_CHECK=1
fi

run_step() {
  local description="$1"
  shift

  echo
  echo "==> ${description}"
  "$@"
}

skip_step() {
  local description="$1"
  echo
  echo "==> Skipping: ${description}"
}

require_file() {
  local path="$1"
  if [[ ! -e "${path}" ]]; then
    echo "Missing required path: ${path}" >&2
    exit 1
  fi
}

require_file "${PYTHON_BIN}"
require_file "${RUFF_BIN}"

run_step "ruff check" "${RUFF_BIN}" check .
run_step "pytest" "${PYTHON_BIN}" -m pytest -q
run_step "terraform fmt -check -recursive" terraform fmt -check -recursive

if command -v databricks >/dev/null 2>&1; then
  if [[ -n "${DATABRICKS_HOST:-}" && -n "${DATABRICKS_TOKEN:-}" ]]; then
    export BUNDLE_VAR_databricks_host="${BUNDLE_VAR_databricks_host:-${DATABRICKS_HOST}}"
    run_step "databricks bundle validate" databricks bundle validate -t dev
  else
    skip_step "databricks bundle validate (set DATABRICKS_HOST and DATABRICKS_TOKEN first)"
  fi
else
  skip_step "databricks bundle validate (databricks CLI not installed)"
fi

if [[ "${RUN_DOCKER_CHECK}" -eq 1 ]]; then
  if command -v docker >/dev/null 2>&1; then
    run_step \
      "docker build fallback image" \
      docker build \
      --build-arg "DATABRICKS_RUNTIME_IMAGE=${FALLBACK_RUNTIME_IMAGE}" \
      -t iposto-mlops:test-local \
      .
  else
    skip_step "docker build (docker CLI not installed)"
  fi
fi

echo
echo "Local CI checks completed."
