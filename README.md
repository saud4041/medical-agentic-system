Here is the complete, professional README.md file for your GitHub repository. It contains markdown tables, clean setups, code blocks, and visual guides to ensure anyone cloning your project can set it up locally on their machine without friction.
## README.md

# 🩺 Multi-Agent Local Medical AI Assistant
An advanced, privacy-first medical decision-support ecosystem built for university research. This project uses a **Multi-Agent Router Architecture** to coordinate between a structured relational database (**SQLite**) and an unstructured clinical vector store (**ChromaDB**). The entire workflow runs completely locally using **LangGraph**, **Streamlit**, and **Ollama** powered by **DeepSeek-R1**.
---## 🏗️ Architecture Overview
The system employs an automated supervisor workflow to dynamically analyze clinical inquiries and delegate tasks to specialized agents:


┌─────────────────────────┐
│ User Intersace (UI) │
│ (Streamlit) │
└────────────┬────────────┘
│
[Clinical Query]
▼
┌─────────────────────────┐
│ Supervisor Router │
│ (LangGraph Node) │
└──────┬───────────┬──────┘
│ │
[Relational Lookup] [Clinical Guideline Query]
▼ ▼
┌───────────────────┐ ┌───────────────────┐
│ Database Agent │ │ Medical RAG Agent│
│ (SQLite Store) │ │ (ChromaDB) │
└───────────────────┘ └───────────────────┘


| Component | Technology | Responsibility |
| :--- | :--- | :--- |
| **Orchestrator** | `LangGraph` | Manages state transitions and conditional routing between nodes. |
| **Local LLM** | `Ollama (DeepSeek-R1)` | Handles locally processed clinical reasoning and query evaluation. |
| **Vector Index**| `ChromaDB` | Houses chunked textbook guidelines and academic reference papers. |
| **Structured DB**| `SQLite` | Tracks historical electronic health records (EHR) and triage logs. |
| **Package Manager**| `uv` | Provides fast, reproducible cross-platform dependency tracking. |
| **UI Layer** | `Streamlit` | Exposes a professional medical dashboard chat interface. |

---

## ⚡ Quick Start (Local Deployment)

### Prerequisites
1. **Python 3.11 or higher** installed on your host system.
2. **Ollama** engine installed. Download it from [ollama.com](https://ollama.com).
3. **uv** package manager installed. Install it via terminal:
   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy Bypass -Command "iwr -useb https://astral.sh | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh | sh
   ```

---

### Step-by-Step Installation

#### 1. Clone the Repository
```bash
git clone https://github.com
cd medical-multi-agent
```

#### 2. Configure Local Language Models
Open your terminal and pull the desired DeepSeek model size (Ensure the Ollama desktop engine application is running in the background):
```bash
ollama run deepseek-r1:7b
```

#### 3. Set Up Environment Variables
Create a file named `.env` in the project root directory and add the configuration paths:
```env
DB_PATH=database/medical_records.db
CHROMA_DIR=vectorstore/chroma_data
LLM_MODEL=deepseek-r1:7b
```

#### 4. Parse & Ingest Medical Literature
Drop any target clinical encyclopedia files, medical papers, or reference PDFs directly inside the `knowledgebase/` folder. Then, execute the layout-aware ingestion pipeline tracker:
```bash
# Creates directory layout if missing
mkdir -p knowledgebase

# Execute the background parser worker engine
uv run python -m src.ingest_knowledge
```
*Note: This script uses an internal SQLite tracking configuration to automatically skip duplicate files on subsequent runs.*

#### 5. Launch the Clinical Dashboard
Run the Streamlit frontend user interface:
```bash
uv run streamlit run src/app.py
```
The application will automatically initialize a mock dataset (including sample patients like John Doe and Jane Smith) and open in your default browser at `http://localhost:8501`.

---

## 🔬 Sample Queries for Testing

You can use these example inputs in the Chat UI to test how the supervisor routes queries between agents:

*   **Test Database Routing Agent:** 
    *   *Input:* `"Show me the historic clinical symptoms and known drug allergies logged for patient John Doe."*
    *   *Behavior:* The supervisor identifies the specific patient profile lookup intent, calls the SQLite connector, and summarizes their recorded case history.
*   **Test Medical RAG Agent:** 
    *   *Input:* `"What is the standard frontline pharmacological management strategy for a patient diagnosed with severe chronic hypertension?"*
    *   *Behavior:* The supervisor recognizes the abstract educational nature of the query, retrieves matching paragraphs from your ingested PDFs in ChromaDB, and returns an evidence-based clinical summary.

---

## 🛠️ Project File Architecture

```text
medical-multi-agent/
├── database/            # Automated SQLite relational storage home
├── vectorstore/         # Persistent ChromaDB collections home
├── knowledgebase/       # Workspace for encyclopedia & research PDFs
├── prompts/             # System instructions separated from logic
│   └── prompts.py
├── flows/               # Visual Langflow pipeline backup configurations
│   └── pipeline.json
├── src/                 # Core Python source application files
│   ├── config.py
│   ├── database.py
│   ├── rag_engine.py
│   ├── graph.py
│   └── app.py
├── COMMANDS.md          # Complete comprehensive terminal cheat sheet
├── pyproject.toml       # Managed project dependency constraints
└── README.md            # Repository documentation guide
```

---

## 🤝 Contribution & Evaluation

This platform is structured as an extensible academic framework. For deep command execution breakdowns, variable flushing techniques, or visual graph flow rendering commands, please consult the accompanying [COMMANDS.md](./COMMANDS.md) tracking index.

Would you like me to help you write a GitHub Actions workflow file (.github/workflows/ci.yml) so that your project automatically runs unit tests every time you push code to GitHub?

