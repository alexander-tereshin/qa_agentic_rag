FROM python:3.13-slim

WORKDIR /app

RUN set -ex && \
    apt update && \
    apt install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --frozen

COPY agent/ agent/
