from tabs import qa_bot_page, resume_manager_page

import streamlit as st


def main() -> None:
    st.set_page_config(
        layout="centered",
        page_icon="assets/hse_logo.png",
        initial_sidebar_state="expanded",
        page_title="HR Assistant Chatbot",
    )

    st.sidebar.title("Навигация")
    selected_page = st.sidebar.selectbox("Выберите модуль", ("🤖 QA Бот", "📄 Управление резюме"))

    st.title("HR Assistant Chatbot")

    if selected_page == "📄 Управление резюме":
        resume_manager_page.render()
    elif selected_page == "🤖 QA Бот":
        qa_bot_page.render()


if __name__ == "__main__":
    main()
