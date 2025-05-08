from enum import Enum

from pydantic import BaseModel


class AgentEnum(str, Enum):
    self_written_agent = "self_written_agent"
    smollagents = "smollagents"
    pydantic_ai_agent = "pydantic_ai_agent"


class AgentQueryRequest(BaseModel):
    agent: AgentEnum
    query: str
