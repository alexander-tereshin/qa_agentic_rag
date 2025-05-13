import os
from pathlib import Path

import requests
from requests.exceptions import RequestException, Timeout
from src import models
from src.components import list_pdfs, pdf_viewer, preview_pdf

import streamlit as st


HTTP_OK = 200


def view_resumes_tab() -> None:
    """Tab for viewing resumes."""
    pdf_files = list_pdfs("data/resumes_pdf")

    if pdf_files:
        selected_pdf = st.selectbox("Выберите резюме для просмотра:", pdf_files)
        if selected_pdf:
            preview_pdf(selected_pdf, "data/resumes_pdf")
    else:
        st.info("В папке нет PDF-файлов с резюме.")


def generate_resume_tab() -> None:
    """Tab for generating a new resume."""
    cities = models.CITIES
    jobs = models.SPECIALIZATIONS
    cv_generation_host = os.getenv("CV_GENERATOR_HOST")
    cv_generation_port = os.getenv("CV_GENERATOR_PORT")
    cv_generation_url = f"http://{cv_generation_host}:{cv_generation_port}/generate_resume"

    name = st.text_input("Имя кандидата", st.session_state.get("name", ""))
    desired_job = st.selectbox(
        "Желаемая должность",
        jobs,
        index=jobs.index(st.session_state.get("loc", jobs[0])),
    )
    years_of_experience = st.slider("Опыт работы (лет)", 0, 20, st.session_state.get("exp", 3))
    location = st.selectbox(
        "Местоположение",
        cities,
        index=cities.index(st.session_state.get("loc", cities[0])),
    )

    if st.button("Сгенерировать резюме"):
        candidate = models.CandidateInput(
            name=name,
            desired_job=desired_job,
            years_of_experience=years_of_experience,
            location=location,
        )
        with st.spinner(f"Ожидание генерации резюме для {candidate.name}..."):
            try:
                response = requests.post(url=cv_generation_url, json=candidate.model_dump(), timeout=120)
                if response.status_code == HTTP_OK:
                    result = response.json()
                    st.success(result.get("message", "Резюме сгенерировано успешно!"))
                    st.info("Резюме добавлено в базу данных.")
                    pdf_filename = result.get("pdf_filename")
                    if pdf_filename:
                        pdf_path = Path("data/resumes_pdf") / pdf_filename
                        if pdf_path.exists():
                            preview_pdf(pdf_path.name, "data/resumes_pdf")
                        else:
                            st.warning(f"Файл {pdf_filename} не найден. Возможно, генерация ещё не завершена.")
                else:
                    st.error(f"Ошибка генерации: {response.text}")
            except Timeout:
                st.error("Превышено время ожидания ответа от сервера.")
            except ConnectionError:
                st.error("Не удалось подключиться к серверу. Проверьте доступность API.")
            except RequestException as e:
                st.error(f"Ошибка при выполнении запроса: {e!s}")


def save_uploaded_file(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> Path:
    """Save the uploaded file to a temporary path."""
    tmp_path = Path("data/resumes_pdf") / uploaded_file.name
    with tmp_path.open("wb") as f:
        f.write(uploaded_file.getbuffer())
    return tmp_path


def process_single_resume(uploaded_file: Path, resume_parser_url: str) -> None:
    """Process a single resume and handle the response."""
    with uploaded_file.open("rb") as f:
        files = {"file": (uploaded_file.name, f, "application/pdf")}
        try:
            response = requests.post(url=resume_parser_url + "/parse_resume", files=files, timeout=120)
            if response.status_code == HTTP_OK:
                st.success(f"Резюме {uploaded_file.name} успешно обработано и добавлено в базу.")
            else:
                st.error(f"Ошибка при обработке резюме {uploaded_file.name}: {response.text}")
        except Timeout:
            st.error(f"Превышено время ожидания ответа для {uploaded_file.name}.")
        except ConnectionError:
            st.error(f"Не удалось подключиться для {uploaded_file.name}. Проверьте доступность API.")
        except RequestException as e:
            st.error(f"Ошибка при выполнении запроса для {uploaded_file.name}: {e!s}")


def process_batch_resumes(tmp_paths: list, resume_parser_url: str) -> None:
    """Process multiple resumes (batch) and handle the response."""
    files_batch = [("file", (file.name, file.open("rb"), "application/pdf")) for file in tmp_paths]
    try:
        response = requests.post(url=resume_parser_url + "/parse_resumes_batch", files=files_batch, timeout=120)
        if response.status_code == HTTP_OK:
            st.success(f"{len(tmp_paths)} резюме успешно обработаны и добавлены в базу.")
        else:
            st.error(f"Ошибка при обработке резюме: {response.text}")
    except Timeout:
        st.error("Превышено время ожидания ответа для группы файлов.")
    except ConnectionError:
        st.error("Не удалось подключиться. Проверьте доступность API.")
    except RequestException as e:
        st.error(f"Ошибка при выполнении запроса: {e!s}")


def process_resumes_tab() -> None:
    """Tab for processing uploaded resumes."""
    resume_parser_host = os.getenv("RESUME_PARSER_HOST")
    resume_parser_port = os.getenv("RESUME_PARSER_PORT")
    resume_parser_url = f"http://{resume_parser_host}:{resume_parser_port}"

    uploaded_files = st.file_uploader("Перетащите резюме сюда (PDF)", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        tmp_paths = [save_uploaded_file(uploaded_file) for uploaded_file in uploaded_files]

        if len(uploaded_files) == 1:
            uploaded_file = tmp_paths[0]
            pdf_viewer(str(uploaded_file))

            if st.button(f"Отправить {uploaded_file.name} на обработку"):
                with st.spinner("Обработка резюме..."):
                    process_single_resume(uploaded_file, resume_parser_url)

        else:
            for tmp_path in tmp_paths:
                st.markdown(f"**{tmp_path.name}**")
                pdf_viewer(str(tmp_path))

            if st.button("Отправить все резюме на обработку"):
                with st.spinner("Обработка всех резюме..."):
                    process_batch_resumes(tmp_paths, resume_parser_url)

    else:
        st.info("Перетащите PDF файл для обработки.")


def render() -> None:
    """Display tabs."""
    tab1, tab2, tab3 = st.tabs(["Просмотр резюме", "Генерация нового резюме", "Обработка резюме"])

    with tab1:
        view_resumes_tab()

    with tab2:
        generate_resume_tab()

    with tab3:
        process_resumes_tab()
