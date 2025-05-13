import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile

from resume_parser.src.logger import setup_logging
from resume_parser.src.resume_parser import ResumeParser
from resume_parser.src.utils import insert_resumes_to_db


logger = setup_logging()
parser = ResumeParser(logger)
app = FastAPI()

logger.info("Starting the application.")


@app.get("/", tags=["Root"])
async def root() -> dict:
    return {"message": "Welcome to the Resume Parser API!"}


@app.get("/healthcheck", tags=["Health"])
async def healthcheck() -> dict:
    return {"status": "healthy"}


@app.post("/parse_resume", tags=["Parsing"])
async def parse_resume(file: Annotated[UploadFile, File()] = ...) -> dict:
    logger.info(f"Получен файл: {file.filename}")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        parsed_data = await parser.parse_resume(tmp_path)
        parsed_resume = parsed_data.model_dump()
        insert_resumes_to_db([parsed_resume], logger)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    finally:
        # If an error occurred, delete the temporary file
        if parsed_resume == {} and Path(tmp_path).exists():
            Path(tmp_path).unlink()

    return parsed_resume


@app.post("/parse_resumes_batch", tags=["Parsing"])
async def parse_resumes_batch(files: Annotated[list[UploadFile], File()] = ...) -> dict:
    logger.info(f"Получено файлов: {[file.filename for file in files]}")

    parsed_models = []
    response_payload = []
    has_error = False

    for file in files:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(await file.read())
                tmp_path = tmp.name

            parsed_data = await parser.parse_resume(tmp_path)
            parsed_resume = parsed_data.model_dump()
            parsed_models.append(parsed_resume)
            response_payload.append(parsed_resume.model_dump())

        except Exception as e:
            logger.exception(f"Ошибка при обработке файла: {file.filename}")
            has_error = True
            response_payload.append({"filename": file.filename, "error": str(e)})

        finally:
            # If an error occurred, delete the temporary file
            if parsed_resume == {} and Path(tmp_path).exists():
                Path(tmp_path).unlink()

    if parsed_models:
        insert_resumes_to_db(parsed_models, logger)

    if has_error:
        raise HTTPException(status_code=500, detail={"results": response_payload})

    return {"results": response_payload}
