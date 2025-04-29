from dotenv import load_dotenv
from src.components import get_bot_response
from streamlit_chat import message

import streamlit as st


load_dotenv()

def main() -> None:
    page_title = "HR Assistant Chatbot"
    st.set_page_config(page_title=page_title)
    st.markdown(f"<h1 style='text-align: center;'>{page_title}</h1>", unsafe_allow_html=True)

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


if __name__ == "__main__":
    main()
