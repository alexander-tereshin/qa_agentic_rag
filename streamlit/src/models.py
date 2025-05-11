from enum import Enum

from pydantic import BaseModel


class AgentEnum(str, Enum):
    self_written_agent = "self_written_agent"
    smollagents = "smollagents"
    pydantic_ai_agent = "pydantic_ai_agent"


class AgentQueryRequest(BaseModel):
    agent: AgentEnum
    query: str


class CandidateInput(BaseModel):
    name: str
    desired_job: str
    years_of_experience: int
    location: str


CITIES = [
    "Москва",
    "Санкт-Петербург",
    "Новосибирск",
    "Екатеринбург",
    "Казань",
    "Нижний Новгород",
    "Челябинск",
    "Самара",
]

SPECIALIZATIONS = [
    "Data Engineer",
    "Developer",
    "Business Expert",
    "System Analyst",
    "Data Scientist",
    "Support Engineer",
    "Technical Lead",
    "Agile Expert",
    "UX/UI Designer",
    "Tester",
    "Product Owner",
    "Software Engineer",
    "Data Analyst",
    "Researcher",
    "Software Architect",
    "Process Lead",
    "Data Steward",
    "Специалист по охране труда",
    "Product Analyst",
    "Контент-менеджер",
    "Руководитель",
    "Кредитный эксперт",
    "специалист по расчету заработной платы",
    "Ассистент",
    "Кассир-контролер",
    "Графический дизайнер",
    "Продуктовый редактор",
    "Юрист",
    "Менеджер проектов",
    "Менеджер по продажам",
    "Менеджер поддержки клиентов",
    "Менеджер по развитию ипотечного бизнеса",
]
