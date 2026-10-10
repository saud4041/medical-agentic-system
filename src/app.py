import sys
import os
import re

# --- WINDOWS ROOT PATH ROUTING PATCH ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from src.database import init_db, get_db_connection
from src.rag_engine import rag_engine
from src.graph import medical_agent_graph
from langchain_core.messages import HumanMessage, AIMessage

# --- WEB DASHBOARD CORE STYLING ---
st.set_page_config(page_title="Medical Agentic System", page_icon="🩺", layout="wide")

st.title("🩺 Medical Agentic System")
st.markdown("---")

# Initialize structured SQLite schemas
init_db()

# --- AUTOMATIC MOCK DATASET SEEDER ---
if "data_seeded" not in st.session_state:
    # 1. Seed comprehensive, realistic clinical profiles into SQLite
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patient_history")
        if (
            cursor.fetchone()[0] <= 3
        ):  # If database only contains previous basic items, reseed the broad array
            # Clear legacy testing remnants to ensure smooth structural joins
            cursor.execute("DELETE FROM patient_history")
            cursor.execute("DELETE FROM clinical_encounters")

            expanded_patients = [
                (
                    "P101",
                    "John Doe",
                    45,
                    "Penicillin",
                    "Essential Hypertension",
                    "2026-08-14",
                ),
                (
                    "P102",
                    "Jane Smith",
                    29,
                    "Sulfa Drugs, Peanuts",
                    "Chronic Bronchial Asthma",
                    "2026-09-01",
                ),
                (
                    "P103",
                    "Robert Chen",
                    62,
                    "None",
                    "Type 2 Diabetes Mellitus",
                    "2026-10-05",
                ),
                (
                    "P104",
                    "Alice Martinez",
                    34,
                    "Amoxicillin, Dairy",
                    "Generalized Anxiety Disorder",
                    "2026-10-08",
                ),
                (
                    "P105",
                    "David Kim",
                    51,
                    "Aspirin",
                    "Hyperlipidemia, Chronic Kidney Disease",
                    "2026-09-24",
                ),
                (
                    "P106",
                    "Sarah Jenkins",
                    19,
                    "Codeine, Tree Nuts",
                    "None",
                    "2026-10-09",
                ),
                (
                    "P107",
                    "Marcus Vance",
                    73,
                    "Contrast Dye",
                    "Atrial Fibrillation, Osteoarthritis",
                    "2026-10-02",
                ),
            ]
            cursor.executemany(
                "INSERT INTO patient_history VALUES (?, ?, ?, ?, ?, ?)",
                expanded_patients,
            )

            expanded_encounters = [
                (
                    "P101",
                    "Acute throbbing occipital headache, elevated physical fatigue",
                    "BP: 145/95 mmHg, HR: 78 bpm, Temp: 36.8°C",
                    "Lisinopril 10mg PO daily",
                ),
                (
                    "P102",
                    "Shortness of breath, mild expiratory wheezing due to seasonal changes",
                    "O2 Sat: 96% on room air, RR: 22 bpm, HR: 88 bpm",
                    "Albuterol HFA Inhaler 2 puffs PRN",
                ),
                (
                    "P103",
                    "Routine quarterly metabolic follow-up, fasting glucose validation",
                    "HbA1c: 7.1%, Weight: 84kg, BP: 130/82 mmHg",
                    "Metformin 500mg PO BID",
                ),
                (
                    "P104",
                    "Productive cough, chest congestion, low-grade fever, yellow sputum",
                    "Temp: 38.2°C, BP: 118/76 mmHg, HR: 92 bpm",
                    "Azithromycin 250mg 5-Day Dose Pack",
                ),
                (
                    "P105",
                    "Burning dysuria, frequent urination, lower abdominal pressure",
                    "Temp: 37.5°C, BP: 138/88 mmHg, Urinalysis: Positive Nitrites",
                    "Ciprofloxacin 500mg PO BID for 3 days",
                ),
                (
                    "P106",
                    "Sore throat, painful swallowing, swollen cervical lymph nodes",
                    "Temp: 38.9°C, Rapid Strep Test: Positive",
                    "Phenoxymethylpenicillin 500mg QID for 10 days",
                ),
                (
                    "P107",
                    "Sudden swelling, warmth, and severe tenderness in the left knee joint",
                    "BP: 128/74 mmHg, HR: 64 bpm (Irregular), Temp: 37.1°C",
                    "Colchicine 0.6mg PO daily, Apixaban 5mg BID",
                ),
            ]
            cursor.executemany(
                "INSERT INTO clinical_encounters (patient_id, symptoms, vitals, prescriptions) VALUES (?, ?, ?, ?)",
                expanded_encounters,
            )
            conn.commit()

    # 2. Seed unstructured literature profiles inside ChromaDB
    try:
        rag_engine.ingest_document(
            doc_id="covid_transmission_01",
            text="COVID-19 transmission occurs primarily through respiratory droplets generated when an infected individual coughs, sneezes, talks, or breathes. People catch COVID-19 by inhaling these contaminated airborne droplets or through aerosols suspended in poorly ventilated indoor spaces. Secondary transmission can occur by touching surfaces contaminated with the SARS-CoV-2 virus and subsequently touching the eyes, nose, or mouth.",
            metadata={"source": "CDC Guidelines 2026", "topic": "COVID-19"},
        )
        rag_engine.ingest_document(
            doc_id="covid_symptoms_02",
            text="Common symptoms of COVID-19 include fever, chills, persistent dry cough, shortness of breath, fatigue, muscle aches, headache, new loss of taste or smell, sore throat, congestion, nausea, and diarrhea. Symptoms typically appear 2 to 14 days after exposure to the virus.",
            metadata={"source": "WHO Clinical Guidelines", "topic": "COVID-19"},
        )
    except Exception:
        pass

    st.session_state.data_seeded = True

