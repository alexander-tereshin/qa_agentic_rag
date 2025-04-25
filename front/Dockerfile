FROM python:3.13

WORKDIR /app

COPY front front

RUN pip install streamlit_chat streamlit streamlit_pdf_viewer python-dotenv

CMD ["streamlit", "run",  "front/streamlit_app.py"]
