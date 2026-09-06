# MASTER PROMPT — AI Learning & Study Assistant

## 0. How Codex Must Use This File

This file is the **single source of truth** for the entire project.

Codex must:

1. Read this file before creating, editing, deleting, or moving project files.
2. Build the project in small verified phases.
3. Keep the project **terminal-only**.
4. Use **Python + Ollama + Qwen 2.5 3B (TinyLlama fallback) + MongoDB + ChromaDB**.
5. Keep the application **offline by default**.
6. Never silently change the agreed architecture.
7. Reuse existing code instead of creating duplicate implementations.
8. Keep each Python file focused on one responsibility.
9. Test each important feature after implementation.
10. Update the **File Responsibility Registry** in this same Markdown file whenever a project file is added, removed, renamed, or its purpose changes.
11. Do not create unnecessary folders or placeholder files.
12. Never place secrets directly in source code. Use `.env`.
13. Never delete user data, MongoDB data, ChromaDB data, or uploaded study documents unless explicitly requested.
14. Before implementing a large change, inspect the existing codebase and explain what files will be changed.
15. After every implementation step, report:
    - files created
    - files modified
    - what each change does
    - how to test it
    - status: VERIFIED / WARNING / FAILED

---

# 1. Project Name

**AI Learning & Study Assistant**

### Core concept

A local Python terminal chatbot that helps a student learn any topic using:

- Ollama
- Qwen 2.5 3B, with TinyLlama as a fallback
- RAG
- ChromaDB
- MongoDB memory
- learning tools
- study planning
- quizzes
- progress tracking
- weak-topic detection
- multilingual answers

The user starts the application with:

```bash
python main.py
```

The project must remain usable without a web browser.

---

# 2. Fixed Project Decisions

These requirements are already decided.

Do not ask again unless implementation becomes technically impossible.

| Area | Fixed Decision |
|---|---|
| Main language | Python |
| Interface | Terminal only |
| Local AI runtime | Ollama |
| Primary LLM | qwen2.5:3b |
| Fallback LLM | tinyllama |
| User count | One local user |
| Main database | MongoDB |
| Vector database | ChromaDB |
| Operation | Offline by default |
| Internet | Optional later, disabled by default |
| RAG files | PDF, TXT, Markdown, DOCX, PPTX |
| Supported learning | Any learning topic |
| Languages | English, Tamil, Thanglish |
| Quiz difficulty | Easy, Medium, Hard |
| Memory | Persistent |
| AI routing | Automatic where practical |
| RAG sources | Show source information when available |
| Grounded RAG | Do not invent missing course-material information |

---

# 3. Main Objectives

The application must be able to:

1. Chat with the student.
2. Explain concepts in simple language.
3. Answer academic and general learning questions.
4. Read the student's learning materials.
5. Retrieve relevant content using RAG.
6. Show source file/page/slide/section information when possible.
7. Remember previous conversations.
8. Remember subjects and topics.
9. Track completed topics.
10. Track quiz performance.
11. Detect weak topics.
12. Create study plans.
13. Create revision plans.
14. Generate quizzes.
15. Generate flashcards.
16. Search notes.
17. Search PDFs.
18. Analyze syllabi.
19. Track learning progress.
20. Answer in English, Tamil, or Thanglish.
21. Work locally without requiring an online AI API.
22. Allow optional internet search only in a later phase.

---

# 4. Important Architecture Rule

Do not use TinyLlama for deterministic tasks that Python can perform more reliably.

Use **Python** for:

- calculations
- quiz scoring
- percentage calculations
- progress calculations
- date calculations
- file validation
- document parsing
- database updates
- retrieval logic
- weak-topic scoring
- command parsing
- system health checks

Use the configured **Ollama model** mainly for:

- natural-language explanations
- summarization
- question generation
- tutoring
- rewriting
- study guidance
- generating natural responses
- interpreting user intent when deterministic routing is insufficient

---

# 5. High-Level System Architecture

```text
USER
  |
  v
Python Terminal CLI
  |
  v
Input Processor
  |
  +--> Command Detection
  |
  +--> Language Detection
  |
  v
AI / Intent Router
  |
  +--------------------+--------------------+----------------------+
  |                    |                    |                      |
  v                    v                    v                      v
Normal Chat          RAG Search          Memory                  Tools
  |                    |                    |                      |
  |                 ChromaDB             MongoDB       +----------+-----------+
  |                    |                    |           |          |           |
  |             Relevant Chunks            |       Quiz Tool   Planner     Calculator
  |                    |                    |           ...
  +--------------------+--------------------+----------------------+
                               |
                               v
                         Context Builder
                               |
                               v
                            Ollama
                               |
                               v
                          TinyLlama
                               |
                               v
                      Response Validator
                               |
                    +----------+----------+
                    |                     |
                    v                     v
               Final Answer          RAG Sources
                    |
                    v
                  USER
```

