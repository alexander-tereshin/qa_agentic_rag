from src.components import agent_chat

import streamlit as st


def main() -> None:
    st.set_page_config(
        layout="centered",
        page_icon="streamlit/hse_logo.png",
        initial_sidebar_state="expanded",
        page_title="HR Assistant Chatbot",
    )
    option = st.sidebar.selectbox(
        "Выберите фреймворк",
        ("Smolagents", "PydanticAI", "Собственная Реализация"),
    )
    agent_map = {
        "Smolagents": "smollagents",
        "PydanticAI": "pydantic_ai_agent",
        "Собственная Реализация": "self_written_agent",
    }
    st.session_state.selected_agent = agent_map[option]

    agent_chat()


if __name__ == "__main__":
    main()
