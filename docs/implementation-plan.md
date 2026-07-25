# Implementation Plan: SecondSelf — Your Personal AI Second Brain

This document details the step-by-step implementation plan for building the **SecondSelf** personal AI knowledge base, starting from empty project setup to a deployed Streamlit application.

---

## User Review Required

> [!IMPORTANT]
> The auto-classification and semantic search Q&A require access to a Large Language Model. We plan to use the **Groq Cloud API** (`llama-3.1-8b-instant`), which is fast and offers a free tier. You will need to obtain a Groq API key and place it in the `.env` file under the key `GROQ_API_KEY`.
>
> For embeddings, we will use a local sentence-transformer model `all-MiniLM-L6-v2`, which runs 100% locally on CPU without needing API keys or GPU resources.

---

## Open Questions

> [!NOTE]
> 1. Do you already have a Groq API Key, or would you prefer to use another LLM provider (e.g., Gemini API, OpenAI API)? *We recommend Groq API with Llama 3 as it fits the problem statement's suggestion for a free LLM.*
> 2. Will you be deploying the project to **Streamlit Community Cloud** (which connects directly to a GitHub repository)? If so, we will format files like `.gitignore` and `requirements.txt` to ensure direct compatibility.

---

## Proposed Changes

We will build the system in 10 sequential phases.

### Phase 0: Project Setup & Scaffolding
Initialize the workspace structure, dependencies, and environment configuration.
- **Goal**: Establish the initial folders and virtual environment configuration.
- **Files**:
  - `[NEW]` [requirements.txt](file:///C:/Users/anand/.gemini/antigravity-ide/scratch/secondself/requirements.txt)
  - `[NEW]` [.env.example](file:///C:/Users/anand/.gemini/antigravity-ide/scratch/secondself/.env.example)
  - `[NEW]` [.gitignore](file:///C:/Users/anand/.gemini/antigravity-ide/scratch/secondself/.gitignore)

---

### Phase 1: Capture Pipeline (`capture.py`)
Implement the ingestion script that can accept a note, link, or file and write raw JSON to `raw/`.
- **Goal**: Support `--note`, `--link` (with basic web scraping), and `--file` (with PDF/txt parsing).
- **Files**:
  - `[NEW]` [capture.py](file:///C:/Users/anand/.gemini/antigravity-ide/scratch/secondself/capture.py)

---

### Phase 2: AI PARA Classifier (`classify.py`)
Write the classification pipeline that interacts with the LLM to filter, structure, and categorize raw files using the PARA framework.
- **Goal**: Scan `raw/`, call Groq LLM, extract frontmatter info, and write initial markdown files to `wiki/`.
- **Files**:
  - `[NEW]` [classify.py](file:///C:/Users/anand/.gemini/antigravity-ide/scratch/secondself/classify.py)

---

### Phase 3: Semantic Linker Engine (`link.py`)
Implement automatic bidirectional linking based on cosine similarity of note content.
- **Goal**: Generate embeddings using local `sentence-transformers`, calculate pairwise similarities, and append wikilinks to matching markdown files.
- **Files**:
  - `[NEW]` [link.py](file:///C:/Users/anand/.gemini/antigravity-ide/scratch/secondself/link.py)

---

### Phase 4: Graph Data Compiler (`build_graph.py`)
Compile the wiki files and their linking structures into a JSON file for front-end rendering.
- **Goal**: Create nodes (categorized by PARA) and links, and save to `graph.json`.
- **Files**:
  - `[NEW]` [build_graph.py](file:///C:/Users/anand/.gemini/antigravity-ide/scratch/secondself/build_graph.py)

---

### Phase 5: RAG Semantic Q&A (`ask.py`)
Provide natural language query answers by retrieving top-K matching notes and passing them to Llama 3 for synthesis.
- **Goal**: Compute query embeddings, retrieve context, format prompt, and run Q&A synthesis.
- **Files**:
  - `[NEW]` [ask.py](file:///C:/Users/anand/.gemini/antigravity-ide/scratch/secondself/ask.py)

---

### Phase 6: Streamlit UI Dashboard (`app.py`)
Assemble everything into a two-column Streamlit application.
- **Goal**: Implement visual force-directed graph (via HTML iframe utilizing `vis-network.js`) and a chat console interface.
- **Files**:
  - `[NEW]` [app.py](file:///C:/Users/anand/.gemini/antigravity-ide/scratch/secondself/app.py)

---

### Phase 7: Local Validation & Iterative Testing
Verify the pipeline end-to-end locally.
- **Goal**: Ingest 15+ real-world notes, run classification, similarity linking, graph compilation, and query testing.

---

### Phase 8: Deployment & Environment Configuration
Deploy the project to a public platform.
- **Goal**: Publish to Streamlit Cloud or Hugging Face Spaces and wire environment secrets.

---

### Phase 9: Final Review & Documentation
Complete documentation and publish code.
- **Goal**: Write detailed setup instructions in `README.md` and complete code cleanup.
- **Files**:
  - `[NEW]` [README.md](file:///C:/Users/anand/.gemini/antigravity-ide/scratch/secondself/README.md)

---

## Verification Plan

### Automated Tests
- Since this is an AI pipeline, we will use validation scripts to test components individually:
  - **Capture verification**: `python capture.py` and inspect `raw/` files.
  - **Classification verification**: `python classify.py` and verify YAML frontmatter formatting.
  - **Embedding & Linking verification**: Check `wiki/` notes for newly appended `[[uuid]]` related connections.
  - **Q&A verification**: Run `python ask.py --query "What is the second brain project?"` and print the source-referenced answers to console.

### Manual Verification
- Deploy Streamlit locally via `streamlit run app.py`.
- Interact with the force-directed graph (drag, zoom, hover) to verify aesthetic requirements (colors, tooltips, pulses).
- Input multiple test questions to verify semantic Q&A UI formatting.