---

# 6. Core Routing Intents

The router should support these logical intents:

```text
NORMAL_CHAT
RAG_SEARCH
MEMORY_SEARCH
CALCULATOR
QUIZ
STUDY_PLAN
REVISION_PLAN
NOTES_SEARCH
PDF_SEARCH
PROGRESS
WEAK_TOPIC
FLASHCARD
SYLLABUS
DOCUMENT_ADD
DOCUMENT_LIST
HELP
SETTINGS
INTERNET_SEARCH
```

`INTERNET_SEARCH` must remain disabled until the offline system is stable.

Natural-language input should work.

Examples:

```text
"Explain DBMS normalization"
    -> NORMAL_CHAT or RAG_SEARCH depending on context

"According to my uploaded notes, explain normalization"
    -> RAG_SEARCH

"Give me a hard Python quiz"
    -> QUIZ

"What is my weakest DBMS topic?"
    -> WEAK_TOPIC

"Create a 7-day study plan for Network Security"
    -> STUDY_PLAN

"What did I study yesterday?"
    -> MEMORY_SEARCH
```

Slash commands may also be supported.

---

# 7. Terminal Commands

Recommended commands:

```text
/chat
/learn
/explain
/quiz
/plan
/revise
/progress
/weak
/flashcards
/syllabus
/add
/documents
/search
/memory
/settings
/help
/clear
/exit
```

Commands are shortcuts only.

The student must also be able to ask the same actions naturally.

---

# 8. Startup Health Check

At application start, verify:

```text
[✓] Python
[✓] Ollama connection
[✓] TinyLlama installed
[✓] MongoDB connection
[✓] ChromaDB available
[✓] document directory available
[!] internet search disabled
```

Use:

- `VERIFIED`
- `WARNING`
- `FAILED`
- `NOT TESTED`

Do not crash with a long stack trace for normal user-facing failures.

Show a simple explanation and useful recovery action.

---

# 9. Ollama Requirements

Default configuration:

```env
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_FALLBACK_MODEL=tinyllama
```

Rules:

1. Keep model name configurable.
2. Do not hardcode TinyLlama throughout the application.
3. Put Ollama communication inside one client/service layer.
4. Handle Ollama-not-running errors gracefully.
5. Preserve conversation context without sending an unlimited history.
6. Later allow replacing TinyLlama with a stronger local model without changing the rest of the architecture.

---

# 10. MongoDB Responsibilities

MongoDB stores persistent application and student data.

Recommended database name:

```text
ai_learning_assistant
```

Recommended collections:

```text
user
subjects
topics
conversations
messages
documents
quiz_results
study_plans
study_sessions
progress
weak_topics
flashcards
learning_goals
tool_history
settings
```

MongoDB stores structured information.

Do not use ChromaDB as a replacement for MongoDB.

---

# 11. Memory Requirements

Persist:

- student name
- language preference
- subjects
- previous conversations
- current learning topics
- completed topics
- weak topics
- strong topics
- quiz scores
- study goals
- study plans
- revision history
- learning preferences
- document metadata
- recent questions
- learning progress

Use:

### Short-term memory

Current conversation context.

### Long-term memory

MongoDB.

Do not load the entire MongoDB history into every LLM request.

Retrieve only context relevant to the current question.

---

# 12. ChromaDB Responsibilities

ChromaDB is used only for vector-based semantic retrieval.

The Phase 4 embedding backend is ChromaDB's local ONNX `all-MiniLM-L6-v2`
model (384 dimensions). It requires a one-time model download and operates
offline afterward. TinyLlama remains the configurable chat/tutoring model.

Each vector record should contain useful metadata such as:

```text
document_id
file_name
file_type
subject
topic
page_number
slide_number
section
chunk_index
chunk_text
```

The exact metadata depends on the source format.

---

# 13. RAG Pipeline

Required flow:

```text
Document
   |
   v
File Type Detection
   |
   v
Document Loader
   |
   v
Text Extraction
   |
   v
Text Cleaning
   |
   v
Chunking
   |
   v
Embedding Generation
   |
   v
ChromaDB Storage
```

Question flow:

```text
User Question
   |
   v
Query Embedding
   |
   v
ChromaDB Similarity Search
   |
   v
Relevant Chunks
   |
   v
Context Builder
   |
   v
TinyLlama
   |
   v
Grounded Answer
   |
   v
Source Information
```

---

# 14. Supported Document Types

Implement loaders for:

### PDF

Library suggestion:

```text
PyMuPDF
```

Track page numbers.

### DOCX

Library:

```text
python-docx
```

Track headings/sections where possible.

### PPTX

Library:

```text
python-pptx
```

Track slide numbers.

### TXT

Use standard Python file handling.

### Markdown

Use standard Python file handling.

