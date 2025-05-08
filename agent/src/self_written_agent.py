import logging
import os
from typing import Literal

import psycopg2
from dotenv import load_dotenv
from openai import Client
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel, Field


load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

llm_api_url = os.getenv("AGENT_LLM_API_URL")
api_key = os.getenv("AGENT_LLM_API_TOKEN")
model = os.getenv("AGENT_LLM_API_MODEL")


client = Client(base_url=llm_api_url, api_key=api_key)

db_params = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


def get_available_tables(schema: str = "public") -> list[str]:
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE';
        """,
        (schema,),
    )
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    logger.debug(f"Available tables: {tables}")
    return tables


def get_table_schema(table_name: str) -> str:
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = %s;
        """,
        (table_name,),
    )
    columns = cursor.fetchall()
    conn.close()
    schema = "\n".join(f"- {col[0]} ({col[1]})" for col in columns)
    logger.debug(f"Schema for {table_name}:\n{schema}")
    return schema


def get_table_preview(table_name: str, limit: int = 10) -> list[dict]:
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")  # noqa: S608
    rows = cursor.fetchall()
    conn.close()
    logger.debug(f"Preview first {limit} rows from {table_name}: {rows}")
    return rows


def sql_engine(query: str) -> str:
    """Execute validated SQL SELECT queries on the 'resumes' table and returns results as a JSON string."""
    logger.info(f"Executing SQL: {query}")
    try:
        with psycopg2.connect(**db_params) as conn, conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            try:
                results = cursor.fetchall()
            except psycopg2.ProgrammingError:
                logger.info("Query executed successfully, but no results to fetch.")
                return []
            else:
                logger.debug(f"SQL results: {results}")
                return results
    except psycopg2.errors.SyntaxError:
        logger.exception("Syntax error in SQL query")
    except psycopg2.Error:
        logger.exception("Database error")
    return []


class SQLRequest(BaseModel):
    reasoning: str = Field(..., description="Почему запрос безопасен или опасен")
    is_dangerous: bool = Field(..., description="Флаг опасности")
    sql_query: str | None = Field(None, description="SQL для выполнения, если safe")


class AgentAction(BaseModel):
    function: Literal["sql_engine"]
    reasoning: str = Field(..., description="Напиши свои мысли, как ты формируешь sql запрос")
    is_dangerous: bool
    sql_query: str | None


def analyze_user_message(message: str) -> AgentAction:
    logger.info(f"Analyzing user message: {message}")
    tables = get_available_tables()
    schema_blocks = [f"Table `{tbl}`:\n{get_table_schema(tbl)}" for tbl in tables]
    full_schema = "\n\n".join(schema_blocks)

    system_prompt = (
        "Ты — AI-ассистент, генерирующий SQL-запросы на основе пользовательских запросов.\n"
        "Ниже — схема базы данных PostgreSQL:\n\n"
        f"{full_schema}\n\n"
        "1) Проанализируй запрос.\n"
        "2) Если он опасен или модифицирует данные — установи is_dangerous=true и опиши reasoning.\n"
        "3) Если безопасен — сгенерируй корректный SELECT и верни его в поле sql_query.\n"
        "4) Перефразируй запрос пользователя как комментарий перед SQL.\n"
        "5) Учитывай различные варианты написания специальностей.\n"
        "6) Оптимизируй запрос для минимальной нагрузки на БД."
    )

    response = client.beta.chat.completions.parse(
        model=model,
        temperature=0.4,
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": message}],
        response_format=AgentAction,
    )

    raw = response.choices[0].message.content
    logger.debug(f"Raw LLM response: {raw}")

    action: AgentAction = response.choices[0].message.parsed
    logger.info(f"LLM reasoning: {action.reasoning}")
    logger.debug(f"Parsed AgentAction: {action.model_dump_json()}")
    if action.sql_query:
        logger.info(f"Generated SQL query: {action.sql_query}")
    return action


def format_sql_result_with_llm(user_message: str, sql_query: str, raw_result: str) -> str:
    """Форматирует результат SQL-запроса в человекочитаемый ответ с помощью LLM."""
    system_prompt = """Ты — AI-ассистент, который помогает пользователю, отвечая на вопросы, связанные с SQL.

        Вот твоя задача:
        1. Прочитай запрос пользователя.
        2. Оцени сгенерированный SQL-код.
        3. Проанализируй результат выполнения запроса (в формате JSON).
        4. Сформулируй краткий, точный и понятный ответ для пользователя, основываясь на данных.
        5. Ответ должен быть по существу и не содержать лишней информации и должен быть на языке вопроса.
        Основное внимание уделяй ясности, точности и соответствию запросу.
        """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Запрос пользователя:\n{user_message}"},
        {"role": "user", "content": f"Сгенерированный SQL:\n{sql_query}"},
        {"role": "user", "content": f"Результат SQL (JSON):\n{raw_result}"},
    ]
    response = client.beta.chat.completions.parse(
        model=model,
        temperature=0.15,
        messages=messages,
    )

    reply = response.choices[0].message.content.strip()
    logger.debug(f"LLM-formatted answer: {reply}")
    return reply


def process_user_message(message: str) -> str:
    logger.info(f"User message received: {message}")
    action = analyze_user_message(message)

    if action.is_dangerous:
        logger.warning(f"Dangerous request rejected: {action.reasoning}")
        return f"Запрос отклонён: {action.reasoning}"
    if action.function == "sql_engine" and action.sql_query:
        try:
            raw_results = sql_engine(action.sql_query)
            logger.info(f"Query executed successfully, returned {len(raw_results)} rows")
        except Exception:
            raw_results = "Ошибка при выполнении SQL"
            logger.exception("SQL execution error")
        return format_sql_result_with_llm(
            user_message=message,
            sql_query=action.sql_query,
            raw_result=raw_results,
        )
    logger.error("No valid SQL query generated")
    return "Ваш запрос не имеет отношения к базе данных."
