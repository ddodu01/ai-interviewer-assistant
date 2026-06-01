import json
import sqlite3
from pathlib import Path

from datasets import load_dataset


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "cv_job_database.db"


def create_tables():
    DATA_DIR.mkdir(exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_descriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_job_id TEXT,
        category TEXT,
        job_title TEXT,
        job_description TEXT,
        job_skill_set TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cvs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_cv_id TEXT,
        candidate_name TEXT,
        raw_text TEXT,
        skills TEXT,
        experience TEXT,
        education TEXT,
        raw_json TEXT
    )
    """)

    conn.commit()
    conn.close()


def clear_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM job_descriptions")
    cursor.execute("DELETE FROM cvs")

    cursor.execute("DELETE FROM sqlite_sequence WHERE name='job_descriptions'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='cvs'")

    conn.commit()
    conn.close()

def value_to_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        return "\n".join(value_to_text(item) for item in value)

    if isinstance(value, dict):
        return "\n".join(
            f"{key}: {value_to_text(val)}"
            for key, val in value.items()
        )

    return str(value)


def safe_get(row, possible_keys):
    for key in possible_keys:
        if key in row and row[key] is not None:
            return row[key]
    return ""


def build_raw_text(row):
    parts = []

    for key, value in row.items():
        text_value = value_to_text(value)
        if text_value.strip():
            parts.append(f"{key}:\n{text_value}")

    return "\n\n".join(parts)


def import_job_descriptions():
    print("Loading job descriptions dataset...")

    dataset = load_dataset("batuhanmtl/job-skill-set")
    train_data = dataset["train"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for row in train_data:
        cursor.execute("""
        INSERT INTO job_descriptions (
            source_job_id,
            category,
            job_title,
            job_description,
            job_skill_set
        )
        VALUES (?, ?, ?, ?, ?)
        """, (
            str(row.get("job_id", "")),
            row.get("category", ""),
            row.get("job_title", ""),
            row.get("job_description", ""),
            row.get("job_skill_set", "")
        ))

    conn.commit()
    conn.close()

    print(f"Imported {len(train_data)} job descriptions.")


def import_cvs():
    print("Loading CV/resume dataset...")

    dataset = load_dataset("datasetmaster/resumes")
    split_name = "train" if "train" in dataset else list(dataset.keys())[0]
    resume_data = dataset[split_name]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for index, row in enumerate(resume_data):
        source_cv_id = str(
            safe_get(row, ["id", "resume_id", "candidate_id"]) or index
        )
        personal_info = row.get("personal_info", {})

        candidate_name = value_to_text(
            safe_get(row, ["name", "candidate_name", "full_name"])
        )

        if not candidate_name and isinstance(personal_info, dict):
            candidate_name = value_to_text(personal_info.get("name", ""))

        skills = value_to_text(
            safe_get(row, ["skills", "skill", "technical_skills"])
        )

        experience = value_to_text(
            safe_get(row, ["experience", "work_experience", "employment"])
        )

        education = value_to_text(
            safe_get(row, ["education", "academic_background"])
        )

        raw_text = build_raw_text(row)
        raw_json = json.dumps(row, ensure_ascii=False)

        cursor.execute("""
        INSERT INTO cvs (
            source_cv_id,
            candidate_name,
            raw_text,
            skills,
            experience,
            education,
            raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            source_cv_id,
            candidate_name,
            raw_text,
            skills,
            experience,
            education,
            raw_json
        ))

    conn.commit()
    conn.close()

    print(f"Imported {len(resume_data)} CVs.")


def check_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM job_descriptions")
    jobs_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cvs")
    cvs_count = cursor.fetchone()[0]

    print("\nDatabase created successfully.")
    print(f"Database path: {DB_PATH}")
    print(f"Job descriptions: {jobs_count}")
    print(f"CVs: {cvs_count}")

    print("\nSample job:")
    cursor.execute("""
    SELECT job_title, category
    FROM job_descriptions
    LIMIT 1
    """)
    print(cursor.fetchone())

    print("\nSample CV:")
    cursor.execute("""
    SELECT id, candidate_name, substr(raw_text, 1, 300)
    FROM cvs
    LIMIT 1
    """)
    print(cursor.fetchone())

    conn.close()


if __name__ == "__main__":
    create_tables()
    clear_tables()
    import_job_descriptions()
    import_cvs()
    check_database()