Preserve useful headings when possible.

---

# 15. RAG Grounding Rules

If the user explicitly asks:

```text
"according to my notes"
"from my PDF"
"from uploaded material"
"in the document"
```

then the answer must be grounded in retrieved document content.

If evidence is insufficient, answer similarly to:

```text
I couldn't find enough information about this in your uploaded learning materials.
```

Do not fabricate course-material content.

Optionally ask:

```text
Would you like a general explanation instead?
```

General chat may use model knowledge.

---

# 16. RAG Source Format

When available:

### PDF

```text
Sources:
- Network_Security.pdf — Page 42
```

### PPTX

```text
Sources:
- Network_Security.pptx — Slide 18
```

### DOCX

```text
Sources:
- DBMS_Notes.docx — Section: Normalization
```

### TXT / MD

```text
Sources:
- python_notes.md — Heading: Loops
```

Do not invent page or section numbers.

---

# 17. Ten Required Tools

All ten are mandatory.

## Tool 1 — Calculator

Responsibilities:

- deterministic arithmetic
- no LLM math dependency for simple calculations
- safe expression handling

Example:

```text
User: Calculate 25 * 18
Result: 450
```

---

## Tool 2 — Quiz Generator

Support:

```text
Easy
Medium
Hard
```

Quiz engine must support:

- generated questions
- answer options where applicable
- student answer collection
- scoring
- result storage
- topic analysis
- feedback

Store results in MongoDB.

---

## Tool 3 — Study Planner

Inputs may include:

```text
subject
exam date
available days
daily available time
current progress
weak topics
difficulty
goals
```

Generate a realistic daily study schedule.

Store plans in MongoDB.

---

## Tool 4 — Revision Planner

Use:

- weak topics
- previous quiz results
- last revision date
- upcoming exam date
- completed topics
- available time

Generate today's or upcoming revision plan.

---

## Tool 5 — Notes Search

Search indexed note content.

Return:

- relevant text
- document name
- source information

---

## Tool 6 — PDF Search

Search specifically within PDF content.

Allow optional filtering by a specific PDF.

---

## Tool 7 — Progress Tracker

Track:

```text
subjects
topics
completion percentage
quiz averages
study sessions
completed work
remaining work
```

Use Python for progress calculations.

---

## Tool 8 — Weak Topic Detector

Analyze:

- quiz scores
- incorrect answers
- repeated mistakes
- low confidence
- incomplete topics
- revision performance

Return ranked weak topics.

---

## Tool 9 — Flashcard Generator

Generate flashcards from:

- a topic
- RAG content
- notes
- syllabus

Allow the user to rate each flashcard:

```text
Easy
Medium
Difficult
```

Use those ratings later for revision recommendations.

---

## Tool 10 — Syllabus Analyzer

Read syllabus documents and identify:

```text
subject
units
topics
subtopics
estimated difficulty
recommended order
study priorities
```

Store useful structure when appropriate.

---

# 18. Quiz Flow

Example:

```text
User: Give me a DBMS quiz

Assistant:
Choose difficulty:
1. Easy
2. Medium
3. Hard

User: 2

Assistant:
Question 1/10
...
```

At completion:

```text
Score: 8/10
Percentage: 80%

Strong:
- Normalization

Needs revision:
- BCNF
- Functional dependency
```

Store the quiz result.

Update progress/weak-topic data when appropriate.

---

# 19. Study Planner Flow

Example input:

```text
Subject: DBMS
Exam date: 20-09-2026
Daily available time: 2 hours
```

System checks:

```text
current progress
remaining topics
weak topics
available days
available minutes
```

Then produces a plan.

Do not create impossible schedules.

Use Python for dates and time allocation.

TinyLlama may help describe or prioritize topics.

---

# 20. Multilingual Behavior

Support:

```text
English
Tamil
Thanglish
```

Automatic language detection is preferred.

Examples:

```text
User:
Explain deadlock.

Assistant:
English response.
```

```text
User:
டெட்லாக் தமிழில் explain பண்ணுங்க.

Assistant:
Tamil response.
```

```text
User:
Deadlock simple ah explain pannunga.

Assistant:
Thanglish response.
```

Do not translate code, mathematical expressions, technical identifiers, filenames, or commands unnecessarily.

---

# 21. Offline-First Rule

The complete core application must work without internet access after required local models/packages are installed.

Internet search:

```env
INTERNET_SEARCH_ENABLED=false
```

Do not implement internet dependence in the core chatbot, RAG, memory, quiz, planner, or progress features.

Internet integration belongs to a later optional phase.

---

# 22. Error Handling

Handle these conditions gracefully:

- Ollama not running
- TinyLlama not installed
- MongoDB not running
- ChromaDB initialization failure
- unsupported document
- missing file
- corrupted document
- empty extracted text
- embedding failure
- retrieval returns no useful chunks
- malformed command
- invalid date
- invalid quiz answer
- invalid difficulty
- database write failure

