import os

import chromadb
from chromadb.utils import embedding_functions
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

MODEL_NAME = "all-MiniLM-L6-v2"

app = FastAPI(title="arXiv Papers Search API")

# CORS origins - comma-separated list, defaults to localhost for development
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Chroma client and collection
# Use path relative to this file's location
_db_path = os.path.join(os.path.dirname(__file__), "chroma_db")
client = chromadb.PersistentClient(path=_db_path)
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=MODEL_NAME
)
collection = client.get_or_create_collection(
    name="arxiv_papers",
    embedding_function=embedding_fn
)


class SearchRequest(BaseModel):
    query: str
    n_results: int = 10


class SearchResult(BaseModel):
    id: str
    title: str
    categories: str
    distance: float


class SearchResponse(BaseModel):
    results: list[SearchResult]


@app.get("/health")
def health_check():
    return {"status": "healthy", "collection_count": collection.count()}


@app.post("/search", response_model=SearchResponse)
def search_papers(request: SearchRequest):
    if request.n_results < 1 or request.n_results > 100:
        raise HTTPException(status_code=400, detail="n_results must be between 1 and 100")

    results = collection.query(
        query_texts=[request.query],
        n_results=request.n_results
    )

    search_results = []
    for i, doc_id in enumerate(results["ids"][0]):
        search_results.append(SearchResult(
            id=doc_id,
            title=results["metadatas"][0][i]["title"],
            categories=results["metadatas"][0][i]["categories"],
            distance=results["distances"][0][i]
        ))

    return SearchResponse(results=search_results)
