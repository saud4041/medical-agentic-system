import os
import chromadb
from src.config import CHROMA_DIR, get_embeddings


class MedicalRAGEngine:
    def __init__(self):
        os.makedirs(CHROMA_DIR, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
        self.embeddings = get_embeddings()
        self.collection = self.chroma_client.get_or_create_collection(
            name="medical_knowledge"
        )

    def ingest_document(self, doc_id: str, text: str, metadata: dict = None):
        """Vectorizes and commits textbook passages safely into ChromaDB."""
        vector = self.embeddings.embed_query(text)

        if not metadata or len(metadata) == 0:
            final_metadata = None
        else:
            final_metadata = [metadata]

        self.collection.add(
            ids=[doc_id],
            embeddings=[vector],
            documents=[text],
            metadatas=final_metadata,
        )

    def query_knowledge_base(self, query: str, n_results: int = 3) -> str:
        """Finds matching reference guidelines from the local store."""
        query_vector = self.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_vector], n_results=n_results
        )

        # --- FIXED: UNPACK NESTED CHROMADB LIST STRUCTURE ---
        if results and "documents" in results and results["documents"]:
            doc_list = results["documents"]

            # ChromaDB returns structures like [[doc1, doc2, doc3]].
            # We check if the first item is a list and flatten it.
            if (
                isinstance(doc_list, list)
                and len(doc_list) > 0
                and isinstance(doc_list[0], list)
            ):
                doc_list = doc_list[0]

            # Filter out any lingering empty strings or None items
            clean_docs = [str(doc) for doc in doc_list if doc]

            if clean_docs:
                return "\n\n".join(clean_docs)

        return "No corresponding medical literature found in local vectors."


rag_engine = MedicalRAGEngine()