Example user-facing message:

```text
[FAILED] Ollama is not available.

Start Ollama and try again:
ollama serve
```

Do not expose unnecessary internal stack traces to the normal user.

Debug logs may contain technical details.

---

# 23. Security and Safety Rules

1. Never execute arbitrary terminal commands from user chat.
2. Never use Python `eval()` on raw user input.
3. Validate file paths.
4. Restrict document processing to supported file types.
5. Store secrets only in `.env`.
6. Do not commit `.env`.
7. Do not expose MongoDB credentials in logs.
8. Do not delete files or databases automatically.
9. Internet search must be explicit and disabled by default.
10. Tool routing must use an allowlist.

---

# 24. Configuration

Recommended `.env.example`:

```env
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_MODEL=tinyllama

MONGODB_URI=mongodb://127.0.0.1:27017
MONGODB_DATABASE=ai_learning_assistant

CHROMA_PATH=./data/chroma

DOCUMENTS_PATH=./data/documents
EXPORTS_PATH=./data/exports
LOGS_PATH=./data/logs

INTERNET_SEARCH_ENABLED=false
DEFAULT_LANGUAGE=auto
```

---

# 25. Recommended Project Structure

```text
ai-learning-assistant/
|
|-- main.py
|-- config.py
|-- requirements.txt
|-- README.md
|-- MASTER_PROMPT.md
|-- .env
|-- .env.example
|-- .gitignore
|
|-- app/
|   |-- __init__.py
|   |
|   |-- cli/
|   |   |-- __init__.py
|   |   |-- terminal.py
|   |   |-- commands.py
|   |   |-- menu.py
|   |   `-- formatter.py
|   |
|   |-- ai/
|   |   |-- __init__.py
|   |   |-- ollama_client.py
|   |   |-- router.py
|   |   |-- response_style.py
|   |   |-- language_detector.py
|   |   |-- agent.py
|   |   |-- context_builder.py
|   |   |-- response_validator.py
|   |   `-- prompts.py
|   |
|   |-- rag/
|   |   |-- __init__.py
|   |   |-- rag_service.py
|   |   |-- loader.py
|   |   |-- chunker.py
|   |   |-- embeddings.py
|   |   |-- vector_store.py
|   |   |-- retriever.py
|   |   `-- citations.py
|   |
|   |-- loaders/
|   |   |-- __init__.py
|   |   |-- pdf_loader.py
|   |   |-- docx_loader.py
|   |   |-- pptx_loader.py
|   |   |-- txt_loader.py
|   |   `-- markdown_loader.py
|   |
|   |-- memory/
|   |   |-- __init__.py
|   |   |-- memory_manager.py
|   |   |-- short_term.py
|   |   |-- long_term.py
|   |   `-- conversation_memory.py
|   |
|   |-- database/
|   |   |-- __init__.py
|   |   |-- mongodb.py
|   |   |-- collections.py
|   |   `-- repositories/
|   |
|   |-- tools/
|   |   |-- __init__.py
|   |   |-- calculator.py
|   |   |-- quiz_generator.py
|   |   |-- study_planner.py
|   |   |-- revision_planner.py
|   |   |-- notes_search.py
|   |   |-- pdf_search.py
|   |   |-- progress_tracker.py
|   |   |-- weak_topic_detector.py
|   |   |-- flashcard_generator.py
|   |   `-- syllabus_analyzer.py
|   |
|   |-- learning/
|   |   |-- __init__.py
|   |   |-- progress.py
|   |   |-- scoring.py
|   |   |-- recommendations.py
|   |   `-- difficulty.py
|   |
|   |-- language/
|   |   |-- __init__.py
|   |   |-- detector.py
|   |   `-- response_language.py
|   |
|   `-- internet/
|       |-- __init__.py
|       |-- search.py
|       `-- settings.py
|
|-- data/
|   |-- documents/
|   |-- chroma/
|   |-- exports/
|   `-- logs/
|
|-- prompts/
|   |-- normal_chat.txt
|   |-- rag.txt
|   |-- quiz.txt
|   `-- planner.txt
|
`-- tests/
    |-- test_ollama.py
    |-- test_mongodb.py
    |-- test_chromadb.py
    |-- test_rag.py
    |-- test_memory.py
    |-- test_router.py
    |-- test_quiz.py
    |-- test_planner.py
    `-- test_tools.py
