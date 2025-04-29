import os

import requests
from dotenv import load_dotenv


load_dotenv()


AGENT_API_HOST = os.getenv("AGENT_API_HOST", "agent")
AGENT_API_PORT = os.getenv("AGENT_API_PORT", "8001")

AGENT_API_URL = f"http://{AGENT_API_HOST}:{AGENT_API_PORT}/agent_query"


def get_bot_response(query: str) -> str:
    url = AGENT_API_URL
    headers = {"Content-Type": "application/json"}
    payload = {"query": query}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Error during API request: {e!s}"

    return data.get("response", "No answer.")
