# 📄 DocQA — Document-Based Q&A System

An intelligent document assistant that lets you upload files, index their content with semantic embeddings, and ask natural-language questions — getting answers synthesized from your own documents.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-DC382D)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

---

## ✨ Features

- **Multi-format file upload** — PDF, TXT, CSV, XLSX, DOCX, images (PNG/JPG/JPEG/GIF/WEBP), and audio (MP3, WAV, M4A, OGG, FLAC, WEBM)
- **Semantic search** — Documents are chunked with LlamaIndex `SentenceSplitter` and embedded with `BAAI/bge-small-en`; questions retrieve the most relevant passages via cosine similarity
- **LLM-synthesized answers** — Groq's `llama-3.3-70b-versatile` generates coherent answers grounded in your document context
- **Streaming responses** — Answers stream token-by-token for a responsive chat experience
- **Image understanding** — Images are described using Groq's vision model (`llama-4-scout-17b-16e-instruct`) and the description is indexed for search
- **Audio transcription** — Audio files are transcribed via Groq Whisper (`whisper-large-v3-turbo`) and indexed; voice input in the chat is also supported
- **Document persistence** — Once uploaded, documents remain searchable indefinitely across all future questions
- **Cross-document synthesis** — Questions search across *all* stored documents, enabling answers that combine information from multiple sources

---

## 🏗️ Architecture

![Document Ingestion Pipeline](assets/doc_ingestion.png)

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│              React 19 + Vite + Tailwind CSS                  │
│     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│     │  File Attach  │  │  Chat Input  │  │  Voice Rec.  │     │
│     └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└────────────┼────────────────┼────────────────┼───────────────┘
             │ POST /upload   │ POST /ask      │ POST /transcribe
             ▼                ▼                ▼
┌──────────────────────────────────────────────────────────────┐
│                     Backend  (FastAPI)                        │
│                                                              │
│  ┌─────────────────┐  ┌────────────────┐  ┌───────────────┐  │
│  │  File Processor  │  │  QA Pipeline   │  │  Transcriber  │  │
│  │  ───────────────│  │  ────────────── │  │  ─────────── │  │
│  │  LlamaParse     │  │  Embed query   │  │  Groq Whisper│  │
│  │  Groq Vision   │  │  Search Qdrant │  │              │  │
│  │  Groq Whisper  │  │  Build prompt  │  └───────────────┘  │
│  └────────┬────────┘  │  Stream LLM   │                     │
│           │           └───────┬────────┘                     │
│           │                   │                              │
│   chunk (LlamaIndex      query + retrieve                    │
│   SentenceSplitter)           │                              │
│   + embed (BGE)               │                              │
│           │                   │                              │
│           ▼                   ▼                              │
│  ┌────────────────────────────────────┐                      │
│  │   Qdrant  (Vector Database)        │                      │
│  │   Collection: "documents"          │                      │
│  │   Embedding: BAAI/bge-small-en     │                      │
│  │   Distance: Cosine Similarity      │                      │
│  └────────────────────────────────────┘                      │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Upload → Extract Text → Chunk (LlamaIndex SentenceSplitter, 500 tokens, 50 overlap) → Embed (BGE) → Store in Qdrant
                                                                                                            │
Ask → Embed Question → Semantic Search (top 10, threshold 0.5) ─────────────────────────────────────────────┘
                                                          │
                                              Build Prompt with Context
                                                          │
                                              Stream LLM Response → UI
