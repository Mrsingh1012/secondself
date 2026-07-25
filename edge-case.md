# Edge Cases & Corner Scenarios: SecondSelf — Your Personal AI Second Brain

This document lists potential edge cases, failure modes, and developer mitigations across each component of the SecondSelf project.

---

## 1. Capture Pipeline (`capture.py`)

### 1.1 URL Scraping Blocked
- **Scenario**: A user attempts to capture a link (e.g., Medium, LinkedIn, or NYTimes) that is protected by Cloudflare, requires login, or enforces rate limits.
- **Impact**: Request returns a `403 Forbidden` or `401 Unauthorized` HTML payload rather than the content.
- **Mitigation**:
  - Use custom User-Agent headers simulating a real browser.
  - If scraping returns a non-200 status or empty text, capture the URL and metadata (title/domain) but leave `content` empty and write a note: *"Scraping blocked. URL stored for manual viewing."*
  - Do not crash the CLI; exit cleanly with a warning.

### 1.2 Binary and Non-Text Files
- **Scenario**: User captures a binary file (e.g., `.png`, `.zip`, `.dmg`) using `--file`.
- **Impact**: Text extraction libraries crash, or output massive garbage binary strings.
- **Mitigation**:
  - Filter input files by file extension or MIME type.
  - If a file is not a supported text type (e.g., `.txt`, `.md`, `.pdf`, `.docx`), copy the file to `raw/attachments/` and write a standard JSON descriptor in `raw/` pointing to the attachment path, without parsing.

### 1.3 Empty Captures
- **Scenario**: CLI called with empty values like `python capture.py --note ""` or empty files.
- **Impact**: Saves empty JSON payloads.
- **Mitigation**:
  - Enforce character/byte minimums (e.g., content must be >= 3 characters). Reject empty arguments.

---

## 2. AI Classifier (`classify.py`)

### 2.1 API Key Missing / Groq Rate Limits
- **Scenario**: `GROQ_API_KEY` is not set, or the free-tier rate limits are exceeded (RPM/TPM).
- **Impact**: Pipeline execution halts with an unhandled exception.
- **Mitigation**:
  - Check for environment variables at startup. If missing, fail gracefully.
  - Implement a simple sleep-retry loop (exponential backoff) for `429 Too Many Requests` errors.

### 2.2 Malformed LLM Response
- **Scenario**: LLM does not return clean JSON output for category, tags, and summary, or wraps it in extra conversational text.
- **Impact**: JSON parser crashes.
- **Mitigation**:
  - Use system prompt rules enforcing *"Return ONLY raw JSON. No conversational wrapper or markdown backticks."*
  - Set `response_format={"type": "json_object"}` in the Groq API call.
  - Use a try-except parser. On failure, fall back to default metadata: Category: `Resources`, Tags: `["uncategorized"]`, Summary: `None`.

### 2.3 Exceeding LLM Context Window
- **Scenario**: A large PDF (e.g., a 100-page book) is captured.
- **Impact**: LLM request fails due to context limits.
- **Mitigation**:
  - Truncate text before sending to LLM (e.g., take the first 4,000 characters for classification, as it usually contains headers/intro).

---

## 3. Semantic Linker (`link.py`)

### 3.1 Single Note / Cold Start
- **Scenario**: The user runs `link.py` when only a single note exists in `wiki/`.
- **Impact**: Comparing 1 note to itself results in 100% similarity, adding a self-reference.
- **Mitigation**:
  - If folder contains fewer than 2 files, exit the linking script gracefully without processing.

### 3.2 Duplicate / Infinite Linking
- **Scenario**: Running `link.py` repeatedly appends the same links to the bottom of the files.
- **Impact**: The Related Connections section grows infinitely with duplicates.
- **Mitigation**:
  - Parse the markdown file body first. If `[[related-uuid]]` is already present, do not append it.
  - Ensure links are written only once.

### 3.3 Semantic Noise (Low Similarity Links)
- **Scenario**: Unrelated notes get linked because similarity is marginally high.
- **Impact**: Spurious lines clutter the graph representation.
- **Mitigation**:
  - Calibrate cosine similarity threshold (default `0.50`). Allow setting a custom threshold via config/argument.

---

## 4. Graph Builder (`build_graph.py`)

### 4.1 Dangling Edges
- **Scenario**: User deletes a wiki file, but another file still references its UUID.
- **Impact**: Graph visualization shows nodes linking to invisible targets.
- **Mitigation**:
  - When parsing connections, check if the target UUID exists in the node list. If not, discard the edge.

### 4.2 Self-Looping Node
- **Scenario**: A note links to itself.
- **Impact**: Visual clutter (edges pointing to self).
- **Mitigation**:
  - Filter out edges where `from_id == to_id`.

---

## 5. RAG Semantic Q&A (`ask.py`)

### 5.1 Out-of-Domain / Irrelevant Query
- **Scenario**: User asks: *"What is the meaning of life?"* or *"Who won the match?"* when their notes contain only programming syntax.
- **Impact**: System retrieves nearest notes and summarizes them, resulting in hallucinated/incorrect responses.
- **Mitigation**:
  - Filter retrieved notes. If the maximum similarity score of top-K results is below a strict retrieval threshold (e.g. `0.35`), do not query the LLM. Instead, return: *"I couldn't find any relevant notes matching your query."*

### 5.2 Context Window Overflow
- **Scenario**: RAG retrieves 3 large notes, and combined context size exceeds the token limit.
- **Impact**: LLM API fails.
- **Mitigation**:
  - Truncate context per note (e.g., take first 1,500 words per note).

---

## 6. Streamlit UI (`app.py`)

### 6.1 Performance and Graph Bloat
- **Scenario**: User has 500+ notes. Rendering 500 nodes and 2000 edges in the browser causes browser lag.
- **Impact**: The app freezes.
- **Mitigation**:
  - Enable `stabilization: true` and set physics iterations in `vis-network`. Once stabilized, disable physics updates so dragging doesn't recalculate the entire graph layout continually.
