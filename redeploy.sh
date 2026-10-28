#!/bin/bash
# Tests -> Build -> Deploy -> Verify. Aborts on the first failure and leaves
# the running app untouched. Runs interactively or from the deploy pipeline.
#
# Usage:
#   ./redeploy.sh              # deploy
#   ./redeploy.sh --no-cache   # rebuild app and app-tests without the Docker build cache,
#                              # so unpinned dependencies are reinstalled (T-013)
#
# Started from a terminal, the deploy runs detached (T-011): a dropped SSH
# connection does not stop it, Ctrl-C does. Follow a running deploy with
#   tail -f redeploy.log
#
# It refuses to start while the shell exports a key from .env with another value (T-012).

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[$(date '+%H:%M:%S')] $*${NC}"; }
warn() { echo -e "${YELLOW}[$(date '+%H:%M:%S')] $*${NC}"; }
err()  { echo -e "${RED}[$(date '+%H:%M:%S')] $*${NC}" >&2; }

HEALTH_TIMEOUT=60
HEALTH_INTERVAL=2
LOG_FILE="redeploy.log"                     # in the deploy directory (gitignored)
LOCK_FILE="/tmp/${PWD##*/}-redeploy.lock"   # one deploy at a time; not under volumes/, which belongs to Docker

usage() { echo "Usage: $0 [--no-cache]"; }

NO_CACHE=""
for arg in "$@"; do
    case "$arg" in
        --no-cache) NO_CACHE="--no-cache" ;;
        *) err "Unknown option: $arg"; usage; exit 1 ;;
    esac
done

