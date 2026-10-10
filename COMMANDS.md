# Project Command Execution Reference Manual

This document details all terminal operations required to manage dependencies, host the local language model, ingest clinical assets, view flow maps, and launch the decision ecosystem.

---

## 1. Environment & Dependency Management (uv)

### Initializing the Project Sandbox
```bash
# Initialize a pristine Python workspace environment managed by uv
uv init medical-ai-agent
cd medical-ai-agent
```

### Adding Core Runtime Dependencies
```bash
# Add fundamental LangChain and LangGraph coordination libraries
uv add langchain langchain-community langchain-ollama langgraph

# Add user interface, local embedding databases, and parser layers
uv add streamlit chromadb pypdf fonttools fonttools grandalf python-dotenv
```

### Cleaning Deprecated Workspaces (Troubleshooting)
If `pysqlite3-binary` was added erroneously on a Windows host platform, strip it from your configuration definitions:
```bash
uv remove pysqlite3-binary
```

---

## 2. Local Language Model Orchestration (Ollama)

Ensure the background engine service is active before running any embedding passes or chat sessions.

```bash
# Start the local Ollama hosting engine daemon
ollama serve

# Download and pull your specific DeepSeek reasoning model engine 
# (Run this in a separate terminal window)
ollama run deepseek-r1:7b
```

---

## 3. Knowledge Base Parsing & Ingestion

Always execute scripts using Python's module activation flag (`-m`) from the main root path to prevent internal `ModuleNotFoundError` resolution anomalies.

```bash
# 1. Establish the document workspace layout directory
mkdir -p knowledgebase

# [Action] Drop your 'The-Gale-Encyclopedia-of-Medicine-3rd-Edition.pdf' into the folder

# 2. Run the concurrent layout-aware chunking and background vector ingestion pipeline
uv run python -m src.ingest_knowledge
```

---

## 4. Visual Pipeline Automation (Langflow)

To debug, test, or dynamically map out structural prompt component pathways inside a visual canvas board interface:

```bash
# Launch the interactive Langflow designer server canvas
uv run langflow run --host 127.0.0.1 --port 7860
```
*Open your web browser to `http://127.0.0.1:7860` and use the "Upload/Import" function to load your `flows/pipeline.json` blueprint configuration layer.*

---

## 5. Exporting LangGraph Structure as an Image

To visualize your multi-agent architecture (Supervisor, DB Agent, RAG Agent), generate an asset image using this command snippet.

### Step 1: Install System Draw Dependency
```bash
uv add grandalf
```

### Step 2: Run the Image Generation Script
Execute this inline code block to generate a visual schematic diagram of your cognitive agent structure:

```bash
uv run python -c "
from src.graph import medical_agent_graph
import os

try:
    img_data = medical_agent_graph.get_graph().draw_mermaid_png()
    with open('medical_agent_graph.png', 'wb') as f:
        f.write(img_data)
    print('🎨 LangGraph flowchart successfully rendered and saved as: medical_agent_graph.png')
except Exception as e:
    print('❌ Image generation failed:', str(e))
    print('💡 Fallback - Printing Graph Structure text representation:\n')
    medical_agent_graph.get_graph().print_ascii()
"
```

---

## 6. Vector Database Administration (ChromaDB)

Because ChromaDB is integrated natively through SQLite storage spaces via our application modules, administration tasks can be triggered using simple terminal commands:

### Verify Vector Metadata Content
```bash
uv run python -c "
import chromadb
from src.config import CHROMA_DIR
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_collection('medical_knowledge')
print(f'📊 Active Vector Collections Detected: {client.list_collections()}')
print(f'🧬 Total Count of Successfully Indexed Document Chunks: {collection.count()}')
"
```

### Reset Vector Database Content
If you need to clear the vector index to test a new chunking profile:
```bash
uv run python -c "
import chromadb
from src.config import CHROMA_DIR
client = chromadb.PersistentClient(path=CHROMA_DIR)
try:
    client.delete_collection('medical_knowledge')
    print('🧹 ChromaDB text collection flushed completely.')
except Exception as e:
    print('Collection not found:', e)
"
```

---

## 7. Launching the Multi-Agent Application UI

Run this command from your root directory to launch the interactive Streamlit medical decision-support dashboard interface:

```bash
uv run streamlit run src/app.py
```
---
## 8. Langflow
```bash
uvx langflow run --host 127.0.0.1 --port 7860
```

---
## 9. State Graph Generation
```bash
uv run python graph_gen.py
```