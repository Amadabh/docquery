# DocQuery — Document-Based Q&A System

An intelligent document assistant that lets you upload files, index their content with semantic embeddings, and ask natural-language questions — getting answers synthesized from your own documents.

---

## Features
- Multi-format file upload (PDF, TXT, CSV, XLSX, DOCX, images, audio)
- Semantic search using embeddings + vector DB
- LLM-generated answers (Groq)
- Streaming responses
- Image understanding + audio transcription
- Cross-document reasoning

---

## Architecture

![Document Ingestion Pipeline](assets/doc_ingestion.png)

## Tech Stack

| Layer | Technology |
|------|------------|
| LLM | Groq (llama-3.3-70b) |
| Embeddings | bge-small-en |
| Chunking | LlamaIndex SentenceSplitter |
| Vector DB | Qdrant |
| Parsing | LlamaParse |
| Backend | FastAPI |
| Frontend | React + Vite |
| Infra | Docker Compose |

---
# SetUp Instructions
## Prerequisites

- **Docker & Docker Compose** (recommended) or **Docker Desktop**, or:
  - Python 3.11+
  - Node.js 18+ / [Bun](https://bun.sh/) 1.0+
- **API Keys** (free tiers available):
  - [Groq API Key](https://console.groq.com/) — for LLM, vision, and transcription
  - [LlamaParse API Key](https://cloud.llamaindex.ai/) — for document parsing

---

## 🚀 Getting Started
 
### Option 1: Docker Compose (Recommended)
 
```bash
git clone https://github.com/Amadabh/docquery.git
cd docquery
cp backend/.env.example backend/.env
# add GROQ_API_KEY + LLAMA_PARSE_KEY
docker compose up --build
```
 
### Services
 
| Service  | URL                        |
| -------- | -------------------------- |
| Frontend | http://localhost:5173      |
| Backend  | http://localhost:8000      |
| Qdrant   | http://localhost:6333      |
 
---
 
### Option 2: Local Development
 
#### 1. Start Qdrant
 
```bash
docker run -p 6333:6333 \
  -v $(pwd)/qdrant_storage:/qdrant/storage \
  qdrant/qdrant
```
 
---
 
#### 2. Start Backend
 
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```
 
> ⚠️ **Note:** On first run, the embedding model (`BAAI/bge-small-en`) is downloaded via FastEmbed.
> Wait until you see **"Application startup complete"** (~30–60s). After that, it is cached and starts quickly.
 
---
 
#### 3. Start Frontend
 
```bash
cd frontend
bun install   # or npm install
bun run dev
```
 
Open: http://localhost:5173

## 📖 Usage
Upload documents via the 📎 icon, then ask questions in chat. The system retrieves relevant context using embeddings and streams LLM-generated answers. Voice input is also supported via 🎤 microphone.

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

---

## 📜 License

This project is for educational and assessment purposes.
