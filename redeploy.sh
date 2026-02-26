#!/bin/bash

# Colors for readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}--- Redeploy Script ---${NC}"

# --- STEP 0: PRE-FLIGHT TESTS ---
TIMESTAMP=$(date +%s)
TEST_CONTAINER_NAME="test_run_${TIMESTAMP}"
REBUILT=0

echo -e "${YELLOW}0. Running tests (testmon: only affected tests)...${NC}"
echo -e "   Container name: ${TEST_CONTAINER_NAME}"

# Only rebuild image if requirements.txt changed (source comes via volume mount)
REQ_HASH_FILE="app/.requirements_hash"
REQ_HASH_CURRENT=$(md5sum app/requirements.txt | cut -d' ' -f1)
REQ_HASH_SAVED=$(cat "$REQ_HASH_FILE" 2>/dev/null || echo "")

if [ "$REQ_HASH_CURRENT" != "$REQ_HASH_SAVED" ]; then
    echo -e "${YELLOW}   requirements.txt changed → rebuilding app-tests image...${NC}"
    docker compose build app-tests
    echo "$REQ_HASH_CURRENT" > "$REQ_HASH_FILE"
    REBUILT=1
fi

docker compose run --name "$TEST_CONTAINER_NAME" --rm app-tests pytest --testmon

TEST_EXIT_CODE=$?

if [ $REBUILT -ne 0 ]; then
    echo -e "Restarting persistent test container with new image."
    docker compose down app-tests
    docker compose up -d app-tests
fi

if [ $TEST_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}TESTS FAILED! (Exit code: $TEST_EXIT_CODE)${NC}"
    echo -e "${RED}Deployment aborted. Please fix the code.${NC}"
    exit 1
else
    echo -e "${GREEN}Tests passed. Starting deployment...${NC}"
fi

# --- STEPS 1-5: DEPLOYMENT (Build BEFORE Stop for minimal downtime) ---

# Set version info for build
export APP_VERSION=$(cat VERSION 2>/dev/null || echo "0.0")
export GIT_COMMIT=$(git rev-parse --short HEAD)
export BUILD_TIME=$(date -Iseconds)
echo -e "${GREEN}Build: v${APP_VERSION} (${GIT_COMMIT}) @ ${BUILD_TIME}${NC}"

# 1. Build new image WHILE app is still running (= no downtime during build)
echo -e "${GREEN}1. Building new image (app keeps running)...${NC}"
docker compose build --no-cache app

BUILD_EXIT_CODE=$?
if [ $BUILD_EXIT_CODE -ne 0 ]; then
    echo -e "${RED}BUILD FAILED! (Exit code: $BUILD_EXIT_CODE)${NC}"
    echo -e "${RED}Deployment aborted. App continues running with old image.${NC}"
    exit 1
fi

# 2. Stop the service (image is already built → short downtime)
echo -e "${GREEN}2. Stopping service 'app'...${NC}"
docker compose stop app

# 3. Remove the container
echo -e "${GREEN}3. Removing container 'app'...${NC}"
docker compose rm -f app

# 4. Check for orphaned containers
echo -e "${GREEN}4. Checking for orphaned containers...${NC}"
PROJECT_NAME=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]')
ORPHANS=$(docker ps -aq \
  --filter "label=com.docker.compose.project=${PROJECT_NAME}" \
  --filter "label=com.docker.compose.service=app")

if [ -n "$ORPHANS" ]; then
    echo -e "${RED}Orphaned containers found. Force removing:${NC}"
    echo "$ORPHANS"
    docker rm -f $ORPHANS
else
    echo "No orphaned containers found. All clean."
fi

# 5. Start container with new image
echo -e "${GREEN}5. Starting container with new image...${NC}"
docker compose up -d app

# 6. Show logs
echo -e "${GREEN}6. Done! Showing logs (press Ctrl+C to exit):${NC}"
docker compose logs -f app 2>&1