```

Do not create all files blindly in one operation.

Create them only when their implementation phase begins.

---

# 26. File Responsibility Registry

This section explains what every planned project file is responsible for.

**Codex must keep this section updated whenever project structure changes.**

---

## Root Files

### `ingest.py`

Developer batch-indexing entry point that discovers supported files in
`data/documents` and delegates loading, chunking, local embeddings, and ChromaDB
storage to the Phase 3/4 RAG services.

---

### `test_setup.py`

Manual local-service health report that reuses the application Ollama, MongoDB,
and ChromaDB service boundaries without writing test data.

---

### `main.py`

Purpose:

- application entry point
- run startup health checks
- initialize required services
- start terminal interface
- perform graceful shutdown

Must not contain all application logic.

---

### `config.py`

Purpose:

- read environment variables
- validate configuration
- expose typed application settings
- provide paths and feature flags

Must not contain secrets directly.

---

### `requirements.txt`

Purpose:

- list Python dependencies required by the project

Keep dependencies minimal.

---

### `.env`

Purpose:

- local private runtime configuration

Never commit.

---

### `.env.example`

Purpose:

- safe example of required environment variables

Must not contain real secrets.

---

### `.gitignore`

Must ignore at minimum:

```text
.env
__pycache__/
*.pyc
.venv/
venv/
data/chroma/
data/logs/
```

Decide carefully whether local uploaded documents should be ignored.

---

### `README.md`

Purpose:

- project description
- prerequisites
- installation
- Ollama setup
- MongoDB setup
- run instructions
- terminal commands
- troubleshooting

---

### `MASTER_PROMPT.md`

Purpose:

- single source of truth
- architecture
- fixed requirements
- implementation rules
- development phases
- file responsibility registry
- acceptance criteria

Codex must update this file when architecture/file responsibilities change.

---

# 27. CLI Files

## `app/cli/terminal.py`

Responsible for:

- main terminal conversation loop
- reading user input
- sending input to router/agent
- displaying output
- graceful exit

Do not put business logic here.

---

## `app/cli/commands.py`

Responsible for:

- slash-command definitions
- command parsing
- command validation
- forwarding commands to correct services

---

## `app/cli/menu.py`

Responsible for:

- interactive terminal menus
- quiz difficulty menu
- settings menus
- document selection
- user-friendly options

---

## `app/cli/formatter.py`

Responsible for:

- consistent terminal output
- headings
- status messages
- source formatting
- quiz formatting
- progress formatting

---

# 28. AI Files

## `app/ai/ollama_client.py`

Responsible for:

- all Ollama communication
- model selection
- chat requests
- embedding requests if architecture uses the same client
- connection error handling
- model availability checks

No other module should duplicate raw Ollama connection code.

---

## `app/ai/router.py`

Responsible for deciding the request intent.

Possible outputs:

```text
NORMAL_CHAT
RAG_SEARCH
MEMORY_SEARCH
QUIZ
STUDY_PLAN
REVISION_PLAN
CALCULATOR
FLASHCARD
PROGRESS
WEAK_TOPIC
SYLLABUS
NOTES_SEARCH
PDF_SEARCH
```

Use deterministic routing where easy.

Use LLM classification only when needed.

---

## `app/ai/agent.py`

Responsible for:

- orchestrating the chosen route
- calling RAG, memory, or tools
- passing final context to the configured Ollama model
- returning structured responses

The agent is the main coordinator.

---

## `app/ai/response_style.py`

Deterministically classifies the requested answer shape and selects concise,
normal, detailed, step, list, summary, code, comparison, or recommendation limits.
It controls presentation only and must never contain factual answers.

---

## `app/ai/language_detector.py`

Deterministically selects English, Tamil, or Thanglish output instructions from
the current user message. It controls output language only and contains no answers.

---

## `app/ai/context_builder.py`

Responsible for building the smallest useful LLM context from:

- system instructions
- current conversation
- relevant memory
- retrieved RAG chunks
- tool results

Do not send unnecessary history.

---

## `app/ai/response_validator.py`

Responsible for:

- checking required response structure
- RAG grounding rules
- source-presence checks
- empty response handling
- basic output quality checks

---

## `app/ai/prompts.py`

Responsible for:

- loading prompt templates
- prompt variables
- central prompt management

Do not spread long prompts across random Python files.

---

# 29. RAG Files

## `app/rag/rag_service.py`

High-level RAG coordinator.

Responsible for:

- document indexing requests
- retrieval requests
- connecting loader, chunker, embeddings, vector store, retriever, citations

---

## `app/rag/loader.py`

Responsible for:

- detecting file extension
- selecting correct document loader
- returning normalized extracted-document objects

---

## `app/rag/chunker.py`

Responsible for:

- splitting text into useful chunks
- preserving metadata
- configurable chunk size
- overlap management

---

## `app/rag/embeddings.py`

Responsible for:

- generating vector embeddings
- embedding configuration
- batching where appropriate
- embedding errors

---

## `app/rag/vector_store.py`

Responsible for:

- ChromaDB initialization
- collections
- insert/update/delete vector records
- persistence
- metadata storage

---

## `app/rag/retriever.py`

Responsible for:

- semantic similarity search
- top-k retrieval
- metadata filtering
- relevance threshold
- returning ranked chunks

---

## `app/rag/citations.py`

Responsible for:

- converting metadata into readable sources

Examples:

```text
DBMS.pdf — Page 21
NetworkSecurity.pptx — Slide 12
notes.md — Heading: Deadlock
```

Never invent source metadata.

---

# 30. Loader Files

## `app/loaders/base.py`

- define the normalized extracted-document record
- provide shared file validation and text cleaning
- expose safe document-loading errors

---

## `app/loaders/pdf_loader.py`

- read PDF
- extract text
- preserve page numbers
- return normalized records

---

## `app/loaders/docx_loader.py`

- read DOCX
- extract paragraphs
- preserve headings/sections when available

---

## `app/loaders/pptx_loader.py`

- read PPTX
- extract slide text
- preserve slide numbers

---

## `app/loaders/txt_loader.py`

- read TXT
- normalize encoding
- return text records

---

## `app/loaders/markdown_loader.py`

- read Markdown
- preserve headings
- provide heading metadata

---

# 31. Memory Files

## `app/memory/memory_manager.py`

High-level memory coordinator.

Responsible for deciding:

- what memory to store
- what memory to retrieve
- short-term vs long-term use

---

## `app/memory/short_term.py`

Responsible for:

- current-session conversation context
- recent turns
- context trimming

---

## `app/memory/long_term.py`

Responsible for:

- long-term student information
- MongoDB-backed retrieval
- persistent learning state

---

## `app/memory/conversation_memory.py`

Responsible for:

- conversation/session records
- storing user and assistant messages
- retrieving recent relevant conversation history

---

# 32. Database Files

## `app/database/mongodb.py`

Responsible for:

- MongoDB client
- connection
- health check
- database access
- graceful shutdown

---

## `app/database/collections.py`

Responsible for:

- centralized collection names
- schema-related constants
- indexes when appropriate

---

## `app/database/repositories/`

Repository layer.

Examples that may be created later:

```text
user_repository.py
conversation_repository.py
quiz_repository.py
progress_repository.py
document_repository.py
study_plan_repository.py
subject_repository.py
```

Each repository owns data access for one domain.

---

# 33. Tool Files

## `app/tools/calculator.py`

Safe deterministic calculator.

Never use raw `eval()`.

---

## `app/tools/quiz_generator.py`

Responsible for:

- quiz creation
- difficulty
- question structure
- answer evaluation
- score generation
- result persistence hooks

---

## `app/tools/study_planner.py`

Responsible for:

- study-plan generation
- available-time calculations
- date range calculations
- topic allocation
- weak-topic prioritization

---

## `app/tools/revision_planner.py`

Responsible for:

- revision priority
- weak-topic scheduling
- revision duration
- previous performance consideration

---

## `app/tools/notes_search.py`

Responsible for:

- semantic search across note-type documents
- source formatting

---

## `app/tools/pdf_search.py`

Responsible for:

- PDF-specific semantic or filtered retrieval

---

## `app/tools/progress_tracker.py`

Responsible for:

- progress calculation
- subject progress
- topic completion
- quiz averages
- study completion summaries

---

## `app/tools/weak_topic_detector.py`

Responsible for:

- evaluating performance data
- ranking weak topics
- deterministic scoring where possible

---

## `app/tools/flashcard_generator.py`

Responsible for:

- flashcard generation
- answer reveal
- difficulty feedback
- storing flashcard feedback when needed

---

## `app/tools/syllabus_analyzer.py`

Responsible for:

- identifying units
- topics
- subtopics
- study order
- learning priorities

Use RAG/document parsing as needed.

---

# 34. Learning Files

## `app/learning/progress.py`

Domain logic for:

- completion status
- progress percentages
- progress aggregation

---

## `app/learning/scoring.py`

Responsible for:

- quiz percentages
- score calculations
- thresholds
- performance classification

---

## `app/learning/recommendations.py`

Responsible for:

- recommended next topics
- study priorities
- revision recommendations

Uses structured data plus AI only when appropriate.

---

## `app/learning/difficulty.py`

Responsible for:

- Easy / Medium / Hard constants
- difficulty validation
- difficulty-related rules

---

# 35. Language Files

## `app/language/detector.py`

Responsible for:

- detecting English
- detecting Tamil
- identifying likely Thanglish

Use simple deterministic logic first.

Do not over-engineer.

---

## `app/language/response_language.py`

Responsible for:

- telling the AI which language style to use
- preserving technical terms
- storing/reusing preferred language where appropriate

---

# 36. Internet Files

Internet feature is future-only.

## `app/internet/settings.py`

Responsible for:

- internet-search feature flag
- enforcing disabled-by-default behavior

---

## `app/internet/search.py`

Future responsibility:

- controlled external search
- source collection
- response grounding

Do not implement until the offline project is complete and verified.

---

# 37. Data Directories

## `data/documents/`

Stores local user learning documents.

---

## `data/chroma/`

Stores local ChromaDB persistence.

---

## `data/exports/`

Stores generated exports if future features need them.

---

## `data/logs/`

Stores debug/application logs.

Do not expose secrets.

---

# 38. Prompt Files

## `prompts/normal_chat.txt`

The adaptive general-purpose learning prompt for `NORMAL_CHAT`. It defines
intent-aware answer shapes, language adaptation, factual caution, safety, and
instruction non-disclosure. It must not contain RAG grounding rules or retrieved
document context.

Normal-chat response length and structure adapt to the detected question type.
Factual content is generated by the configured Ollama model and is never hardcoded.

---

## `prompts/rag.txt`

Strict grounded-answer instructions.

---

## `prompts/quiz.txt`

Quiz generation rules.

---

## `prompts/planner.txt`

Study/revision planning language instructions.

---

# 39. Test Files

## `tests/test_loaders.py`

Verify all Phase 3 document formats, normalized metadata, supported-extension
dispatch, encoding behavior, and safe empty/unsupported document failures.

---

## `tests/test_phase1.py`

Verify the Phase 1 foundation:

- allowlisted command parsing
- bounded and clearable short-term memory
- offline-first configuration defaults

## `tests/test_ollama.py`

Verify:

- Ollama reachable
- configured model available
- simple response works

---

## `tests/test_mongodb.py`

Verify:

- MongoDB connection
- basic write/read
- cleanup of test record

---

## `tests/test_chromadb.py`

Verify:

- local vector store creation
- insert
- query
- persistence

---

## `tests/test_rag.py`

Verify:

- document indexing
- retrieval
- metadata
- grounded answer behavior

---

## `tests/test_memory.py`

Verify:

- conversation storage
- memory retrieval
- progress persistence

---

## `tests/test_router.py`

Verify that common phrases map to correct intents.

---

## `tests/test_quiz.py`

Verify:

- difficulty validation
- scoring
- result calculation

---

## `tests/test_planner.py`

Verify:

- date logic
- time allocation
- plan structure

---

## `tests/test_tools.py`

Verify deterministic tool behavior.

---

# 40. Development Phases

Codex must follow this order unless the user explicitly changes it.

## Phase 1 — Project Foundation

Implement only:

- base folders needed now
- `main.py`
- configuration
- `.env.example`
- Ollama client
- TinyLlama chat
- terminal loop
- basic conversation memory
- health check
- graceful `/exit`
- `/clear`
- `/help`

Success condition:

```text
python main.py
```

opens a working TinyLlama terminal chatbot.

---

## Phase 2 — MongoDB

Implement:

- MongoDB connection
- user profile
- conversation storage
- message storage
- subject/topic foundations

Verify persistence after restarting the application.

---

## Phase 3 — Document Loaders

Implement:

- PDF
- TXT
- Markdown
- DOCX
- PPTX

Verify extracted text and metadata.

---

## Phase 4 — ChromaDB + Embeddings

Implement:

- embeddings
- ChromaDB
- vector indexing
- metadata
- semantic retrieval

---

## Phase 5 — RAG

Implement:

- `/add`
- `/documents`
- retrieval
- grounded prompt
- sources
- insufficient-evidence handling

---

## Phase 6 — Automatic Router

Implement intent routing between:

- chat
- RAG
- memory
- tools

---

## Phase 7 — Ten Learning Tools

Implement one tool at a time.

Verify each before starting the next.

---

## Phase 8 — Quiz System

Implement:

- Easy / Medium / Hard
- scoring
- MongoDB result history
- feedback

---

## Phase 9 — Study Planner

Implement:

- exam date
- available time
- progress awareness
- weak-topic priority
- MongoDB storage

---

## Phase 10 — Progress + Weak Topics

Implement:

- topic progress
- quiz averages
- weakness algorithm
- recommendations

---

## Phase 11 — Revision + Flashcards + Syllabus

Complete remaining learning features.

---

## Phase 12 — English + Tamil + Thanglish

Implement language handling and verify examples.

---

## Phase 13 — Testing and Hardening

Run all tests.

Fix:

- startup failures
- invalid inputs
- corrupted files
- empty RAG results
- database failures
- model failures

---

## Phase 14 — Optional Internet Search

Only implement after explicit user approval.

Keep disabled by default.

---

## Phase 15 — Documentation

Complete:

- README
- architecture
- database design
- UML
- DFD
- module explanations
- testing report
- final-year report structure
- PPT plan
- demo flow
- viva questions

---

# 41. Implementation Rules for Codex

When asked to implement a phase:

### Step 1 — Inspect

Inspect existing project files first.

Do not assume the repository is empty.

### Step 2 — Plan

State:

```text
Goal
Files to create
Files to modify
Dependencies
Testing method
```

### Step 3 — Implement

Keep changes focused.

### Step 4 — Validate

Run:

- syntax checks
- relevant tests
- actual terminal command where possible

### Step 5 — Report

Use:

```text
IMPLEMENTATION RESULT

