FROM python:3.13-slim

WORKDIR /app

COPY db/create_data.py .

RUN pip install psycopg2-binary

CMD ["python", "create_data.py"]
