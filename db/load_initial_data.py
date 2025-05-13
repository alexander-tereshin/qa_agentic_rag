import json
import logging
import os
import sys
from pathlib import Path

import psycopg2


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

JSONS_DIR = Path(__file__).resolve().parent / "data" / "resumes_json"
if not JSONS_DIR.exists():
    logger.error(f"Directory not found: {JSONS_DIR}")
    sys.exit(1)

json_files = list(JSONS_DIR.glob("*.json"))
if not json_files:
    logger.warning(f"No JSON files found in {JSONS_DIR}")
    sys.exit(1)
else:
    logger.info(f"Found {len(json_files)} JSON file(s) to insert.")


conn = psycopg2.connect(
    host=os.environ["POSTGRES_HOST"],
    port=os.environ["POSTGRES_PORT"],
    database=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
)

insert_query = """
INSERT INTO resumes (
    name, gender, title, summary, contact_info,
    skills, experience, education,
    languages, certifications, hobbies, portfolio
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

cursor = conn.cursor()
inserted_count = 0

for filepath in json_files:
    try:
        with filepath.open("r", encoding="utf-8") as f:
            resume = json.load(f)
        name = resume.get("name")
        cursor.execute(
            insert_query,
            (
                name,
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
            ),
        )
        logger.debug(f"Inserted resume '{name}' from '{filepath.name}'")
        inserted_count += 1
    except json.JSONDecodeError:
        logger.exception(f"Error decoding JSON in {filepath.name}")
    except Exception:
        logger.exception(f"Error processing {filepath.name}")

conn.commit()
logger.info(f"Inserted {inserted_count} resumes.")

cursor.close()
conn.close()
logger.info("Database connection closed.")