[VERIFIED] Feature
[WARNING] Feature
[FAILED] Feature

Created:
- ...

Modified:
- ...

Tested:
- ...

Next recommended step:
- ...
```

### Step 6 — Update This File

If any file responsibility or architecture changes, update the relevant section of `MASTER_PROMPT.md`.

---

# 42. Coding Standards

Use:

- Python type hints
- readable function names
- docstrings for important modules/functions
- clear exceptions
- small functions
- dependency injection where useful
- pathlib for filesystem paths where practical
- environment-based configuration
- structured return values for router/tools where useful

Avoid:

- giant `main.py`
- circular imports
- duplicate Ollama code
- duplicate MongoDB clients
- raw `eval()`
- hardcoded Windows-only paths
- hardcoded secrets
- unnecessary frameworks
- premature web/API code
- huge classes doing everything

---

# 43. Suggested Core Data Shapes

Use these as conceptual models, not mandatory exact schemas.

## User

```json
{
  "name": "Student",
  "preferred_language": "auto",
  "daily_study_minutes": 120,
  "created_at": "...",
  "updated_at": "..."
}
```

## Subject

```json
{
  "name": "DBMS",
  "description": "Database Management Systems",
  "progress": 65,
  "status": "active"
}
```

## Topic

```json
{
  "subject": "DBMS",
  "topic": "Normalization",
  "status": "completed",
  "confidence": 80,
  "quiz_average": 75
}
```

## Quiz Result

```json
{
  "subject": "DBMS",
  "topic": "Normalization",
  "difficulty": "medium",
  "score": 8,
  "total": 10,
  "percentage": 80,
  "created_at": "..."
}
```

---

# 44. Important UX Requirement

The terminal should feel clear and beginner-friendly.

Example:

```text
========================================================
       AI LEARNING & STUDY ASSISTANT
       RAG + MEMORY + TOOLS
