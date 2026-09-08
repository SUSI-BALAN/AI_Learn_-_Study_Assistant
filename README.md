# AI Learning & Study Assistant

Offline-first Python terminal assistant for local study chat, persistent memory,
and document vector search.

Run it with:

```powershell
python main.py
```

## Features

- Local chat through Ollama
- Primary model: `qwen2.5:3b`
- Fallback model: `tinyllama`
- SQLite structured memory at `data/assistant.db`
- ChromaDB semantic/vector memory for indexed documents
- PDF, TXT, Markdown, DOCX, and PPTX loaders
- Source-aware RAG foundation
- Deterministic calculator routing
- English, Tamil, and Thanglish response guidance
- Terminal-only interface
- No MongoDB requirement

## Memory Design

The project uses three separate memory layers:

- RAM: active short-term conversation context
- SQLite: persistent structured memory, conversations, profile, facts, and learning records
- ChromaDB: semantic search over indexed study documents

`/clear` clears only the current RAM context. It does not delete SQLite history,
stored memory facts, progress data, or ChromaDB documents.

## Setup

Prerequisites:

- Python 3.10+
- Ollama
- `qwen2.5:3b`
- `tinyllama`

Install and prepare:

```powershell
ollama pull qwen2.5:3b
ollama pull tinyllama
Copy-Item .env.example .env
python -m pip install -r requirements.txt
python main.py
```

If Ollama is installed but not running, start it in another terminal:

```powershell
ollama serve
```

SQLite is created automatically at `data/assistant.db`. No database server is
needed.

## Commands

```text
/help           Show command help
/setup          Show beginner setup steps
/status         Show startup health again
/memory         Show important stored memory facts
/history        Show recent persisted messages
/conversations  Show previous conversation sessions
/profile        Show the stored local profile
/clear          Clear current RAM conversation context only
/exit           Exit safely
```

Natural exit words also close the app:

```text
bye
goodbye
leave
quit
exit
close
```

## Documents And RAG

Place supported study files in:

```text
data/documents
```

Index them with:

```powershell
python ingest.py
```

ChromaDB stores document chunks, metadata, and vectors in `data/chroma`.
Explicit material-based questions such as "according to my uploaded notes" use
RAG. If no useful document evidence is found, the assistant reports insufficient
evidence instead of inventing a document-based answer.

## Verification

Run all tests:

```powershell
python -m unittest discover -v
```

Run the local service health check:

```powershell
python test_setup.py
```

Expected startup health includes:

```text
Python      : VERIFIED
Ollama      : VERIFIED
Model       : qwen2.5:3b (VERIFIED)
SQLite      : VERIFIED
ChromaDB    : VERIFIED
Memory      : VERIFIED
Language    : auto
```

## Troubleshooting

If `Ollama` is `FAILED`, run:

```powershell
ollama serve
```

If the model is missing, run:

```powershell
ollama pull qwen2.5:3b
ollama pull tinyllama
```

If SQLite is `FAILED`, make sure the project folder is writable and restart:

```powershell
python main.py
```

