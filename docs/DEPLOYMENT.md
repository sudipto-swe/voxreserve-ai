# LOCAL DEPLOYMENT & EXECUTION GUIDE

## Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Node.js 18+ (tested on Node v20)
- Optional: Ollama (for running local LLM like `llama3.2`)
- Optional: Docker & Docker Compose

## Quick Start (Local Development)

### 1. Clone & Configure Environment
```bash
cp .env.example .env
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Seed realistic demo data
PYTHONPATH=. python scripts/seed_data.py

# Start FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
In another terminal:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in Chrome, Edge, or Safari.

### 4. Optional: Run Local Ollama LLM
```bash
ollama run llama3.2:latest
```
*Note: If Ollama is not running, VOXRESERVE automatically engages its intelligent deterministic rule engine, allowing full conversational bookings, hours inquiries, menu lookups, and allergen checks.*

### 5. Running with Docker Compose
```bash
docker-compose up --build
```
Access frontend at `http://localhost:5173` and backend at `http://localhost:8000`.
