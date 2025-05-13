import logging
import re
import typing

import pymupdf
from openai import AsyncOpenAI

from resume_parser.config.config import Path, settings
from resume_parser.src.models import SYSTEM_PROMPT, Resume


class ResumeParser:
    def __init__(self, logger: logging.Logger) -> None:
        self.llm_client = AsyncOpenAI(base_url=settings.llm_api_url, api_key=settings.llm_api_token.get_secret_value())
        self.logger = logger

    def extract_text_from_pdf(self, file_path: str | Path) -> str:
        try:
            doc = pymupdf.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return self._preprocess_text(text)

        except Exception:
            self.logger.exception(f"Ошибка при извлечении текста из PDF {file_path}: ")
            raise

    def _preprocess_resume_text(self, text: str, max_length: int = 8000) -> str:
        if len(text) <= max_length:
            return text

        self.logger.info(f"Резюме слишком большое ({len(text)} символов), сокращаем до {max_length} символов")

        beginning: typing.Final = text[: int(max_length * 0.3)]

        middle_start: typing.Final = int(len(text) * 0.3)
        middle_length: typing.Final = int(max_length * 0.5)
        middle: typing.Final = text[middle_start : middle_start + middle_length]

        end_start: typing.Final = max(0, len(text) - int(max_length * 0.2))
        end: typing.Final = text[end_start:]

        processed_text: typing.Final = (
            beginning + "\n...[Текст резюме сокращен]...\n" + middle + "\n...[Текст резюме сокращен]...\n" + end
        )

        if len(processed_text) > max_length:
            return processed_text[:max_length]

        return processed_text

    def _preprocess_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]", "", text)
        text = re.sub(r"([^\w\s])\1+", r"\1", text)
        return text.strip()

    def _raise_if_too_short(self, text: str) -> None:
        if len(text) < settings.allowed_min_len_resume:
            self.logger.warning(f"Извлеченный текст слишком короткий: {text[:50]}...")
            raise ValueError("Извлеченный текст слишком короткий для парсинга резюме")

    async def parse_resume(self, file_path: str | Path) -> list[Resume]:
        try:
            resume_text = self.extract_text_from_pdf(file_path)
            self._raise_if_too_short(resume_text)

            user_prompt = f"""
            Вот текст резюме:\n{resume_text}\n
            Извлеки всю доступную информацию и верни ее в структурированном виде.
            """

            completion = await self.llm_client.beta.chat.completions.parse(
                model=settings.llm_api_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.15,
                response_format=Resume,
            )
            structured_data = completion.choices[0].message.parsed

        except Exception:
            self.logger.exception(f"Ошибка при парсинге резюме {file_path}")
            raise

        return structured_data

    async def batch_parse_resumes(self, directory_path: str | Path) -> list[Resume]:
        directory: typing.Final = Path(directory_path)

        if not directory.is_dir():
            raise ValueError(f"Директория {directory} не существует")

        pdf_files: typing.Final = list(directory.glob("*.pdf"))
        self.logger.info(f"Найдено {len(pdf_files)} PDF-файлов в директории {directory}")

        resume_data_list: typing.Final = []
        for pdf_file in pdf_files:
            try:
                self.logger.info(f"Парсинг файла: {pdf_file}")
                resume_data = await self.parse_resume(pdf_file)
                resume_data_list.append(resume_data)
                self.logger.info(f"Успешно распарсено резюме: {resume_data.name}")
            except Exception:
                self.logger.exception(f"Ошибка при парсинге {pdf_file}")
                continue

        self.logger.info(f"Всего успешно обработано {len(resume_data_list)} из {len(pdf_files)} PDF-файлов")
        return resume_data_list
