import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.ollama import OllamaChatCompletionClient
from autogen_ext.tools.mcp import StdioServerParams, mcp_server_tools


async def main() -> None:
    postgres_mcp_config = {
        "command": "uv",
        "args": [
            "run",
            "postgres-mcp",
            "--access-mode=unrestricted",
        ],
        "env": {"DATABASE_URI": "postgresql://user:password@127.0.0.1:5432/hr_base_qa_db"},
    }

    server_params = StdioServerParams(
        command="uv",
        args=postgres_mcp_config["args"],
        env=postgres_mcp_config["env"],
    )

    tools = await mcp_server_tools(server_params)

    model_client = OllamaChatCompletionClient(
        model="qwen2.5:latest",
    )

    looped_assistant = AssistantAgent(
        name="looped_assistant",
        model_client=model_client,
        tools=tools,
        system_message="You are a helpful translation assistant.",
    )

    termination_condition = TextMessageTermination("looped_assistant")

    team = RoundRobinGroupChat(
        [looped_assistant],
        termination_condition=termination_condition,
    )
    async for _message in team.run_stream(task="""создай таблицу test с полями id, name и age."""):
        pass

    await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