```

---

## 🛠️ Tech Stack & Rationale

| Layer | Technology | Why |
|---|---|---|
| **LLM** | [Groq](https://groq.com/) (`llama-3.3-70b-versatile`) | Free tier, extremely fast inference via custom LPU hardware |
| **Embeddings** | `BAAI/bge-small-en` via FastEmbed | Runs locally (no API cost), high quality for its size, fast |
| **Chunking** | LlamaIndex `SentenceSplitter` | Respects sentence boundaries, accurate token counting via `tiktoken`, preserves LlamaParse metadata |
| **Vector DB** | [Qdrant](https://qdrant.tech/) | Purpose-built for vector search, simple Docker setup, payload filtering |
| **File Parsing** | [LlamaParse](https://docs.llamaindex.ai/en/stable/llama_cloud/llama_parse/) | Handles PDF, DOCX, XLSX, CSV, and more with high fidelity |
| **Vision** | Groq (`llama-4-scout-17b-16e-instruct`) | Free multimodal model for image description |
| **Speech-to-Text** | Groq Whisper (`whisper-large-v3-turbo`) | Fast, accurate transcription via Groq's API |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) | Async-first, automatic OpenAPI docs, streaming support |
| **Frontend** | React 19 + Vite + Tailwind CSS v4 | Modern tooling, fast HMR, utility-first styling |
| **Containerization** | Docker Compose | One-command startup for all three services |

---

## 📋 Prerequisites

- **Docker & Docker Compose** (recommended), or:
  - Python 3.11+
  - Node.js 18+ / [Bun](https://bun.sh/) 1.0+
- **API Keys** (free tiers available):
  - [Groq API Key](https://console.groq.com/) — for LLM, vision, and transcription
  - [LlamaParse API Key](https://cloud.llamaindex.ai/) — for document parsing

---

## 🚀 Getting Started

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/Amadabh/docquery.git
cd docquery

# 2. Create your environment file
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys:
#   GROQ_API_KEY='your-groq-key'
#   LLAMA_PARSE_KEY='your-llamaparse-key'

# 3. Start all services
docker compose up --build
```

