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
import base64
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


AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mp4", ".mpeg", ".mpga", ".webm"}
IMAGE_EXTENSIONS = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
 


class Question(BaseModel):
    question: str

# --- Helpers ---
def chunk_text(text: str):
    nodes = splitter.get_nodes_from_documents([Document(text=text)])
    return [node.get_content() for node in nodes]

def transcribe_audio(file_path: str, filename: str) -> str:
    """Use Groq Whisper to transcribe audio and return text."""
    with open(file_path, "rb") as f:
        transcription = groq_client.audio.transcriptions.create(
            file=(filename, f),
            model="whisper-large-v3-turbo",
            response_format="text",
        )
    print(f"Audio transcribed: {str(transcription)[:100]}...")
    return str(transcription)


def describe_image(file_path: str, suffix: str) -> str:
    """Use Groq vision model to describe an image and return text description."""
    media_type = IMAGE_EXTENSIONS.get(suffix.lower(), "image/jpeg")
    with open(file_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")
 
    response = groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",  # Groq vision model
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": (
                            "Describe this image in detail. Include: objects, people, text, "
                            "colors, layout, context, and any other relevant information. "
                            "Be thorough so the description can be used for search and Q&A."
                        )
                    }
                ]
            }
        ],
        max_tokens=1024,
    )
    description = response.choices[0].message.content
    print(f"Image described: {description[:100]}...")
    return description


async def extract_text(file: UploadFile, content: bytes) -> str:
    """Extract text from uploaded file — supports documents, images, and audio."""
    suffix = os.path.splitext(file.filename)[1].lower()
    tmp_path = f"/tmp/{uuid.uuid4()}{suffix}"
 
    with open(tmp_path, "wb") as f:
        f.write(content)
 
    try:
        if suffix in IMAGE_EXTENSIONS:
            return describe_image(tmp_path, suffix)
 
        elif suffix in AUDIO_EXTENSIONS:
            return transcribe_audio(tmp_path, file.filename)
 
        else:
            # Document: use LlamaParse for PDFs, DOCX, etc.
            try:
                docs = await parser.aload_data(tmp_path)
                return "\n".join(doc.text for doc in docs)
            except Exception as e:
                print(f"LlamaParse error: {e}")
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
                "content": '''"Answer the question using only the provided context. "
                "Each chunk is labeled with its source. "
                "If the context contains transcripts, treat them as spoken words. "
                "If the answer is not in the context, say so." '''
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
    suffix = os.path.splitext(file.filename)[1].lower()
    file_type =""
 
    # Determine file type for response
    if suffix in IMAGE_EXTENSIONS:
        file_type = "image"
    elif suffix in AUDIO_EXTENSIONS:
        file_type = "audio"
    else:
        file_type = "document"
    t = time.time()                          
    text = await extract_text(file, content)
    print(f"[TIMER] extraction total: {time.time() - t:.2f}s")
    if not text.strip():
        return {"status": "error", "message": "Could not extract text from file"}
    
    chunks = chunk_text(text)
    print(f"[TIMER] chunking: {time.time() - t:.2f}s")
    documents = [
        {"page_content": chunk, "metadata": {"source": file.filename}}
        for chunk in chunks
    ]
    store_documents(documents)
    print(f"[TIMER] qdrant store: {time.time() - t:.2f}s")
    return {"status": "ok", "chunks_stored": len(chunks)}

@app.post("/ask")
async def ask(body: Question):
    results = qdrant.query_points(
        collection_name=COLLECTION,
        query=models.Document(text=body.question, model=MODEL_NAME),
        limit=10,
        score_threshold=0.5
    )
    context = "\n\n".join(
        f"[Source: {r.payload.get('source', 'unknown')}]\n{r.payload['text']}"
        for r in results.points
    )
    # response = generate_response(f"Context:\n{context}\n\nQuestion: {body.question}\nAnswer:")
    prompt = f"Context:\n{context}\n\nQuestion: {body.question}\nAnswer:"
    return StreamingResponse(
        stream_response(prompt),
        media_type="text/plain"
    )
    
    # return {"answer": response}

@app.post("/transcribe")
async def transcribe_only(file: UploadFile = File(...)):
    """Transcribe audio file and return transcript without storing in vector DB."""
    content = await file.read()
    suffix = os.path.splitext(file.filename)[1].lower()
 
    if suffix not in AUDIO_EXTENSIONS:
        return {"status": "error", "message": "File is not a supported audio format."}
 
    tmp_path = f"/tmp/{uuid.uuid4()}{suffix}"
    with open(tmp_path, "wb") as f:
        f.write(content)
 
    try:
        transcript = transcribe_audio(tmp_path, file.filename)
        return {"status": "ok", "transcript": transcript}
    finally:
        os.unlink(tmp_path)

@app.on_event("startup")
async def startup():
    print("Preloading BGE embedding model...")
    t = time.time()
    try:
        qdrant.query_points(
            collection_name=COLLECTION,
            query=models.Document(text="warmup", model=MODEL_NAME),
            limit=1
        )
    except Exception:
        pass
    print(f"Model ready in {time.time() - t:.2f}s")
