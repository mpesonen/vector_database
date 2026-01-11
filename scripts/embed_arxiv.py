import argparse
import json
import os

import chromadb
from chromadb.utils import embedding_functions
from tqdm import tqdm

MODEL_NAME = "all-MiniLM-L6-v2"

# Paths relative to this script's location
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
DATA_FILE = os.path.join(_project_root, "arxiv-metadata-oai-snapshot.json")
CHROMA_DB_PATH = os.path.join(_project_root, "backend", "chroma_db")
BATCH_SIZE = 100  # Number of papers per batch for embedding


def get_year_from_arxiv_id(arxiv_id: str) -> int | None:
    """Extract publication year from arXiv ID.

    arXiv IDs use format YYMM.NNNNN (post-2007) or category/YYMMNNN (pre-2007).
    Returns the 4-digit year or None if unparseable.
    """
    try:
        # New format: YYMM.NNNNN (e.g., 2301.12345 = Jan 2023)
        if "." in arxiv_id:
            yymm = arxiv_id.split(".")[0]
            yy = int(yymm[:2])
        # Old format: category/YYMMNNN (e.g., hep-th/9901001 = Jan 1999)
        elif "/" in arxiv_id:
            yymm = arxiv_id.split("/")[1][:4]
            yy = int(yymm[:2])
        else:
            return None
        # Convert 2-digit year to 4-digit (07-99 = 1907-1999, 00-06 = 2000-2006)
        # arXiv started in 1991, so anything >= 91 is 19xx
        return 1900 + yy if yy >= 91 else 2000 + yy
    except (ValueError, IndexError):
        return None


def load_papers(filepath: str, limit: int | None, min_year: int | None = None) -> list[dict]:
    """Load papers from JSONL file, extracting only id, title, and abstract."""
    papers = []
    with open(filepath, "r") as f:
        for line in f:
            if limit is not None and len(papers) >= limit:
                break
            record = json.loads(line)
            # Filter by year if specified (using arXiv ID which encodes submission date)
            if min_year is not None:
                paper_year = get_year_from_arxiv_id(record["id"])
                if paper_year is None or paper_year < min_year:
                    continue
            papers.append({
                "id": record["id"],
                "title": record["title"].replace("\n", " ").strip(),
                "abstract": record["abstract"].replace("\n", " ").strip(),
                "categories": record.get("categories", ""),
            })
    return papers


def main():
    parser = argparse.ArgumentParser(
        description="Generate embeddings for arXiv papers and store them in ChromaDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python embed_arxiv.py --limit 1000       Embed 1000 papers (default)
  python embed_arxiv.py -l 10000           Embed 10000 papers
  python embed_arxiv.py --limit 0          Embed ALL papers
  python embed_arxiv.py --year 2010        Embed papers from 2010 onwards
  python embed_arxiv.py -y 2020 -l 5000    Embed 5000 papers from 2020 onwards
  python embed_arxiv.py --clean -l 5000    Clear vector DB and embed 5000 papers
"""
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=1000,
        help="Number of papers to embed (default: 1000, use 0 for all papers)"
    )
    parser.add_argument(
        "--clean", "-c",
        action="store_true",
        help="Delete existing embeddings before generating new ones"
    )
    parser.add_argument(
        "--year", "-y",
        type=int,
        default=None,
        help="Only include papers from this year onwards (e.g., 2010)"
    )
    args = parser.parse_args()

    # Always show usage summary
    print("arXiv Embeddings Generator")
    print(f"Using model {MODEL_NAME}")
    print(f"  --limit: {args.limit if args.limit > 0 else 'all'}")
    print(f"  --year: {args.year if args.year else 'any'}")
    print(f"  --clean: {args.clean}")
    print()

    # Initialize Chroma with persistent storage (in backend folder)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Set up embedding function
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=MODEL_NAME
    )

    # Clean existing collection if requested
    if args.clean:
        try:
            client.delete_collection(name="arxiv_papers")
            print("Deleted existing collection 'arxiv_papers'")
        except ValueError:
            print("No existing collection to delete")

    limit = args.limit if args.limit > 0 else None
    limit_str = str(limit) if limit else "all"
    year_str = f" from {args.year} onwards" if args.year else ""

    print(f"Reading {limit_str} papers{year_str} from {DATA_FILE}...")
    papers = load_papers(DATA_FILE, limit, args.year)
    print(f"Read {len(papers)} papers")

    # Create or get collection
    collection = client.get_or_create_collection(
        name="arxiv_papers",
        metadata={"description": "arXiv papers with title and abstract embeddings"},
        embedding_function=embedding_fn
    )

    # Generate embeddings in batches with progress bar
    print("Generating embeddings...")
    for i in tqdm(range(0, len(papers), BATCH_SIZE), desc="Embedding batches"):
        batch = papers[i:i + BATCH_SIZE]
        embedding_text = [f"{p['title']} {p['abstract']}" for p in batch]
        ids = [p["id"] for p in batch]
        metadatas = [{"title": p["title"], "categories": p["categories"]} for p in batch]

        collection.add(
            documents=embedding_text,
            ids=ids,
            metadatas=metadatas,
        )

    print(f"\nSuccessfully embedded {len(papers)} papers")
    print(f"Collection count: {collection.count()}")


if __name__ == "__main__":
    main()
