from fastapi import FastAPI, HTTPException

from agent.src.logger import setup_logging
from agent.src.models import AgentQueryRequest
from agent.src.utils import agent


logger = setup_logging()
app = FastAPI()


@app.post("/agent_query")
async def agent_query(request: AgentQueryRequest) -> None:
    try:
        result = await agent.run(request.query)
    except TimeoutError as err:
        raise HTTPException(status_code=504, detail="The request to the agent timed out.") from err
    return {"response": result}


@app.get("/healthcheck", tags=["Health"])
async def healthcheck() -> dict:
    return {"status": "healthy"}
