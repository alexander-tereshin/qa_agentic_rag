import os

import requests
from dotenv import load_dotenv
from src.models import AgentQueryRequest

import streamlit as st


load_dotenv()


AGENT_HOST = os.getenv("AGENT_HOST")
AGENT_PORT = os.getenv("AGENT_PORT")
AGENT_API_URL = f"http://{AGENT_HOST}:{AGENT_PORT}/agent_query"


def display_conversation(history: list[dict[str, str]]) -> None:
    """Display the conversation history in Streamlit chat format."""
    for entry in history:
        st.markdown(f"**Вы:** {entry['user']}")
        st.markdown(f"**Бот:** {entry['bot']}")


def clear_chat(chat_type: str) -> None:
    """Clear stored chat history by type."""
    if chat_type == "agent":
        st.session_state.conversation_history_agentic_rag = []
    elif chat_type == "classification":
        st.session_state.conversation_history_classification = []
    elif chat_type == "retrieval":
        pass


def get_agent_response(request: AgentQueryRequest) -> str:
    """Send query to the agent API and return the response."""
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(AGENT_API_URL, json=request.model_dump(), headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "⚠️ Ответ отсутствует.")
    except requests.exceptions.RequestException as e:
        return f"❌ Ошибка при запросе к API: {e!s}"


def agent_chat() -> None:
    st.markdown("### Agentic RAG")

    if "conversation_history_agentic_rag" not in st.session_state:
        st.session_state.conversation_history_agentic_rag = []

    query = st.chat_input("Введите ваш запрос")
    if query:
        st.session_state.conversation_history_agentic_rag.append({"user": query, "bot": None})

    for i, entry in enumerate(st.session_state.conversation_history_agentic_rag):
        st.markdown(f"**Вы:** {entry['user']}")
        if entry["bot"] is None:
            with st.spinner("🧠 Думаю..."):
                request = AgentQueryRequest(
                    agent=st.session_state.get("selected_agent", "default"),
                    query=entry["user"],
                )
                answer = get_agent_response(request)
                st.session_state.conversation_history_agentic_rag[i]["bot"] = answer
                st.rerun()
        else:
            st.markdown(f"**Бот:** {entry['bot']}")

    if st.session_state.conversation_history_agentic_rag and st.button("Очистить чат 🗑️"):
        clear_chat("agent")
