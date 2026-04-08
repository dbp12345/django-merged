#!/usr/bin/env bash

set -Eeuo pipefail

log() {
  echo "[deploy] $*"
}

fail() {
  echo "[deploy] ERROR: $*" >&2
  exit 1
}

PROJECT_PATH="${LIGHTSAIL_PROJECT_PATH:-}"
DEPLOY_BRANCH="${DEPLOY_BRANCH:-dev}"
VENV_PATH="${VENV_PATH:-}"
PYTHON_BIN="${PYTHON_BIN:-python}"
PIP_BIN="${PIP_BIN:-pip}"
RESTART_CMD="${RESTART_CMD:-}"
REQUIRED_ENV_VARS="${REQUIRED_ENV_VARS:-}"
SYSTEM_PACKAGES="${SYSTEM_PACKAGES:-}"
APT_GET_BIN="${APT_GET_BIN:-apt-get}"
SUDO_BIN="${SUDO_BIN:-sudo}"

if [[ -z "$PROJECT_PATH" ]]; then
  fail "LIGHTSAIL_PROJECT_PATH is required."
fi

if [[ ! -d "$PROJECT_PATH" ]]; then
  fail "Project path does not exist: $PROJECT_PATH"
fi

if [[ -n "$VENV_PATH" ]]; then
  if [[ -f "$VENV_PATH" ]]; then
    log "Activating virtualenv from file: $VENV_PATH"
    # shellcheck disable=SC1090
    source "$VENV_PATH"
  elif [[ -f "$VENV_PATH/bin/activate" ]]; then
    log "Activating virtualenv from directory: $VENV_PATH"
    # shellcheck disable=SC1091
    source "$VENV_PATH/bin/activate"
  else
    fail "VENV_PATH does not point to an activate script or virtualenv directory."
  fi
fi

cd "$PROJECT_PATH"

if [[ -n "$REQUIRED_ENV_VARS" ]]; then
  log "Checking required environment variables"
  for var_name in $REQUIRED_ENV_VARS; do
    if [[ -z "${!var_name:-}" ]]; then
      fail "Missing required environment variable: $var_name"
    fi
  done
fi

if [[ -n "$SYSTEM_PACKAGES" ]]; then
  if ! command -v "$APT_GET_BIN" >/dev/null 2>&1; then
    fail "SYSTEM_PACKAGES was provided but '$APT_GET_BIN' is not available on this server."
  fi

  INSTALL_CMD=("$APT_GET_BIN")
  if command -v "$SUDO_BIN" >/dev/null 2>&1; then
    INSTALL_CMD=("$SUDO_BIN" "$APT_GET_BIN")
  fi

  log "Installing system packages: $SYSTEM_PACKAGES"
  "${INSTALL_CMD[@]}" update
  # shellcheck disable=SC2086
  "${INSTALL_CMD[@]}" install -y $SYSTEM_PACKAGES
fi

log "Fetching latest branch state for $DEPLOY_BRANCH"
git fetch origin "$DEPLOY_BRANCH"

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" != "$DEPLOY_BRANCH" ]]; then
  log "Checking out $DEPLOY_BRANCH"
  git checkout "$DEPLOY_BRANCH"
fi

log "Pulling latest code"
git pull --ff-only origin "$DEPLOY_BRANCH"

log "Installing Python dependencies"
"$PIP_BIN" install -r requirements.txt

log "Applying migrations"
"$PYTHON_BIN" manage.py migrate

log "Running Django system checks"
"$PYTHON_BIN" manage.py check

log "Collecting static files"
"$PYTHON_BIN" manage.py collectstatic --noinput

if [[ -n "$RESTART_CMD" ]]; then
  log "Restarting app service"
  bash -lc "$RESTART_CMD"
else
  log "No restart command configured. Skipping service restart."
fi

log "Deployment completed successfully"