# --- Shell variables must not override .env (T-012) ---
# docker compose takes an exported shell variable over the same key in .env. Values left in a shell
# from another project or stage go silently into this deploy (database user, ports, project name).
# Prints the names of the keys the shell sets to another value; values are never printed.
env_overrides() {
    local line key value dq='^"(.*)"$' sq="^'(.*)'\$"
    [ -f .env ] || return 0
    while IFS= read -r line || [ -n "$line" ]; do
        line="${line%$'\r'}"
        line="${line#export }"
        [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || continue
        key="${line%%=*}"
        printenv "$key" >/dev/null || continue
        value="${line#*=}"
        if [[ "$value" =~ $dq || "$value" =~ $sq ]]; then
            value="${BASH_REMATCH[1]}"
        else
            # Unquoted, the value ends before " #" and trailing blanks, as docker compose reads it
            value="${value%%[[:space:]]#*}"
            value="${value%"${value##*[![:space:]]}"}"
        fi
        [ "$(printenv "$key")" = "$value" ] || printf ' %s' "$key"
    done < .env
}
ENV_OVERRIDES=$(env_overrides)
if [ -n "$ENV_OVERRIDES" ]; then
    err "Set in this shell with a value other than in .env:${ENV_OVERRIDES}"
    err "docker compose would take the shell values. Run 'unset${ENV_OVERRIDES}' or open a new terminal. Deployment aborted."
    exit 1
fi

# --- Detach from the terminal (T-011) ---
# Started from an SSH session, the script re-runs itself in its own session under nohup, writes to
# LOG_FILE and only follows that log here. A dropped SSH connection (SIGHUP) kills the log viewer, not
# the deploy, so the app is never left stopped halfway through. Ctrl-C (SIGINT) still aborts: the viewer
# forwards it to the deploy's process group. The deploy pipeline (no terminal) and the detached child
# skip this block.
if [ -t 1 ] && [ -z "${REDEPLOY_DETACHED:-}" ]; then
    flock -n "$LOCK_FILE" true
    LOCK_STATUS=$?
    if [ $LOCK_STATUS -eq 1 ]; then
        err "A redeploy is already running (lock ${LOCK_FILE}). Follow it with: tail -f ${LOG_FILE}"
        exit 1
    elif [ $LOCK_STATUS -ne 0 ]; then
        err "Cannot use the lock file ${LOCK_FILE} (flock exit ${LOCK_STATUS}). Deployment aborted."
        exit 1
    fi
    : > "$LOG_FILE"
    # Through bash, so `bash redeploy.sh` (no ./, no exec bit) re-runs as well as ./redeploy.sh
    REDEPLOY_DETACHED=1 setsid nohup flock "$LOCK_FILE" bash "$0" "$@" > "$LOG_FILE" 2>&1 < /dev/null &
    CHILD=$!
    trap 'warn "Ctrl-C: aborting the deploy"; kill -INT -- -"$CHILD" 2>/dev/null; sleep 1; kill -TERM -- -"$CHILD" 2>/dev/null' INT
    warn "--- Redeploy runs detached (pid ${CHILD}), log: ${LOG_FILE}. A dropped SSH session does not stop it, Ctrl-C does. ---"
    tail -n +1 -f --pid="$CHILD" "$LOG_FILE" &
    TAIL=$!
    wait "$CHILD" 2>/dev/null
    wait "$TAIL" 2>/dev/null
    EXIT_CODE=$(sed -n 's/^\[redeploy exit \([0-9]*\)\]$/\1/p' "$LOG_FILE" | tail -n 1)
    # The deploy has ended and released the lock. Following the logs is only watching:
    # Ctrl-C ends it without an error, and a dropped session leaves nothing running.
    if [ "${EXIT_CODE:-1}" = "0" ]; then
        log "7. Showing logs (Ctrl+C to stop watching, the deploy is done):"
        trap 'exit 0' INT
        docker compose logs -f app 2>&1
    fi
    exit "${EXIT_CODE:-1}"
fi
# The detached child ignores a hangup and reports its exit code as the last log line for the viewer.
if [ -n "${REDEPLOY_DETACHED:-}" ]; then
    trap '' HUP
    trap 'err "Aborted by Ctrl-C."; exit 130' INT TERM
    trap 'echo "[redeploy exit $?]"' EXIT
fi

warn "--- Redeploy Script ---"

# Ensure containers run as current user
export HOST_UID=$(id -u)
export HOST_GID=$(id -g)

# --- STEP 0: PRE-FLIGHT TESTS ---
TIMESTAMP=$(date +%s)
TEST_CONTAINER_NAME="test_run_${TIMESTAMP}"
REBUILT=0

log "0. Running tests (testmon: only affected tests)..."
echo "   Container name: ${TEST_CONTAINER_NAME}"

# Only rebuild image if requirements.txt changed (source comes via volume mount), or with --no-cache
REQ_HASH_FILE="app/.requirements_hash"
REQ_HASH_CURRENT=$(md5sum app/requirements.txt | cut -d' ' -f1)
REQ_HASH_SAVED=$(cat "$REQ_HASH_FILE" 2>/dev/null || echo "")

if [ "$REQ_HASH_CURRENT" != "$REQ_HASH_SAVED" ] || [ -n "$NO_CACHE" ]; then
    if [ -n "$NO_CACHE" ]; then
        warn "   --no-cache -> rebuilding app-tests image without the build cache..."
    else
        warn "   requirements.txt changed -> rebuilding app-tests image..."
    fi
    # The hash is written only after a successful build: a failed build must
    # not mark the old image as current, or every later run skips the rebuild.
    if ! docker compose build $NO_CACHE app-tests; then
        err "BUILD OF app-tests FAILED. Deployment aborted. The running app is unchanged."
        exit 1
    fi
    echo "$REQ_HASH_CURRENT" > "$REQ_HASH_FILE"
    REBUILT=1
fi

# T-014: four workers (pytest-xdist); testmon keeps its selection across them
docker compose run --name "$TEST_CONTAINER_NAME" --rm app-tests pytest -n 4 --testmon
TEST_EXIT_CODE=$?

if [ $REBUILT -ne 0 ]; then
    log "Restarting persistent test container with new image."
    docker compose down app-tests
    docker compose up -d app-tests
fi

if [ $TEST_EXIT_CODE -ne 0 ]; then
    err "TESTS FAILED! (Exit code: $TEST_EXIT_CODE)"
    err "Deployment aborted. The running app is unchanged."
    exit 1
fi
log "Tests passed. Starting deployment..."

# --- STEPS 1-5: DEPLOYMENT (Build BEFORE Stop for minimal downtime) ---

export APP_VERSION=$(cat VERSION 2>/dev/null || echo "0.0")
export GIT_COMMIT=$(git rev-parse --short HEAD)
export BUILD_TIME=$(date -Iseconds)
log "Build: v${APP_VERSION} (${GIT_COMMIT}) @ ${BUILD_TIME}"

# 1. Build new image WHILE app is still running (= no downtime during build)
#    With the layer cache, unless --no-cache (T-013)
log "1. Building new image (app keeps running)..."
docker compose build $NO_CACHE app
BUILD_EXIT_CODE=$?
if [ $BUILD_EXIT_CODE -ne 0 ]; then
    err "BUILD FAILED! (Exit code: $BUILD_EXIT_CODE)"
    err "Deployment aborted. App continues running with old image."
    exit 1
fi

# 2. Stop the service (image is already built -> short downtime)
log "2. Stopping service 'app'..."
docker compose stop app

# 3. Remove the container
log "3. Removing container 'app'..."
docker compose rm -f app

# 4. Check for orphaned containers
log "4. Checking for orphaned containers..."
PROJECT_NAME=$(grep -E '^COMPOSE_PROJECT_NAME=' .env 2>/dev/null | cut -d= -f2 | tr -d '[:space:]')
PROJECT_NAME=${PROJECT_NAME:-$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]')}
ORPHANS=$(docker ps -aq \
  --filter "label=com.docker.compose.project=${PROJECT_NAME}" \
  --filter "label=com.docker.compose.service=app")

if [ -n "$ORPHANS" ]; then
    warn "Orphaned containers found. Force removing:"
    echo "$ORPHANS"
    docker rm -f $ORPHANS
else
    echo "No orphaned containers found. All clean."
fi

# 5. Start container with new image (db-backup is started alongside if missing)
log "5. Starting container with new image..."
docker compose up -d app db-backup

# 6. Verify: the running container must be healthy AND run the commit just built.
#    A container that came up from a stale image is a hard failure, not a warning.
log "6. Verifying deployment (expecting ${GIT_COMMIT})..."
elapsed=0
status="unknown"
while [ $elapsed -lt $HEALTH_TIMEOUT ]; do
    status=$(docker compose ps --format '{{.Health}}' app 2>/dev/null || echo "unknown")
    [ "$status" = "healthy" ] && break
    sleep $HEALTH_INTERVAL
    elapsed=$((elapsed + HEALTH_INTERVAL))
done
if [ "$status" != "healthy" ]; then
    err "App did NOT become healthy within ${HEALTH_TIMEOUT}s (status: ${status})."
    docker compose logs --tail=50 app
    exit 1
fi
RUNNING_COMMIT=$(docker compose exec -T app printenv GIT_COMMIT 2>/dev/null | tr -d '\r')
if [ "$RUNNING_COMMIT" != "$GIT_COMMIT" ]; then
    err "App runs '${RUNNING_COMMIT:-<none>}', expected '${GIT_COMMIT}'. Image was NOT rebuilt."
    exit 1
fi
log "Deployed v${APP_VERSION} (${GIT_COMMIT}), app is healthy."
# 7. Started from a terminal, the log viewer above now follows the logs (T-011); the pipeline shows none.
