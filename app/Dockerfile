FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Application modules (add new files here!) ---
COPY main.py .
COPY database.py .
COPY utils.py .
COPY strings.py .

# --- Configuration ---
COPY pyproject.toml .
COPY pytest.ini .

# --- Templates & static assets ---
COPY templates ./templates

# --- Tests (available in image for CI; app-tests uses volume mount) ---
COPY tests ./tests

# Build-time version info
ARG APP_VERSION=0.0
ARG GIT_COMMIT=unknown
ARG BUILD_TIME=unknown
ENV APP_VERSION=$APP_VERSION
ENV GIT_COMMIT=$GIT_COMMIT
ENV BUILD_TIME=$BUILD_TIME

CMD ["python", "main.py"]
