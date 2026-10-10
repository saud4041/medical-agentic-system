import sys
import os
import sqlite3
from src.config import DB_PATH


def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # New Table: Active list tracking of all successfully vectorized files
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingested_files (
                file_hash TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                total_chunks INTEGER,
                ingested_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Patient Records Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_history (
                patient_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                known_allergies TEXT,
                chronic_conditions TEXT,
                last_visit_date TEXT
            )
        """)

        # Clinical Encounter Telemetry Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinical_encounters (
                encounter_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT,
                symptoms TEXT,
                vitals TEXT,
                prescriptions TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(patient_id) REFERENCES patient_history(patient_id)
            )
        """)
        conn.commit()


init_db()
