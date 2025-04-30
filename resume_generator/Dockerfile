FROM python:3.13-slim

WORKDIR /app

RUN set -ex \
    && apt update \
    && apt install -y --no-install-recommends \
        ca-certificates\
        curl\
        texlive-xetex \
        texlive-latex-extra \
        texlive-fonts-recommended \
        texlive-lang-cyrillic \
        texlive-latex-recommended \
        latexmk \
        fontconfig \
    && apt autoremove -y \
    && apt clean\
    && rm -rf /var/lib/apt/lists/*

RUN update-ca-certificates

COPY --from=ghcr.io/astral-sh/uv:latest  /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --frozen

COPY resume_generator resume_generator
