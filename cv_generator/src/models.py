from typing import Literal

import jinja2
from pydantic import BaseModel, Field

from cv_generator.config.config import PROJECT_ROOT, Path, settings


class CandidateInput(BaseModel):
    name: str = Field(..., description="Имя кандидата")
    desired_job: str = Field(..., description="Желаемая должность")
    years_of_experience: int = Field(..., description="Опыт работы в годах")
    location: str = Field(..., description="Местоположение")


class Experience(BaseModel):
    job_title: str = Field(..., description="Должность")
    company: str = Field(..., description="Компания")
    start_date: str = Field(..., description="Дата начала работы")
    end_date: str | None = Field(None, description="Дата окончания работы")
    achievements: list[str] | None = Field(None, description="Достижения расписанные по методике STAR")


class Education(BaseModel):
    degree: str | None = Field(None, description="Опционально степень (например, бакалавр, магистр и т.д.)")
    institution: str = Field(..., description="Учебное заведение")
    start_date: str = Field(..., description="Дата начала учебы")
    end_date: str | None = Field(None, description="Дата окончания учебы")
    details: str = Field(..., description="Cпециализация, (например: Машинное обучение)")


class Projects(BaseModel):
    name: str | None = Field(None, description="Название проекта")
    link: str | None = Field(None, description="Ссылка на проект")
    description: str | None = Field(None, description="Описание проекта")


class Contacts(BaseModel):
    phone: str = Field(..., description="Мобильный телефон")
    email: str = Field(..., description="Email")
    linkedin: str | None = Field(None, description="Опционально LinkedIn")
    github: str | None = Field(None, description="Опционально ссылка на Github")
    location: str = Field(..., description="Страна (например, Россия, Казахстан, Беларусь и прочие)")


class Resume(BaseModel):
    name: str = Field(..., description="ФИО")
    contact_info: Contacts = Field(..., description="Контактная информация, обращай внимание на должность!")
    gender: Literal["мужской", "женский"] = Field(..., description="Пол кандидата")
    title: str = Field(..., description="Желаемая должность")
    summary: str = Field(..., description="Краткое summary о себе")
    skills: list[str] | None = Field(None, description="Перечень навыков")
    experience: list[Experience] | None = Field(
        None, description="Опыт работы, придумай в соответствии с years_of_experience"
    )
    education: list[Education] = Field(None, description="Образование")
    languages: list[str] | None = Field(None, description="Языки, на которых говорит кандидат, опционально")
    certifications: list[str] | None = Field(None, description="Сертификаты, опционально")
    hobbies: list[str] | None = Field(None, description="Хобби, опционально")
    portfolio: list[Projects] | None = Field(None, description="Портфолио или примеры работ, опционально")


LATEX_ESCAPE_MAP = {
    "%": r"\%",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}

JOBS = [
    "AI Engineer",
    "Agile Coach",
    "Computational Scientist",
    "Algorithm Engineer",
    "Applied Scientist",
    "Automation QA",
    "Backend Developer",
    "Blockchain Developer",
    "Business Intelligence Analyst",
    "CDO",
    "CTO",
    "Cloud Engineer",
    "Cybersecurity Specialist",
    "Database Administrator",
    "Data Analyst",
    "Data Architect",
    "Data Engineer",
    "Data Quality Engineer",
    "Data Scientist",
    "Data Steward",
    "Computer Vision Engineer",
    "DevOps Engineer",
    "Developer",
    "Engineering Manager",
    "Firmware Engineer",
    "BI Developer",
    "Frontend Developer",
    "Full Stack Developer",
    "Head of Data",
    "Head of Engineering",
    "IT Project Manager",
    "Integration Engineer",
    "Interaction Designer",
    "MLOps Engineer",
    "Mobile Developer",
    "Embedded Systems Engineer",
    "Motion Designer",
    "NLP Engineer",
    "Network Engineer",
    "Platform Engineer",
    "Product Analyst",
    "Product Designer",
    "Product Manager",
    "Product Owner",
    "Project Manager",
    "QA Engineer",
    "Quantitative Analyst",
    "Research Scientist",
    "Researcher",
    "Scrum Master",
    "Security Engineer",
    "Site Reliability Engineer",
    "Software Engineer",
    "Solutions Architect",
    "System Analyst",
    "Technical Lead",
    "Tester",
    "UI Developer",
    "UX Researcher",
    "UX/UI Designer",
    "Machine Learning Engineer",
]

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(settings.latex_template_path).parent),
    comment_start_string="<%",
    comment_end_string="%>",
    autoescape=True,
)
latex_template = jinja_env.get_template(Path(settings.latex_template_path).name)

with (PROJECT_ROOT / settings.prompt_path).open(mode="r") as prompt:
    PROMPT_STRUCTURE = prompt.read()
