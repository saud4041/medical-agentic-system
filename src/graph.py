from typing import Annotated, TypedDict, Literal
import json
import re
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AIMessage
from src.config import get_llm
from src.database import get_db_connection
from src.rag_engine import rag_engine

# Import streamlined prompts
from prompts.prompts import DB_AGENT_PROMPT_TEMPLATE, RAG_AGENT_PROMPT_TEMPLATE


class MultiAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str
    target_patient: str


llm = get_llm()


# --- CRASH-PROOF ALIVE PATIENT DICTIONARY CACHE ---
def get_known_patient_names():
    """Fetches valid names from the database safely to facilitate microsecond text-matching."""
    try:
        with get_db_connection() as conn:
            # Enforce raw tuples for this specific query to ensure uniform scanning
            conn.row_factory = None
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM patient_history")
            rows = cursor.fetchall()

            patient_map = {}
            for row in rows:
                if row and isinstance(row, tuple) and len(row) > 0:
                    name_str = row[0]
                    if name_str:
                        patient_map[name_str.lower()] = name_str
            return patient_map

    except Exception as e:
        print(f"⚠️ Routing cache fallback activated: {str(e)}")
        return {
            "john doe": "John Doe",
            "jane smith": "Jane Smith",
            "robert chen": "Robert Chen",
            "alice martinez": "Alice Martinez",
            "david kim": "David Kim",
            "sarah jenkins": "Sarah Jenkins",
            "marcus vance": "Marcus Vance",
        }


# --- AGENT 1: AUTOMATIC DATABASE AGENT ---
def db_agent_node(state: MultiAgentState):
    """Queries structured records and passes clean JSON context down to the LLM."""
    last_msg = state["messages"][-1].content
    target = state.get("target_patient", "unknown")

    with get_db_connection() as conn:
        # --- FIX: FORCE EXPLICIT TUPLE-BASED DESCRIPTION MAPPING ---
        # Bypasses direct dict(row) unpack crashes entirely
        conn.row_factory = None
        cursor = conn.cursor()

        if target and target != "unknown":
            query_param = f"%{target}%"
            cursor.execute(
                """
                SELECT h.patient_id, h.name, h.age, h.known_allergies, h.chronic_conditions, 
                       e.symptoms, e.vitals, e.prescriptions 
                FROM patient_history h 
                LEFT JOIN clinical_encounters e ON h.patient_id = e.patient_id 
                WHERE h.name LIKE ? OR h.patient_id LIKE ?
                """,
                (query_param, query_param),
            )
        else:
            cursor.execute(
                """
                SELECT h.patient_id, h.name, h.age, h.known_allergies, h.chronic_conditions, 
                       e.symptoms, e.vitals, e.prescriptions  
                FROM patient_history h
                LEFT JOIN clinical_encounters e ON h.patient_id = e.patient_id
                LIMIT 3
                """
            )

        rows = cursor.fetchall()

        # Explicit column serialization to map raw text rows safely into a dictionary array
        columns = [desc[0] for desc in cursor.description]
        data = []
        for row in rows:
            data.append(dict(zip(columns, row)))

    formatted_prompt = DB_AGENT_PROMPT_TEMPLATE.format(
        raw_database_payload=json.dumps(data)
        if data
        else "No patient records located.",
        user_query=last_msg,
    )

    response = llm.invoke(formatted_prompt)
    return {"messages": [AIMessage(content=response.content)]}


# --- AGENT 2: MEDICAL RAG AGENT ---
def rag_agent_node(state: MultiAgentState):
    """Queries context indices and generates a final response context."""
    last_msg = state["messages"][-1].content

    # Query ChromaDB context collections
    retrieved_guidelines = rag_engine.query_knowledge_base(last_msg, n_results=2)

    formatted_prompt = RAG_AGENT_PROMPT_TEMPLATE.format(
        retrieved_guidelines=retrieved_guidelines, user_query=last_msg
    )

    response = llm.invoke(formatted_prompt)
    return {"messages": [AIMessage(content=response.content)]}


# --- AGENT 3: HIGH-SPEED ROUTER ---
def supervisor_router_node(state: MultiAgentState):
    """
    Executes algorithmic keyword & patient entity lookups instantly.
    Bypasses DeepSeek token generation lag entirely for routing.
    """
    last_msg = state["messages"][-1].content.lower()

    # Check for direct Patient ID strings (e.g., P101, P106)
    id_match = re.search(r"\bp\d{3}\b", last_msg)
    if id_match:
        target_id = id_match.group(0).upper()
        return {"next_agent": "database", "target_patient": target_id}

    # Check for Patient Name strings out of our local EHR registry
    known_patients = get_known_patient_names()
    for lower_name, exact_name in known_patients.items():
        if lower_name in last_msg:
            return {"next_agent": "database", "target_patient": exact_name}

    # Intent keyword fallback markers
    db_keywords = [
        "patient",
        "record",
        "history",
        "chart",
        "prescription",
        "vitals",
        "allergies",
        "encounter",
    ]
    if any(keyword in last_msg for keyword in db_keywords):
        return {"next_agent": "database", "target_patient": "unknown"}

    # Instant fallback to RAG Knowledge Base if no relational entities match
    return {"next_agent": "rag", "target_patient": "unknown"}


def route_decision(state: MultiAgentState) -> Literal["database", "rag"]:
    return state["next_agent"]


# --- COMPILE STATE GRAPH WORKFLOW ---
workflow = StateGraph(MultiAgentState)
workflow.add_node("supervisor", supervisor_router_node)
workflow.add_node("database_agent", db_agent_node)
workflow.add_node("rag_agent", rag_agent_node)

workflow.add_edge(START, "supervisor")
workflow.add_conditional_edges(
    "supervisor", route_decision, {"database": "database_agent", "rag": "rag_agent"}
)
workflow.add_edge("database_agent", END)
workflow.add_edge("rag_agent", END)

medical_agent_graph = workflow.compile()
