from pydantic import BaseModel


class AgentQueryRequest(BaseModel):
    query: str
