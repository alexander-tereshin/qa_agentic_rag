import os

import requests
from dotenv import load_dotenv
from src.models import AgentQueryRequest

import streamlit as st


load_dotenv()


AGENT_HOST = os.getenv("AGENT_HOST")
AGENT_PORT = os.getenv("AGENT_PORT")
AGENT_API_URL = f"http://{AGENT_HOST}:{AGENT_PORT}/agent_query"


def display_conversation(history: list) -> None:
    """Display conversation history."""
    for entry in history:
        st.markdown(f"**Вы:** {entry['user']}")
        st.markdown(f"**Бот:** {entry['bot']}")


def clear_chat(chat_type: str) -> None:
    """Clear chat history based on chat type."""
    if chat_type == "agent":
        st.session_state.conversation_history_rag = []
    elif chat_type == "classification":
        st.session_state.conversation_history_classification = []
    elif chat_type == "retrieval":
        pass


def get_agent_response(request: AgentQueryRequest) -> str:
    headers = {"Content-Type": "application/json"}
    payload = request.model_dump()
    try:
        response = requests.post(AGENT_API_URL, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Error during API request: {e!s}"
    return data.get("response", "No answer.")


def agent_chat() -> None:
    st.markdown("### Agentic RAG")

    if "conversation_history_agentic_rag" not in st.session_state:
        st.session_state.conversation_history_agentic_rag = []

    query = st.chat_input("Введите Ваш запрос")

    if query:
        try:
            request = AgentQueryRequest(agent=st.session_state.selected_agent, query=query)
            answer = get_agent_response(request)

            st.session_state.conversation_history_agentic_rag.append({"user": query, "bot": answer})
            display_conversation(st.session_state.conversation_history_agentic_rag)

        except Exception as e:  # noqa: BLE001
            st.write(f"Ошибка: {e}")

    if st.session_state.conversation_history_agentic_rag and st.button("Очистить чат :wastebasket:"):
        clear_chat("agent")