# --- CONVERSATION MEMORY LAYER ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar panel providing dynamic test tokens
with st.sidebar:
    st.markdown("### 💡 Interactive Testing Prompts")
    st.markdown("**Test Database Tracking (New Infected Patients):**")
    st.code("Lookup clinical record for Marcus Vance")
    st.code("Show infection symptoms for patient Sarah Jenkins")
    st.markdown("---")
    st.markdown("**Test Vector Reference Library:**")
    st.code("How do you catch covid-19?")

# Display conversation histories
for msg in st.session_state.chat_history:
    with st.chat_message("user" if isinstance(msg, HumanMessage) else "assistant"):
        st.write(msg.content)

# --- USER CHAT INPUT INTERACTION INTERFACE ---
if user_query := st.chat_input(
    "Enter clinical symptoms or look up historical patient context..."
):
    st.session_state.chat_history.append(HumanMessage(content=user_query))
    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        status_box = st.empty()
        thinking_box = st.expander(
            "💭 View Local Agent Co-Ordinator Reasoning", expanded=True
        )
        text_box = st.empty()

        with status_box:
            st.info("🤖 Supervisor routing query across your local agent workspace...")

        try:
            # Trigger LangGraph orchestration logic
            output_state = medical_agent_graph.invoke(
                {"messages": st.session_state.chat_history}
            )
            final_agent_message = output_state["messages"][-1].content
            status_box.empty()

            # --- SAFE DEEPSEEK STRING EXTRACTION ENGINE ---
            if "<think>" in final_agent_message:
                parts = final_agent_message.split("</think>", 1)
                raw_reasoning = parts[0].replace("<think>", "").strip()
                actual_answer = (
                    parts[1].strip()
                    if len(parts) > 1
                    else "Summary compilation complete."
                )

                thinking_box.write(raw_reasoning)
                text_box.write(actual_answer)
                st.session_state.chat_history.append(AIMessage(content=actual_answer))
            else:
                thinking_box.write(
                    "Direct agent mapping used — no sub-reasoning token strings found."
                )
                text_box.write(final_agent_message)
                st.session_state.chat_history.append(
                    AIMessage(content=final_agent_message)
                )

        except Exception as e:
            status_box.empty()
            error_msg = f"❌ Core Execution Error: {str(e)}"
            text_box.error(error_msg)
            print(f"Internal System Debug Log: {e}")
