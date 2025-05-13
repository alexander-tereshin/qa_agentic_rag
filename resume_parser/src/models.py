from typing import Literal

from pydantic import BaseModel, Field

from resume_parser.config.config import PROJECT_ROOT, settings


class Experience(BaseModel):
    job_title: str = Field(..., description="Должность")
    company: str = Field(..., description="Компания")
    start_date: str = Field(..., description="Дата начала работы")
    end_date: str | None = Field(None, description="Дата окончания работы")
    achievements: list[str] | None = Field(None, description="Достижения на рабочем месте, если указаны")


class Education(BaseModel):
    degree: str | None = Field(None, description="Степень (например, бакалавр, магистр и т.д.), если указаны")
    institution: str = Field(..., description="Учебное заведение")
    start_date: str = Field(..., description="Дата начала учебы")
    end_date: str | None = Field(None, description="Дата окончания учебы")
    details: str = Field(..., description="Cпециализация, (например: Машинное обучение)")


class Projects(BaseModel):
    name: str | None = Field(None, description="Название проекта, если указаны")
    link: str | None = Field(None, description="Ссылка на проект, если указаны")
    description: str | None = Field(None, description="Описание проекта, если указаны")


class Contacts(BaseModel):
    phone: str = Field(..., description="Мобильный телефон")
    email: str = Field(..., description="Email")
    linkedin: str | None = Field(None, description="Опционально LinkedIn")
    github: str | None = Field(None, description="Опционально ссылка на Github")
    location: str = Field(..., description="Страна (например, Россия, Казахстан, Беларусь и прочие)")


class Resume(BaseModel):
    name: str = Field(..., description="ФИО")
    contact_info: Contacts = Field(..., description="Контактная информация")
    gender: Literal["мужской", "женский"] = Field(..., description="Пол кандидата")
    title: str | None = Field(..., description="Желаемая должность, если указано")
    summary: str | None = Field(..., description="Краткое summary о себе, если указано")
    skills: list[str] | None = Field(None, description="Перечень навыков, если указаны")
    experience: list[Experience] | None = Field(
        None, description="Опыт работы, придумай в соответствии с years_of_experience"
    )
    education: list[Education] = Field(None, description="Образование")
    languages: list[str] | None = Field(None, description="Языки, на которых говорит кандидат, если указаны")
    certifications: list[str] | None = Field(None, description="Сертификаты, если указаны")
    hobbies: list[str] | None = Field(None, description="Хобби, если указаны")
    portfolio: list[Projects] | None = Field(None, description="Портфолио или примеры работ, если указаны")


with (PROJECT_ROOT / settings.prompt_path).open(mode="r") as prompt:
    SYSTEM_PROMPT = prompt.read()
