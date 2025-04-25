import os

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools
from dotenv import load_dotenv


load_dotenv()


host = os.environ["POSTGRES_HOST"]
port = os.environ["POSTGRES_PORT"]
database = os.environ["POSTGRES_DB"]
user = os.environ["POSTGRES_USER"]
password = os.environ["POSTGRES_PASSWORD"]

database_uri = f"postgresql://{user}:{password}@{host}:{port}/{database}"


async def setup_team() -> (RoundRobinGroupChat, OllamaChatCompletionClient):
    server_params = StdioServerParams(
        command="uv",
        args=[
            "run",
            "postgres-mcp",
            "--access-mode=unrestricted",
        ],
        env={"DATABASE_URI": database_uri},
    )

    tools = await mcp_server_tools(server_params)

    model_client = OllamaChatCompletionClient(
        model=os.environ["LLM_API_MODEL"],
        host=os.environ["OLLAMA_HOST"],
    )

    assistant = AssistantAgent(
        name="assistant",
        model_client=model_client,
        tools=tools,
        system_message="You are a helpful assistant.",
    )

    termination_condition = TextMessageTermination("assistant")

    team = RoundRobinGroupChat(
        [assistant],
        termination_condition=termination_condition,
    )

    return team, model_client
