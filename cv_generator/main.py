import asyncio
from typing import Annotated

from fastapi import FastAPI, Query

from cv_generator.src import utils
from cv_generator.src.logger import setup_logging


logger = setup_logging()
app = FastAPI()

logger.info("Starting the application.")


@app.get("/", tags=["Root"])
async def root() -> dict:
    return {"message": "Welcome to the Resume Generation API!"}


@app.get("/healthcheck", tags=["Health"])
async def healthcheck() -> dict:
    return {"status": "healthy"}


@app.get("/generate", tags=["Generation"])
async def generate_resumes(n: Annotated[int, Query(description="Number of resumes to generate")] = ...) -> dict:
    logger.info(f"Received request to generate {n} resumes")
    asyncio.create_task(utils.generate_resume_task(n, logger))  # noqa: RUF006
    return {"status": "started", "message": f"Generation of {n} resumes started"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("cv_generator.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104
