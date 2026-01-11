# arXiv Papers Vector Search

A semantic search demo for arXiv research papers using vector embeddings. Search for papers by meaning rather than keywords.

## Technologies

- **Backend**: FastAPI, ChromaDB, sentence-transformers
- **Frontend**: React, TypeScript, Vite, Bun
- **Embeddings**: all-MiniLM-L6-v2 (384 dimensions)
- **Package Management**: uv (Python), Bun (JavaScript)
- **Deployment**: Docker Compose

<img width="1628" height="1109" alt="arxiv_search_screenshot" src="https://github.com/user-attachments/assets/70787dfe-d2e2-4376-8e9c-94b30252aafe" />

## Quick Start (Local)

```bash
# Start the application
docker compose up -d --build

# Access the frontend
open http://localhost
```

## Usage

### Generate Embeddings

Download the arXiv metadata dataset and generate embeddings locally before deployment:

```bash
# Download dataset (optional - ~4GB)
# https://www.kaggle.com/datasets/Cornell-University/arxiv

# Install dependencies
uv sync

# Generate embeddings (default: 1000 papers)
uv run python scripts/embed_arxiv.py

# Generate more embeddings with year filter
uv run python scripts/embed_arxiv.py --limit 10000 --year 2016

# Options:
#   --limit, -l    Number of papers (0 = all)
#   --year, -y     Filter papers from this year onwards
#   --clean, -c    Clear existing embeddings first
```

### EC2 Deployment

**Prerequisites:**

- Ubuntu EC2 instance (t3.medium recommended)
- 20GB+ EBS storage
- Security group: ports 22, 80, 8000 open

**Deploy:**

```bash
# 1. Upload project to EC2
scp -i ~/.ssh/your-key.pem -r . ubuntu@YOUR_EC2_IP:~/vector_database

# 2. SSH and run setup
ssh -i ~/.ssh/your-key.pem ubuntu@YOUR_EC2_IP
cd ~/vector_database
chmod +x scripts/ec2-setup.sh
./scripts/ec2-setup.sh

# 3. Log out and back in, then start
newgrp docker  # or logout/login
docker compose -f docker-compose.prod.yml up -d --build

# 4. Verify
curl http://localhost:8000/health
```

The setup script automatically detects your EC2 public IP and configures the `.env` file.

## Project Structure

```text
.
├── backend/
│   ├── api.py           # FastAPI application
│   ├── chroma_db/       # Vector database (generated)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   └── Dockerfile
├── scripts/
│   ├── embed_arxiv.py   # Embedding generation
│   └── ec2-setup.sh     # EC2 setup script
├── docker-compose.yml       # Local development
└── docker-compose.prod.yml  # Production deployment
```

## API Endpoints

- `GET /health` - Health check with collection count
- `POST /search` - Search papers by query

  ```json
  {"query": "neural networks", "n_results": 10}
  ```

## License

MIT
