import os
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_pdf_viewer import pdf_viewer


load_dotenv()


AGENT_API_HOST = os.getenv("AGENT_API_HOST", "agent")
AGENT_API_PORT = os.getenv("AGENT_API_PORT", "8001")
AGENT_API_ENDPOINT = os.getenv("AGENT_API_ENDPOINT", "/agent_query")

AGENT_API_URL = f"http://{AGENT_API_HOST}:{AGENT_API_PORT}{AGENT_API_ENDPOINT}"


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


def list_pdfs(directory: str) -> list:
    """Функция для получения списка всех PDF-файлов в папке."""
    return [f for f in Path(directory).iterdir() if f.lower().endswith(".pdf")]


def preview_pdf(pdf_filename: str, directory: str) -> None:
    """Функция для отображения PDF в Streamlit."""
    pdf_path = Path(directory) / pdf_filename

    if Path(pdf_path).exsists():
        with Path(pdf_path).open() as pdf_file:
            st.download_button(label="Download PDF", data=pdf_file, file_name=pdf_filename, mime="application/pdf")
        pdf_viewer(pdf_path)
    else:
        st.error(f"PDF file '{pdf_filename}' not found.")
