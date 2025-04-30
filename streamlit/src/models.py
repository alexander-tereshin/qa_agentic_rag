from enum import Enum

from pydantic import BaseModel


class AgentEnum(str, Enum):
    mcp = "mcp"
    smollagents = "smollagents"
    pydantic_ai_agent = "pydantic_ai_agent"


class AgentQueryRequest(BaseModel):
    agent: AgentEnum
    query: str
