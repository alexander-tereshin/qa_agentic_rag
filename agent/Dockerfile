FROM python:3.13

WORKDIR /app

RUN apt-get update && apt-get install -y 

COPY --from=ghcr.io/astral-sh/uv:latest  /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --frozen

COPY agent agent