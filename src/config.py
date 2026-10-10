import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama, OllamaEmbeddings

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "database/medical_records.db")
CHROMA_DIR = os.getenv("CHROMA_DIR", "vectorstore/chroma_data")

LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-r1:1.5b")


def get_llm():
    return ChatOllama(model=LLM_MODEL, temperature=0.2)


def get_embeddings():
    return OllamaEmbeddings(model=LLM_MODEL)
