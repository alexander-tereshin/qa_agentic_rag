import asyncio
import json
import logging
import random
import re
import subprocess
from collections.abc import AsyncGenerator
from pathlib import Path

import psycopg2
from faker import Faker
from openai import AsyncOpenAI

from resume_generator.config import config
from resume_generator.src import models


fake = Faker(locale="ru_RU")


db_params = {
    "host": config.settings.postgres_host,
    "port": config.settings.postgres_port,
    "database": config.settings.postgres_db,
    "user": config.settings.postgres_user,
    "password": config.settings.postgres_password.get_secret_value(),
}


def escape_string(text: str | None) -> str | None:
    if not text:
        return text
    text = re.sub(r"[\"']", "", text)
    for char, replacement in models.LATEX_ESCAPE_MAP.items():
        text = text.replace(char, replacement)
    return text


def escape_all_strings(obj: any) -> any:
    if isinstance(obj, str):
        return escape_string(obj)
    if isinstance(obj, list):
        return [escape_all_strings(item) for item in obj]
    if isinstance(obj, dict):
        return {k: escape_all_strings(v) for k, v in obj.items()}
    if isinstance(obj, models.BaseModel):
        return escape_all_strings(obj.model_dump())
    return obj


async def generate_random_resumes(limit: int) -> AsyncGenerator[dict]:
    count = 0
    while count < limit:
        yield {
            "name": fake.name(),
            "phone_number": fake.phone_number(),
            "desired_job": random.choice(models.JOBS),  # noqa: S311
            "years_of_experience": random.randint(0, 15),  # noqa: S311
            "location": fake.country(),
        }
        await asyncio.sleep(0)
        count += 1


async def prompts_generator(resume_gen: AsyncGenerator[dict]) -> AsyncGenerator[str]:
    async for resume in resume_gen:
        yield models.PROMPT_STRUCTURE.format(candidate=resume)
        await asyncio.sleep(0)


def save_resume_to_json(resume: models.Resume) -> Path:
    position = "_".join(resume.title.lower().split())
    candidate_name = "_".join(resume.name.lower().split())
    filename = f"{candidate_name}_{position}.json"
    path = config.JSON_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(resume.model_dump(), f, ensure_ascii=False, indent=4)
    return path


def clean_cv_folder(cv_dir: Path = config.CV_DIR) -> None:
    for file in cv_dir.iterdir():
        if file.suffix != ".pdf":
            file.unlink()


