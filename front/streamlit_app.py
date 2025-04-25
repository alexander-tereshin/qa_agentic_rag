import os

import streamlit as st
from dotenv import load_dotenv
from src.components import get_bot_response, list_pdfs, preview_pdf
from streamlit_chat import message


load_dotenv()

PDF_DIRECTORY = os.getenv("PDF_DIR", "data/resumes_pdf")
PAGE_TITLE = os.getenv("PAGE_TITLE", "HR Assistant Chatbot")


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE)
    st.markdown(f"<h1 style='text-align: center;'>{PAGE_TITLE}</h1>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["💬 Chat", "📄 Resume Viewer"])

    with tab1:
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I am your HR bot. Ask me your question."}
            ]

        for msg in st.session_state.messages:
            message(msg["content"], is_user=(msg["role"] == "user"))

        user_input = st.chat_input("Enter your question...")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.spinner("Processing your request..."):
                response = get_bot_response(user_input)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

    with tab2:
        pdf_files = list_pdfs(PDF_DIRECTORY)

        if pdf_files:
            selected_pdf = st.selectbox("Select a resume to preview:", pdf_files)
            if selected_pdf:
                preview_pdf(selected_pdf, PDF_DIRECTORY)
        else:
            st.info("No PDF resumes found in the directory.")


if __name__ == "__main__":
    main()