This starts three containers:
| Service | URL |
|---|---|
| **Frontend** | [http://localhost:5173](http://localhost:5173) |
| **Backend** | [http://localhost:8000](http://localhost:8000) |
| **Qdrant** | [http://localhost:6333](http://localhost:6333) |

> ⚠️ **Wait for the BGE embedding model to finish loading before uploading files or asking questions.**
>
> On first startup (or after clearing Docker volumes), the backend downloads and initializes the `BAAI/bge-small-en` model via FastEmbed. This can take **30–60 seconds** depending on your machine and internet speed. Watch the backend logs for a line like:
> ```
> Fetching 5 files: 100%|██████████| 5/5 [...]
> ```
> or a confirmation that the embedding model is ready. Sending requests before this completes will result in errors. Subsequent starts are fast because the model is cached.

### Option 2: Local Development

**Terminal 1 — Qdrant:**
```bash
docker run -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

**Terminal 2 — Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create .env from template and add your keys
cp .env.example .env

uvicorn main:app --reload --port 8000
```

> ⚠️ **BGE cold start:** On first run, FastEmbed will download `BAAI/bge-small-en` before the server is ready to handle requests. Wait until you see the Uvicorn startup message (`Application startup complete`) before using the app — the embedding model must finish loading first.

**Terminal 3 — Frontend:**
```bash
cd frontend
bun install    # or: npm install
bun run dev    # or: npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📖 Usage

### 1. Upload Documents

Click the **📎 paperclip** icon in the chat input bar to attach one or more files. Supported formats:

| Category | Extensions |
|---|---|
| Documents | `.pdf`, `.txt`, `.csv`, `.xlsx`, `.docx` |
| Images | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` |
| Audio | `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.webm` |

Files are processed and indexed when you send a message.

### 2. Ask Questions

Type a question and press **Enter**. The system will:
1. Embed your question using `bge-small-en`
2. Retrieve the top 10 most relevant chunks (cosine similarity ≥ 0.5) from **all** stored documents
3. Stream an LLM-generated answer grounded in the retrieved context

### 3. Voice Input

Click the **🎤 microphone** icon to record a voice question. The recording is transcribed via Groq Whisper and populated into the input field.

---

## 🧪 Testing the System

### Sample Test Documents

Create these files to test the system end-to-end:

**`therapy_tips.txt`**
```
10 Tips for Managing Anxiety

1. Practice deep breathing exercises — 4-7-8 technique works well.
2. Try Cognitive Behavioral Therapy (CBT) to reframe negative thought patterns.
3. Establish a consistent sleep schedule.
4. Limit caffeine and alcohol intake.
5. Exercise regularly — even 20 minutes of walking helps.
6. Practice mindfulness meditation daily.
7. Keep a worry journal to externalize anxious thoughts.
8. Use progressive muscle relaxation before bed.
9. Set boundaries and learn to say no.
10. Consider speaking with a licensed therapist for professional guidance.
```

**`school_guide.txt`**
```
School Accommodation Options for Students

IEP (Individualized Education Program):
- Legally binding document for students with disabilities.
- Includes specific learning goals and services.
- Requires evaluation and team meeting.

504 Plan:
- Provides accommodations for students with disabilities.
- Examples: extra test time, preferential seating, note-taking assistance.
- Less formal than an IEP.

Common Accommodations:
- Extended time on tests and assignments
- Quiet testing environment
- Modified homework expectations
- Access to assistive technology
- Regular check-ins with a counselor
- Flexible seating arrangements

How to Request:
1. Contact the school's special education coordinator.
2. Provide documentation of the student's needs.
3. Attend a planning meeting with the school team.
```

### Test Workflow

```
Step 1: Upload "therapy_tips.txt" via the paperclip icon
Step 2: Upload "school_guide.txt"
Step 3: Ask "What's a good therapy for anxiety?"
        → Should get an answer referencing CBT, deep breathing, etc.
Step 4: Ask "What accommodations can we request?"
        → Should get an answer about IEP, 504 plans, extra time, etc.
Step 5: Ask "Should therapy come before accommodations?"
        → Should synthesize an answer from BOTH documents
```

---

## 📁 Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI app — upload, ask, transcribe endpoints
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example          # Environment variable template
│   └── Dockerfile           # Backend container image
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main chat UI component
│   │   ├── main.jsx         # React entry point
│   │   ├── index.css        # Global styles
│   │   └── components/ui/   # Reusable UI components (badge, button, card, scroll-area)
│   ├── index.html           # HTML entry point
│   ├── package.json         # Frontend dependencies
│   ├── vite.config.js       # Vite + Tailwind configuration
│   └── Dockerfile           # Frontend container image
├── docker-compose.yml       # Orchestrates backend, frontend, and Qdrant
├── qdrant_storage/          # Qdrant persistent data (auto-created)
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload` | Upload a file for processing and indexing |
| `POST` | `/ask` | Ask a question; returns a streamed plain-text response |
| `POST` | `/transcribe` | Transcribe an audio file without indexing |

### `/upload`

```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@therapy_tips.txt"
```
**Response:**
```json
{ "status": "ok", "chunks_stored": 3 }
```

### `/ask`

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is CBT?"}'
```
**Response:** Streamed plain text.

### `/transcribe`

```bash
curl -X POST http://localhost:8000/transcribe \
  -F "file=@recording.webm"
```
**Response:**
```json
{ "status": "ok", "transcript": "What therapy works best for anxiety?" }
```

---

## ⚖️ Design Decisions & Trade-offs

### MVP Trade-offs

| Decision | Rationale |
|---|---|
| **Single user, no auth** | MVP scope — simplifies architecture; multi-tenant support can be added via collection-per-user |
| **No chat history/memory** | Each question is independent; keeps the retrieval pipeline stateless and simple |
| **No document deletion** | Documents persist indefinitely; deletion can be added by tracking Qdrant point IDs per file |
| **`SentenceSplitter` (500 tokens / 50 overlap)** | Respects sentence boundaries for more coherent chunks; size balances context richness with embedding precision — tunable per use case |
| **Score threshold 0.5** | Filters out low-relevance noise; can be adjusted or made dynamic |
| **Local embeddings (FastEmbed + BGE)** | Zero API cost, runs on CPU, avoids rate limits — trades off for a cold-start delay on first boot while the model downloads and initializes |

### Scaling Considerations

- **Multi-user** — Namespace Qdrant collections per user; add auth layer (OAuth, JWT)
- **Larger documents** — Add a task queue (Celery/Redis) for async processing
- **Better retrieval** — Hybrid search (semantic + BM25), re-ranking with cross-encoders
- **Conversation memory** — Maintain a sliding window of recent Q&A pairs in the prompt
- **Production deployment** — Containerize behind a reverse proxy (Nginx/Caddy), add health checks, logging, and monitoring

---

## 📜 License

This project is for educational and assessment purposes.