========================================================

Model       : TinyLlama
Ollama      : Connected
MongoDB     : Connected
ChromaDB    : Ready
Internet    : OFFLINE
Language    : Auto

Type /help to view commands.

You:
```

Do not flood the screen with debug output.

---

# 45. Acceptance Criteria

The project is considered successful when:

## Chat

- terminal starts
- TinyLlama replies
- conversation context works
- `/clear` works
- `/exit` works

## MongoDB

- data survives application restart
- student profile can be read
- conversations are persisted
- learning data is stored safely

## RAG

- all required file formats can be indexed
- semantic retrieval works
- PDF page sources work where available
- PPTX slide sources work
- strict material-only questions do not hallucinate unsupported content

## Tools

All ten tools work.

## Quiz

- Easy
- Medium
- Hard
- scoring
- persistence
- weak-topic update

## Study Planner

- date aware
- available-time aware
- progress aware
- weak-topic aware

## Languages

- English works
- Tamil works
- Thanglish works

## Offline

Core application works without online API keys.

---

# 46. Final Deliverables

The completed project should include:

```text
Complete Python source code
Ollama integration
TinyLlama integration
MongoDB integration
ChromaDB integration
RAG
Memory
All 10 tools
Study planner
Quiz system
Progress tracking
Weak-topic detection
Revision planner
Flashcards
Syllabus analyzer
Multilingual support
Source references
Hallucination safeguards
Tests
requirements.txt
.env.example
README
Installation guide
User guide
Architecture diagram description
Use-case diagram description
DFD
UML design
Database design
Testing documentation
Final-year project report structure
Abstract
Problem statement
Objectives
Modules
Results
Future enhancements
Presentation structure
Demo flow
Viva questions and answers
```

---

# 47. Final Instruction to Codex

You are the implementation agent for this project.

Your job is **not** to generate everything at once.

Your job is to build the application phase by phase while preserving this architecture.

Before making changes:

1. inspect the repository;
2. compare current state with this file;
3. identify the smallest safe next implementation;
4. modify only required files;
5. test your changes;
6. report results clearly;
7. update this file when file responsibilities or architecture change.

If the user says:

```text
Continue
```

continue from the first incomplete phase.

If the user requests a feature that conflicts with this document, explain the conflict and wait for confirmation before changing the architecture.

If an implementation choice is minor and does not change the agreed architecture, choose the simplest maintainable option and continue.

The final application must remain:

```text
LOCAL
PYTHON
TERMINAL-ONLY
OLLAMA
TINYLLAMA
MONGODB
CHROMADB
RAG
MEMORY
TOOLS
OFFLINE-FIRST
```
