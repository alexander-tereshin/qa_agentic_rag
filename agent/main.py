from collections.abc import AsyncGenerator

from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.ollama import OllamaChatCompletionClient
from fastapi import FastAPI
from pydantic import BaseModel

from agent.src import utils
from agent.src.logger import setup_logging
from agent.src.models import AgentQueryRequest


logger = setup_logging()
app = FastAPI()

team: None | RoundRobinGroupChat = None
model_client: None | OllamaChatCompletionClient = None


class TaskRequest(BaseModel):
    task: str


@app.on_event("startup")
async def startup_event() -> None:
    global team, model_client
    logger.info("Starting up and initializing team...")
    team, model_client = await utils.setup_team()
    logger.info("Team initialized successfully.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    if model_client:
        await model_client.close()


@app.post("/agent_query")
async def agent_query(payload: AgentQueryRequest) -> None:
    async def stream_results() -> AsyncGenerator[str]:
        full_response = ""
        async for message in team.run_stream(task=payload.query):
            logger.info(f"Received query: {payload.query}")
            full_response += message
        return {"response": full_response}


@app.get("/healthcheck", tags=["Health"])
async def healthcheck() -> dict:
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("agent.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104
