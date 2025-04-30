from fastapi import FastAPI, HTTPException

from agent.src.logger import setup_logging
from agent.src.models import AgentQueryRequest
from agent.src.pydantic_ai_agent import pydantic_ai_agent
from agent.src.smolagent_agent import smolagent_agent


logger = setup_logging()
app = FastAPI()


@app.get("/", tags=["Root"])
async def root() -> dict:
    return {"message": "Welcome to the Agent API!"}


@app.post("/agent_query")
async def agent_query(request: AgentQueryRequest) -> None:
    try:
        if request.agent == "smollagents":
            result = smolagent_agent.run(request.query)
        elif request.agent == "pydantic_ai_agent":
            result = await pydantic_ai_agent.run(request.query)
            result = result.output

    except TimeoutError as err:
        raise HTTPException(status_code=504, detail="The request to the agent timed out.") from err
    return {"response": result}


@app.get("/healthcheck", tags=["Health"])
async def healthcheck() -> dict:
    return {"status": "healthy"}
