FROM python:3.13

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ca-certificates\
    && apt-get clean

RUN update-ca-certificates

COPY --from=ghcr.io/astral-sh/uv:latest  /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --frozen

COPY agent agent

ENTRYPOINT ["uv", "run"]

CMD ["uvicorn", "agent.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
