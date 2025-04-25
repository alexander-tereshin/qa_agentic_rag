FROM python:3.13-slim

WORKDIR /app

COPY db/load_initial_data.py .

RUN pip install psycopg2-binary

CMD ["python", "load_initial_data.py"]
