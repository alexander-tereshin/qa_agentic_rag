import os

import requests
from requests.exceptions import RequestException, Timeout
from src import models
from src.components import list_pdfs, preview_pdf

import streamlit as st


HTTP_OK = 200


def render() -> None:
    cities = models.CITIES
    jobs = models.SPECIALIZATIONS

    cv_generation_host = os.getenv("CV_GENERATOR_HOST")
    cv_generation_port = os.getenv("CV_GENERATOR_PORT")
    cv_generation_url = f"http://{cv_generation_host}:{cv_generation_port}"

    tab1, tab2, tab3 = st.tabs(["Просмотр резюме", "Генерация нового резюме", "Обработка резюме"])

    with tab1:
        st.markdown("### Просмотр сгенерированных резюме")
        pdf_files = list_pdfs("data/resumes_pdf")

        if pdf_files:
            selected_pdf = st.selectbox("Выберите резюме для просмотра:", pdf_files)
            if selected_pdf:
                preview_pdf(selected_pdf, "data/resumes_pdf")
        else:
            st.info("В папке нет PDF-файлов с резюме.")

    with tab2:
        st.markdown("### Генерация нового резюме")

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

            with st.spinner(f"Запуск генерации резюме для {candidate.name}..."):
                try:
                    response = requests.post(url=cv_generation_url, json=candidate.model_dump(), timeout=30)
                    if response.status_code == HTTP_OK:
                        st.success(response.json().get("message"))
                        st.write("Ожидание генерации PDF...")

                        if st.button("🔄 Обновить список резюме"):
                            pdf_files = list_pdfs("data/resumes_pdf")
                            if pdf_files:
                                latest_pdf = sorted(pdf_files)[-1]
                                st.success("Резюме сгенерировано успешно!")
                                preview_pdf(latest_pdf, "data/resumes_pdf")
                            else:
                                st.warning("Новых PDF файлов не найдено. Попробуйте позже.")
                    else:
                        st.error(f"Ошибка генерации: {response.text}")
                except Timeout:
                    st.error("Превышено время ожидания ответа от сервера.")
                except ConnectionError:
                    st.error("Не удалось подключиться к серверу. Проверьте доступность API.")
                except RequestException as e:
                    st.error(f"Ошибка при выполнении запроса: {e!s}")
    with tab3:
        st.markdown("### Внесение резюме в базу")
