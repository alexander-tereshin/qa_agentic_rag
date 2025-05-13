import json
import os
from typing import Any

import psycopg2
import sqlparse
from openai import OpenAI
from smolagents import OpenAIServerModel, ToolCallingAgent, tool


db_params = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}


@tool
def validate_sql_query(query: str) -> str:
    """Check the syntax of a SQL query without executing it on the table. Useful for safe validation.

    Args:
        query (str): The SQL query to validate.

    Returns:
        str: A message indicating whether the query is syntactically valid or describing the syntax error.

    """
    conn = psycopg2.connect(**db_params)
    try:
        with conn.cursor() as cursor:
            cursor.execute("EXPLAIN " + query)
    except psycopg2.Error as e:
        return f"Ошибка в SQL-запросе: {e!s}"
    finally:
        conn.close()
    return "Запрос синтаксически корректен."


@tool
def get_unique_column_values(column: str) -> str:
    """Return a sorted list of unique values from a given column in the 'resumes' table.

    Args:
        column (str): The column name to extract unique values from.

    Returns:
        str: JSON-encoded list of unique values or error message if the column is invalid.

    """
    allowed_columns = {"id", "name", "gender", "title", "summary", "languages", "skills", "certifications", "hobbies"}

    if column not in allowed_columns:
        return f"Error: Column '{column}' is not allowed for unique value extraction."

    query = f'SELECT DISTINCT "{column}" FROM resumes ORDER BY "{column}"'  # noqa: S608

    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        with conn.cursor() as cursor:
            cursor.execute(query)
            values = cursor.fetchall()
            return json.dumps([v[0] for v in values], ensure_ascii=False)
    except psycopg2.Error as e:
        return f"Database error: {e!s}"
    finally:
        if conn:
            conn.close()


@tool
def sql_engine(query: str) -> str:
    """Execute validated SQL SELECT queries on the 'resumes' table and returns results as a JSON string.

    Table Schema for 'resumes':
        - id (integer)              - primary key
        - contact_info (jsonb)      - {"email": "...", "phone": "...", ...}
        - experience (jsonb)        - list of work-experience blocks
        - education (jsonb)         - list of education blocks
        - portfolio (jsonb)         - list of projects {"name", "link", "description"}
        - languages (ARRAY)         - e.g. ['Русский – родной', 'Английский – B2']
        - skills (ARRAY)            - e.g. ['Kubernetes', 'Python']
        - certifications (ARRAY)    - certificate names
        - hobbies (ARRAY)           - list of hobbies
        - name (text)               - full name
        - gender (text)             - gender
        - title (text)              - current/target job title
        - summary (text)            - resume summary/about section

    Examples:
        >>> sql_engine(\'''
            SELECT id, name, title
            FROM resumes
            WHERE 'Kubernetes' = ANY(skills)
            ORDER BY id
            LIMIT 5;
        \''')
        "[ [4, 'Маргарита Кирилловна Дорофеева', 'DevOps Engineer'], ... ]"

    Important:
        • Only SELECT queries are allowed.
        • Never pass raw user input directly without validation.
        • Avoid requesting more than 1000 rows per call.
        • Double-quote column names if they contain uppercase or non-ASCII characters.

    Args:
        query (str): A valid SQL SELECT query.

    Returns:
        str:
            - JSON-encoded list of result rows for SELECT queries.
            - Or an error message string for invalid or forbidden queries.

    """
    # GUARDRAIL
    try:
        parsed = sqlparse.parse(query)
        if len(parsed) != 1:
            return "Error: Only one SQL statement is allowed."

        stmt = parsed[0]
        if stmt.get_type() != "SELECT":
            return "Error: Only SELECT queries are permitted."

    except Exception as e:  # noqa: BLE001
        return f"Error while parsing SQL query: {e!s}"

    ###
    output = ""
    conn = None
    try:
        conn = psycopg2.connect(**db_params)
        with conn.cursor() as cursor:
            cursor.execute(query)
            try:
                rows: list[tuple[Any, ...]] = cursor.fetchall()
                output = rows
            except psycopg2.ProgrammingError:
                output = "Query executed successfully, but no results to fetch."

        conn.commit()

    except psycopg2.errors.SyntaxError as e:
        output = f"Syntax error in SQL query: {e!s}"
    except psycopg2.Error as e:
        output = f"Database error: {e!s}"
    finally:
        if conn:
            conn.close()

    return json.dumps(output, ensure_ascii=False)


@tool
def refine_and_validate_answer(sql_query: str, raw_result: str, draft_answer: str) -> str:
    """Переписывает ответ, делает его более понятным и проверяет, соответствует ли он данным SQL-запроса.

    Args:
        sql_query (str): Исходный SQL-запрос.
        raw_result (str): JSON-строка с результатами запроса.
        draft_answer (str): Черновой ответ.

    Returns:
        str: Улучшенный и проверенный финальный ответ.

    """
    prompt = f"""
Ты — эксперт по данным. Вот запрос, результат и черновой ответ:

SQL-запрос:
{sql_query}

Результат запроса (JSON):
{raw_result}

Черновой ответ:
"{draft_answer}"

Твоя задача:
1. Проверь, что черновой ответ действительно соответствует данным.
2. Дай очень прямой ответ без объяснений
3. Используй тот же язык, что и в черновике (русский или английский).

Финальный ответ:
"""
    try:
        client = OpenAI(api_key=os.getenv("LLM_API_TOKEN"), base_url=os.getenv("LLM_API_URL"))
        response = client.chat.completions.create(
            model=os.getenv("LLM_API_MODEL"),
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:  # noqa: BLE001
        return f"Ошибка при генерации финального ответа: {e}"


model = OpenAIServerModel(
    model_id=os.getenv("LLM_API_MODEL"),
    api_base=os.getenv("LLM_API_URL"),
    api_key=os.getenv("LLM_API_TOKEN"),
    flatten_messages_as_text=True,
)

smolagent_agent = ToolCallingAgent(
    tools=[sql_engine, get_unique_column_values],
    model=model,
    planning_interval=5,
    description=(
        """
        You are an HR assistant helping users analyze resume data stored in a PostgreSQL database.
        Always detect the user's query language and respond in the same language (if the question is in Russian, answer
        in Russian). Use the sql_engine tool to execute queries and retrieve data.
        Optionally, `use get_unique_column_values` to extract distinct values from specific columns when needed.
        Never fabricate or assume data—answers must be strictly based on SQL query results.
        Provide short, factual answers directly tied to the data.
        Casual greetings are allowed, but all answers must be precise and data-focused.
        Do not discuss topics unrelated to resumes.
        If asked 'Who are you?', reply: 'I am an HR assistant.'
        """
    ),
    max_steps=10,
)
