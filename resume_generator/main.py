import asyncio
from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from resume_generator.src import utils
from resume_generator.src.logger import setup_logging
from resume_generator.src.models import CandidateInput


logger = setup_logging()
app = FastAPI()

logger.info("Starting the application.")


@app.get("/", tags=["Root"])
async def root() -> dict:
    return {"message": "Welcome to the Resume Generation API!"}


@app.get("/healthcheck", tags=["Health"])
async def healthcheck() -> dict:
    return {"status": "healthy"}


@app.get("/generate_random_resume", tags=["Generation"])
async def generate_resumes(n: Annotated[int, Query(description="Number of resumes to generate")] = ...) -> dict:
    logger.info(f"Received request to generate {n} resumes")
    asyncio.create_task(utils.generate_random_resume_task(n, logger))  # noqa: RUF006
    return {"status": "started", "message": f"Generation of {n} resumes started"}


@app.post("/generate_resume", tags=["Generation"])
async def generate_resume(candidate: CandidateInput) -> dict:
    logger.info(f"Received request to generate resume for {candidate.name}")

    try:
        pdf_filename, resume_json = await utils.generate_resume(logger, candidate.model_dump())
    except Exception as e:
        logger.exception("Ошибка генерации резюме")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Ошибка генерации: {e!s}"},
        )
    utils.insert_resumes_to_db(resume=resume_json, logger=logger)
    return {
        "status": "success",
        "message": f"Резюме успешно сгенерировано для {candidate.name}",
        "pdf_filename": pdf_filename,
    }
