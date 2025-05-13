from src.components import agent_chat

import streamlit as st


def render() -> None:
    with st.expander("⚙️ Выбор фреймворка (по желанию)", expanded=False):
        option = st.selectbox(
            "Выберите фреймворк:",
            ("Собственная Реализация", "Smolagents", "PydanticAI"),
        )

        agent_map = {
            "Smolagents": "smollagents",
            "PydanticAI": "pydantic_ai_agent",
            "Собственная Реализация": "self_written_agent",
        }

        st.session_state.selected_agent = agent_map[option]

    agent_chat()
