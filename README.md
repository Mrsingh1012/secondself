# SecondSelf — Your Personal AI Second Brain

Every notes app fails the same way: you capture notes, bookmarks, and files, and then you never find them again. **SecondSelf** is a self-organizing personal knowledge base. It automatically categorizes your captures using the PARA framework, semantically links related concepts using local embeddings, compiles them into a force-directed interactive knowledge graph, and provides a conversational RAG Q&A interface over everything you know.

---

## 🌟 Key Features

1. **Capture Pipeline (`capture.py`)**: One-command ingestion script that takes notes, scraping target URLs, or reading text, docx, and PDF files.
2. **AI PARA Classifier (`classify.py`)**: Sends raw items to a Groq Cloud LLM (`llama-3.1-8b-instant`) to classify items into PARA categories (**Projects**, **Areas**, **Resources**, **Archives**), generating tags and summaries.
3. **Semantic Linker (`link.py`)**: Computes local text embeddings using `sentence-transformers/all-MiniLM-L6-v2` and auto-inserts connections (`[[related-id]]`) based on similarity.
4. **Interactive Knowledge Graph (`build_graph.py` & `app.py`)**: Builds a nodes-and-edges data model visualized in a glowing force-directed graph.
5. **Retrieval-Augmented Q&A (`ask.py`)**: Answers plain English questions by retrieving semantically relevant notes and synthesizing responses with citations.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+
- **LLM API**: Groq Cloud API (Llama 3)
- **Local Embeddings**: `sentence-transformers` (all-MiniLM-L6-v2)
- **UI Engine**: Streamlit
- **Graph Renderer**: `vis-network.js` via dynamic iframe injection

---

## 🚀 Setup Instructions

### 1. Clone & Initialize Directory
Ensure you are in the project folder root:
```bash
git init
```

### 2. Configure Virtual Environment & Dependencies
Create a Python virtual environment and install the required libraries:
```bash
# Create venv
python -m venv .venv

# Activate venv (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate venv (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Environment variables
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your **Groq API Key**:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
SIMILARITY_THRESHOLD=0.50
```
*Note: If `GROQ_API_KEY` is not provided, the system runs in a local fallback mode where it uses local keyword heuristics for classification and snippet extraction for search.*

---

## 📖 Usage Guide

### 1. Capture Content
Use `capture.py` to ingest different data types:
```bash
# Capture a simple text note
python capture.py --note "Read 10 pages of Deep Learning book on transformers tonight"

# Capture a web link (content will be scraped and stored)
python capture.py --link "https://en.wikipedia.org/wiki/Cosine_similarity"

# Capture a PDF/txt/docx file
python capture.py --file "path/to/my_notes.pdf"
```

### 2. Run the Classification & Linking Pipeline
Run these commands to organize the ingested raw files and build the visualization graph:
```bash
# 1. Classify raw entries into PARA markdown notes
python classify.py

# 2. Semantic-link related notes using embeddings
python link.py

# 3. Compile notes and connections into graph.json
python build_graph.py
```

### 3. Ask Questions (CLI)
Query your accumulated knowledge via command line:
```bash
python ask.py "What are my goals for Q3?"
```

### 4. Open the Streamlit App (UI)
Start the dashboard to browse the interactive graph and use the Q&A search console:
```bash
streamlit run app.py
```
This will open the dashboard in your default web browser (usually at `http://localhost:8501`).

---

## 📁 Repository Structure
```text
secondself/
├── docs/
│   ├── architecture.md           # Technical architecture layout
│   ├── implementation-plan.md     # Phase-by-phase building blocks
│   └── edge-case.md               # Analysis of edge cases and mitigations
├── raw/                           # Raw ingested captures (JSON)
├── wiki/                          # Processed PARA markdown notes
├── capture.py                     # CLI capture tool
├── classify.py                    # PARA categorization script
├── link.py                        # Semantic embedding auto-linking
├── build_graph.py                 # Graph node/edge compiler
├── graph.json                     # Generated graph data
├── ask.py                         # Semantic retrieval Q&A
├── app.py                         # Streamlit UI dashboard
├── requirements.txt               # Dependencies
└── README.md                      # Setup instructions
```
