from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import os
import tempfile
from groq import Groq
from qdrant_client import QdrantClient, models
from llama_parse import LlamaParse
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
import time
load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
qdrant = QdrantClient(url=os.environ.get("QDRANT_URL", "http://localhost:6333"))
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
parser = LlamaParse(api_key=os.environ.get("LLAMA_PARSE_KEY"), result_type="text", language="en")
splitter = SentenceSplitter(chunk_size=500, chunk_overlap=50)

COLLECTION = "documents"
MODEL_NAME = "BAAI/bge-small-en"

class Question(BaseModel):
    question: str

# --- Helpers ---
def chunk_text(text: str):
    nodes = splitter.get_nodes_from_documents([Document(text=text)])
    return [node.get_content() for node in nodes]

async def extract_text(file: UploadFile, content: bytes) -> str:
    suffix = os.path.splitext(file.filename)[1]
    tmp_path = f"/tmp/{uuid.uuid4()}{suffix}"

    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        docs = await parser.aload_data(tmp_path)
        return "\n".join(doc.text for doc in docs)
    except Exception as e:
        print(f"Extraction error: {e}")
        return content.decode("utf-8", errors="ignore")
    finally:
        os.unlink(tmp_path)



def generate_response(prompt: str) -> str:
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "Answer the question using only the provided context. If the answer is not in the context, say so."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def stream_response(prompt: str):
    stream = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Answer the question using only the provided context. If the answer is not in the context, say so."
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta

def store_documents(documents):
    if not qdrant.collection_exists(collection_name=COLLECTION):
        qdrant.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=qdrant.get_embedding_size(MODEL_NAME),
                distance=models.Distance.COSINE
            ),
        )

    docs = [doc['page_content'] for doc in documents]
    payloads = [{"text": doc["page_content"], **doc["metadata"]} for doc in documents]
    ids = [str(uuid.uuid4()) for _ in documents]

    qdrant.upload_collection(
        collection_name=COLLECTION,
        vectors=[models.Document(text=doc, model=MODEL_NAME) for doc in docs],
        payload=payloads,
        ids=ids,
    )

    info = qdrant.get_collection(COLLECTION)
    print(f"Collection now has {info.points_count} total chunks")

# --- Routes ---
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    text = await extract_text(file, content)
    chunks = chunk_text(text)
    documents = [
        {"page_content": chunk, "metadata": {"source": file.filename}}
        for chunk in chunks
    ]
    store_documents(documents)
    return {"status": "ok", "chunks_stored": len(chunks)}

@app.post("/ask")
async def ask(body: Question):
    results = qdrant.query_points(
        collection_name=COLLECTION,
        query=models.Document(text=body.question, model=MODEL_NAME),
        limit=5
    )
    context = "\n\n".join(r.payload["text"] for r in results.points)
    # response = generate_response(f"Context:\n{context}\n\nQuestion: {body.question}\nAnswer:")
    prompt = f"Context:\n{context}\n\nQuestion: {body.question}\nAnswer:"
    return StreamingResponse(
        stream_response(prompt),
        media_type="text/plain"
    )
    
    # return {"answer": response}