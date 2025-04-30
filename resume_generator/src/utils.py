import asyncio
import json
import logging
import random
import re
import subprocess
from collections.abc import AsyncGenerator

from faker import Faker
from openai import AsyncOpenAI

from resume_generator.config.config import CV_DIR, JSON_DIR, LATEX_DIR, Path, settings
from resume_generator.src.models import JOBS, LATEX_ESCAPE_MAP, PROMPT_STRUCTURE, BaseModel, Resume, latex_template


fake = Faker(locale="ru_RU")


def escape_string(text: str | None) -> str | None:
    if not text:
        return text
    text = re.sub(r"[\"']", "", text)
    for char, replacement in LATEX_ESCAPE_MAP.items():
        text = text.replace(char, replacement)
    return text


def escape_all_strings(obj: any) -> any:
    if isinstance(obj, str):
        return escape_string(obj)
    if isinstance(obj, list):
        return [escape_all_strings(item) for item in obj]
    if isinstance(obj, dict):
        return {k: escape_all_strings(v) for k, v in obj.items()}
    if isinstance(obj, BaseModel):
        return escape_all_strings(obj.model_dump())
    return obj


async def generate_random_resumes(limit: int) -> AsyncGenerator[dict]:
    count = 0
    while count < limit:
        yield {
            "name": fake.name(),
            "phone_number": fake.phone_number(),
            "desired_job": random.choice(JOBS),  # noqa: S311
            "years_of_experience": random.randint(0, 15),  # noqa: S311
            "location": fake.country(),
        }
        await asyncio.sleep(0)
        count += 1


async def prompts_generator(resume_gen: AsyncGenerator[dict]) -> AsyncGenerator[str]:
    async for resume in resume_gen:
        yield PROMPT_STRUCTURE.format(candidate=resume)
        await asyncio.sleep(0)


def save_resume_to_json(resume: Resume) -> Path:
    position = "_".join(resume.title.lower().split())
    candidate_name = "_".join(resume.name.lower().split())
    filename = f"{candidate_name}_{position}.json"
    path = JSON_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(resume.model_dump(), f, ensure_ascii=False, indent=4)
    return path


def clean_cv_folder(cv_dir: Path = CV_DIR) -> None:
    for file in cv_dir.iterdir():
        if file.suffix != ".pdf":
            file.unlink()


async def compile_latex(latex_file_path: Path) -> None:
    await asyncio.to_thread(
        subprocess.run,
        [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={CV_DIR}",
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
        retry_delay = settings.retry_delay
        prompt = await queue.get()
        if prompt is None:
            queue.task_done()
            break
        task_name = asyncio.current_task().get_name()
        retries = 0
        while retries < settings.max_retries:
            try:
                logger.debug(f"[PROMPT] {prompt}")
                completion = await llm_api_client.beta.chat.completions.parse(
                    model=settings.llm_api_model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Твоя задача создать структурированный вывод согласно заданной схеме.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.15,
                    response_format=Resume,
                )
                response = completion.choices[0].message.parsed

                if not response:
                    logger.warning(f"[{task_name}] Received empty answer for prompt: {prompt}")
                    continue

                logger.info(f"[{task_name}] Response received")

                json_path = save_resume_to_json(response)
                logger.info(f"[{task_name}] JSON saved: {json_path}")

                resume = escape_all_strings(response)
                tex_path = LATEX_DIR / f"{Path(json_path).stem}.tex"
                pdf_path = CV_DIR / tex_path.with_suffix(".pdf").name

                output = latex_template.render(resume)
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
                retry_delay = min(retry_delay * 2, settings.max_retry_delay)
                retries += 1

        if retries >= settings.max_retries:
            logger.error(f"[{task_name}] Max retries reached. Skipping this generation.")

        queue.task_done()


async def generate_resume_task(
    n: int,
    logger: logging.Logger,
) -> None:
    logger.info(f"Received request to generate {n} resumes")

    llm_api_client = AsyncOpenAI(base_url=settings.llm_api_url, api_key=settings.llm_api_token.get_secret_value())
    queue = asyncio.Queue(settings.workers_num * 2)

    workers = [
        asyncio.create_task(
            generate_and_save_resume(
                llm_api_client=llm_api_client,
                queue=queue,
                logger=logger,
            )
        )
        for _ in range(settings.workers_num)
    ]
    logger.info(f"Spawning {settings.workers_num} workers")

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
