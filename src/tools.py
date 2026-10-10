from langchain_core.tools import tool
from src.database import get_db_connection


@tool
def fetch_patient_history(patient_name: str) -> str:
    """Fetches historic clinical logging information for a specific patient."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT symptoms, diagnosis_log FROM patient_history WHERE patient_name = ?",
            (patient_name,),
        )
        rows = cursor.fetchall()
        if not rows:
            return f"No medical history found for patient: {patient_name}."
        return "\n".join(
            [
                f"Symptoms: {r['symptoms']} | Past Assessment: {r['diagnosis_log']}"
                for r in rows
            ]
        )
