import json
import logging

import psycopg2

from resume_parser.config.config import settings
from resume_parser.src.models import Resume


db_params = {
    "host": settings.postgres_host,
    "port": settings.postgres_port,
    "database": settings.postgres_db,
    "user": settings.postgres_user,
    "password": settings.postgres_password.get_secret_value(),
}


def resume_to_sql_values(resume: dict) -> tuple:
    return (
        resume.get("name"),
        resume.get("gender"),
        resume.get("title"),
        resume.get("summary"),
        json.dumps(resume.get("contact_info")),
        resume.get("skills"),
        json.dumps(resume.get("experience")),
        json.dumps(resume.get("education")),
        resume.get("languages"),
        resume.get("certifications"),
        resume.get("hobbies"),
        json.dumps(resume.get("portfolio")),
    )


def insert_resumes_to_db(resumes: list[Resume], logger: logging.Logger) -> None:
    insert_query = """
    INSERT INTO resumes (
        name, gender, title, summary, contact_info,
        skills, experience, education,
        languages, certifications, hobbies, portfolio
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    try:
        with psycopg2.connect(**db_params) as conn, conn.cursor() as cursor:
            for resume in resumes:
                try:
                    cursor.execute(insert_query, resume_to_sql_values(resume))
                except Exception:
                    conn.rollback()
                    logger.exception(f"Error inserting resume {resume.name}")
                    continue
            conn.commit()
    except Exception:
        logger.exception("Failed to connect to the database")
