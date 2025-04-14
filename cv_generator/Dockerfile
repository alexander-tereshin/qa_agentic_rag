FROM python:3.13
SHELL ["/bin/sh", "-exc"]
WORKDIR /app

RUN apt-get update && apt-get install -y \
    ca-certificates\
    curl\
    texlive-xetex \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-lang-cyrillic \
    texlive-latex-recommended \
    latexmk \
    fontconfig \
    && apt-get clean
RUN update-ca-certificates
COPY --from=ghcr.io/astral-sh/uv:latest  /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev --frozen

COPY cv_generator cv_generator

ENTRYPOINT ["uv", "run"]
CMD ["uvicorn", "src.cv_generator.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