async def compile_latex(latex_file_path: Path) -> None:
    await asyncio.to_thread(
        subprocess.run,
        [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={config.CV_DIR}",
            str(latex_file_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


async def generate_and_save_resume(
    llm_api_client: AsyncOpenAI,
    logger: logging.Logger,
    queue: asyncio.Queue,
) -> None:
    while True:
        retry_delay = config.settings.retry_delay
        prompt = await queue.get()
        if prompt is None:
            queue.task_done()
            break
        task_name = asyncio.current_task().get_name()
        retries = 0
        while retries < config.settings.max_retries:
            try:
                logger.debug(f"[PROMPT] {prompt}")
                completion = await llm_api_client.beta.chat.completions.parse(
                    model=config.settings.llm_api_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Твоя задача создать структурированный вывод согласно заданной схеме.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.15,
                    response_format=models.Resume,
                )
                response = completion.choices[0].message.parsed

                if not response:
                    logger.warning(f"[{task_name}] Received empty answer for prompt: {prompt}")
                    continue

                logger.info(f"[{task_name}] Response received")

                json_path = save_resume_to_json(response)
                logger.info(f"[{task_name}] JSON saved: {json_path}")

                resume = escape_all_strings(response)
                tex_path = config.LATEX_DIR / f"{Path(json_path).stem}.tex"
                pdf_path = config.CV_DIR / tex_path.with_suffix(".pdf").name

                output = models.latex_template.render(resume)
                await asyncio.to_thread(tex_path.write_text, output, encoding="utf-8")
                logger.info(f"[{task_name}] LaTeX saved: {tex_path}")

                await compile_latex(tex_path)
                logger.info(f"[{task_name}] PDF compiled: {pdf_path}")
                break

            except subprocess.CalledProcessError:
                logger.exception(f"[{task_name}] LaTeX compilation error")
            except Exception as e:
                logger.exception(f"[{task_name}] Generating resume error", exc_info=e)
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, config.settings.max_retry_delay)
                retries += 1

        if retries >= config.settings.max_retries:
            logger.error(f"[{task_name}] Max retries reached. Skipping this generation.")

        queue.task_done()


async def generate_random_resume_task(
    n: int,
    logger: logging.Logger,
) -> None:
    logger.info(f"Received request to generate {n} resumes")

    llm_api_client = AsyncOpenAI(
        base_url=config.settings.llm_api_url, api_key=config.settings.llm_api_token.get_secret_value()
    )
    queue = asyncio.Queue(config.settings.workers_num * 2)

    workers = [
        asyncio.create_task(
            generate_and_save_resume(
                llm_api_client=llm_api_client,
                queue=queue,
                logger=logger,
            )
        )
        for _ in range(config.settings.workers_num)
    ]
    logger.info(f"Spawning {config.settings.workers_num} workers")

    async def enqueue_prompts() -> None:
        async for prompt in prompts_generator(generate_random_resumes(n)):
            await queue.put(prompt)
        for _ in workers:
            await queue.put(None)

    await enqueue_prompts()
    await queue.join()
    await asyncio.gather(*workers)

    clean_cv_folder()
    logger.info("Temp files cleaned")


async def generate_resume(logger: logging.Logger, candidate_data: dict) -> str | None:
    logger.info("Starting resume generation")
    llm_api_client = AsyncOpenAI(
        base_url=config.settings.llm_api_url, api_key=config.settings.llm_api_token.get_secret_value()
    )
    candidate = json.dumps(candidate_data, ensure_ascii=False)

    prompt = f"""
    Заполни структурированное резюме по следующему кандидату: {models.PROMPT_STRUCTURE.format(candidate=candidate)}.
    """

    logger.debug(f"[PROMPT] {prompt}")

    try:
        completion = await llm_api_client.beta.chat.completions.parse(
            model=config.settings.llm_api_model,
            messages=[
                {"role": "system", "content": "Твоя задача — создать структурированный вывод согласно заданной схеме."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.15,
            response_format=models.Resume,
        )
        response = completion.choices[0].message.parsed

        if not response:
            logger.warning("Received empty response")
            return None

        logger.info("Response received from LLM")

        json_path = save_resume_to_json(response)
        logger.info(f"Saved resume JSON: {json_path}")

        resume = escape_all_strings(response)
        tex_path = config.LATEX_DIR / f"{json_path.stem}.tex"
        pdf_path = config.CV_DIR / tex_path.with_suffix(".pdf").name

        tex_output = models.latex_template.render(resume)
        await asyncio.to_thread(tex_path.write_text, tex_output, encoding="utf-8")
        logger.info(f"LaTeX file saved: {tex_path}")

        await compile_latex(tex_path)
        logger.info(f"PDF compiled: {pdf_path}")

    except subprocess.CalledProcessError:
        logger.exception("LaTeX compilation error")
    except Exception as e:
        logger.exception("Error generating resume", exc_info=e)

    return pdf_path.name, response.model_dump()


def resume_to_sql_values(resume: dict) -> tuple:
    return (
        resume.get("name"),
        resume.get("gender"),
        resume.get("title"),
        resume.get("summary"),
        json.dumps(resume.get("contact_info")),
        resume.get("skills"),
        json.dumps(resume.get("experience")),
        json.dumps(resume.get("education")),
        resume.get("languages"),
        resume.get("certifications"),
        resume.get("hobbies"),
        json.dumps(resume.get("portfolio")),
    )


def insert_resumes_to_db(resume: dict, logger: logging.Logger) -> None:
    insert_query = """
    INSERT INTO resumes (
        name, gender, title, summary, contact_info,
        skills, experience, education,
        languages, certifications, hobbies, portfolio
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with psycopg2.connect(**db_params) as conn, conn.cursor() as cursor:
            try:
                cursor.execute(insert_query, resume_to_sql_values(resume))
                logger.info(f"Resume for '{resume.get('name')}' inserted into database successfully.")
            except Exception:
                conn.rollback()
                logger.exception(f"Error inserting resume {resume.name}")
            conn.commit()
    except Exception:
        logger.exception("Failed to connect to the database")
