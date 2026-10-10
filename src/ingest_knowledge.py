import os
import glob
import hashlib
import re
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.database import get_db_connection
from src.rag_engine import rag_engine

# Silence underlying platform font rendering alerts safely
warnings.filterwarnings("ignore", category=UserWarning, module="pypdf")

KNOWLEDGEBASE_DIR = "knowledgebase"
BATCH_SIZE = 100  # Process chunks in controlled micro-batches to allow Windows sockets to recycle


def calculate_file_hash(filepath: str) -> str:
    """Computes SHA-256 signatures to reliably track file changes."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def is_file_already_ingested(file_hash: str) -> bool:
    """Checks the database to ensure we do not re-index files."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM ingested_files WHERE file_hash = ?", (file_hash,))
        return cursor.fetchone() is not None


def record_successful_ingestion(file_hash: str, filename: str, total_chunks: int):
    """Logs files in SQLite once they are fully vectorized."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO ingested_files (file_hash, filename, total_chunks) VALUES (?, ?, ?)",
            (file_hash, filename, total_chunks),
        )
        conn.commit()


def clean_academic_text(page_text: str) -> str:
    """Filters out running headers, footers, page numbers, and DOIs from medical literature."""
    if not page_text:
        return ""

    lines = page_text.splitlines()
    cleaned_lines = []

    doi_pattern = re.compile(r"doi:\s*10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
    url_pattern = re.compile(r"https?:\(//\S+\vert{}www\.\S+\)")

    for line in lines:
        line_strip = line.strip()

        if not line_strip or line_strip.isdigit():
            continue

        if len(line_strip) < 15 and (
            "volume" in line_strip.lower()
            or "issue" in line_strip.lower()
            or "page" in line_strip.lower()
        ):
            continue

        if doi_pattern.search(line_strip) or url_pattern.search(line_strip):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def process_single_chunk_with_retry(idx, chunk_data, filename, max_retries=5):
    """Worker task that handles background vector computation with resilient connection retries."""
    doc_id = f"{filename}_chunk_{idx}"
    metadata = {"source": filename, "page": chunk_data["page"]}

    backoff = 1.0
    for attempt in range(max_retries):
        try:
            rag_engine.ingest_document(
                doc_id=doc_id, text=chunk_data["text"], metadata=metadata
            )
            return True
        except Exception as e:
            # Catching Socket 10038 error or generic connection pool drops
            if (
                "10038" in str(e)
                or "socket" in str(e).lower()
                or "connection" in str(e).lower()
            ):
                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"Chroma DB failure on chunk {idx} after {max_retries} attempts: {str(e)}"
                    )

                # Sleep with linear-jitter backoff to let Windows recycle sockets
                time.sleep(backoff)
                backoff *= 1.5
                continue
            else:
                # Immediate exit if the error isn't networking-related
                raise RuntimeError(
                    f"Chroma DB unexpected processing failure on chunk {idx}: {str(e)}"
                )


def process_and_ingest_pdfs():
    """Reads new medical literature, handles background embedding calculations, and updates the index."""
    os.makedirs(KNOWLEDGEBASE_DIR, exist_ok=True)
    pdf_files = glob.glob(os.path.join(KNOWLEDGEBASE_DIR, "*.pdf"))

    if not pdf_files:
        print(
            f"⚠️ No PDF reference materials discovered within './{KNOWLEDGEBASE_DIR}/'."
        )
        return

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=250, length_function=len
    )

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        file_hash = calculate_file_hash(pdf_path)

        if is_file_already_ingested(file_hash):
            print(
                f"⏩ Skipping '{filename}' — Already fully processed and indexed into Vector DB."
            )
            continue

        print(f"\n🚀 Processing new asset: {filename}...")

        try:
            reader = PdfReader(pdf_path)
            full_text_chunks = []

            for page_idx, page in enumerate(reader.pages):
                raw_text = page.extract_text()
                sanitized_text = clean_academic_text(raw_text)

                if sanitized_text.strip():
                    page_chunks = text_splitter.split_text(sanitized_text)
                    for chunk in page_chunks:
                        full_text_chunks.append({"text": chunk, "page": page_idx + 1})

            total_chunks = len(full_text_chunks)
            print(
                f"🧬 Structured text split complete. Generated {total_chunks} medical contexts."
            )

            if total_chunks == 0:
                print(f"⚠️ Warning: No parseable text found in '{filename}'.")
                continue

            print(
                f"🧠 Computing text vector spaces via local ThreadPool (Controlled Windows Sockets Profile)..."
            )
            success_count = 0

            # Sub-divide massive 20,000+ chunks into batches of 100 to prevent port crashing
            for batch_start in range(0, total_chunks, BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, total_chunks)
                batch_chunks = full_text_chunks[batch_start:batch_end]

                print(
                    f"   ↳ Ingesting chunk block {batch_start} to {batch_end} of {total_chunks}..."
                )

                # Dropping workers to 2-3 avoids exhausting the Windows port pool
                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = {
                        executor.submit(
                            process_single_chunk_with_retry,
                            batch_start + i,
                            chunk,
                            filename,
                        ): batch_start + i
                        for i, chunk in enumerate(batch_chunks)
                    }

                    for future in as_completed(futures):
                        chunk_idx = futures[future]
                        try:
                            if future.result():
                                success_count += 1
                        except Exception as exc:
                            print(
                                f"\n❌ Critical network socket lock-up occurred at chunk index {chunk_idx}: {exc}"
                            )
                            print(
                                "❗ Ingestion paused. Your current progress has been saved natively inside ChromaDB."
                            )
                            return

                # Cool-down breather to let the Windows OS clear out lingering socket connections safely
                time.sleep(0.5)

            # Verification Commit Check
            if success_count == total_chunks:
                record_successful_ingestion(file_hash, filename, total_chunks)
                print(
                    f"✅ Successfully synchronized all {total_chunks} text vectors from '{filename}' into ChromaDB."
                )
            else:
                print(
                    f"⚠️ Ingestion incomplete ({success_count}/{total_chunks} processed). Duplicate tracking log omitted."
                )

        except Exception as e:
            print(f"❌ Failed to parse pipeline metrics across {filename}: {str(e)}")


if __name__ == "__main__":
    process_and_ingest_pdfs()
