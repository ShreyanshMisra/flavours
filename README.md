# Flavor Pairing Knowledge Graph

A knowledge graph application that models ingredients, their flavor compounds, and pairing relationships based on shared chemistry. Discover why certain ingredients pair well together through molecular gastronomy science.

<img width="1440" height="809" alt="Screenshot 2026-04-28 at 11 06 27 AM" src="https://github.com/user-attachments/assets/a5eda96a-e1c2-4963-8068-0ec1b985bf8f" />

## Features

- **Search Ingredients**: Find ingredients and explore their flavor profiles
- **Pairing Recommendations**: Get scientifically-backed pairing suggestions with explanations
- **Ingredient Comparison**: Compare two ingredients to see shared compounds
- **Graph Exploration**: Interactive D3.js visualization of ingredient relationships
- **Surprise Pairings**: Discover unexpected but chemically-justified combinations

## Tech Stack

- **Database**: Neo4j Aura (graph database)
- **Backend**: FastAPI (Python) on Render
- **Frontend**: React 18, Vite, D3.js deployed with Vercel

## Architecture

```
 FlavorDB (cosylab)
        │
        ▼
 ┌─────────────────────────────────────────┐
 │ ETL pipeline (etl/)                     │
 │ fetch.py → clean.py → transform.py      │
 │ (scrape)   (normalize)  (pairing scores │
 │                          + Neo4j CSVs)  │
 └──────────────────┬──────────────────────┘
                    │ load_aura.py / load.py
                    ▼
            ┌──────────────┐      ┌─────────────────┐      ┌──────────────────┐
            │  Neo4j Aura  │◄─────│  FastAPI (api/) │◄─────│ React + D3       │
            │  (graph DB)  │ bolt │  on Render      │ HTTP │ (frontend/)      │
            └──────────────┘      └─────────────────┘      │ on Vercel        │
                                                           └──────────────────┘
```

## Running Locally

### Prerequisites

- Python 3.11+ and Node.js 18+
- A Neo4j database: either a free [Neo4j Aura](https://neo4j.com/cloud/aura/) instance, or a local one via `docker-compose up neo4j`

### 1. Backend (FastAPI)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Create .env in the repo root with your database credentials:
#   NEO4J_URI=neo4j+s://<your-instance>.databases.neo4j.io
#   NEO4J_USER=<user>
#   NEO4J_PASSWORD=<password>
#   NEO4J_DATABASE=<database>   # omit for local Neo4j

cd api
uvicorn main:app --reload --port 8000
```

API docs are served at http://localhost:8000/docs.

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev            # http://localhost:3000, expects the API on :8000
```

Set `VITE_API_URL` in `frontend/.env.local` if the API runs elsewhere.

### 3. (Optional) Rebuild the dataset

The Neo4j-ready CSVs are already committed under `data/neo4j/`. To regenerate
them from scratch:

```bash
python etl/fetch.py        # scrape FlavorDB into data/raw/
python etl/clean.py        # normalize into data/processed/
python etl/transform.py    # compute pairing scores, write data/neo4j/*.csv
python etl/load_aura.py    # load into Neo4j Aura (or load.py for local Neo4j)
```

### Tests

```bash
pytest                     # API tests run against a mocked database;
                           # data tests need data/processed/ from the ETL step
```

## Graph Schema

```
(:Ingredient)-[:CONTAINS]->(:FlavorCompound)
(:Ingredient)-[:BELONGS_TO]->(:Category)
(:FlavorCompound)-[:HAS_PROFILE]->(:TasteProfile)
(:Ingredient)-[:PAIRS_WITH {score, shared_compounds, explanation}]->(:Ingredient)
```

## Pairing Algorithm

Pairing scores are computed using weighted compound overlap:

1. Find shared flavor compounds between two ingredients
2. Calculate weighted Jaccard similarity based on compound concentrations
3. Apply diminishing returns to avoid over-scoring identical ingredients
4. Generate human-readable explanations based on key shared compounds

## References

- **FlavorDB**: https://cosylab.iiitd.edu.in/flavordb/ - Primary data source for flavor compounds mapped to ingredients
- **FooDB**: https://foodb.ca/ - Supplementary food composition data
- **Foodpairing Research**: Ahn et al., "Flavor network and the principles of food pairing" (Scientific Reports, 2011) - https://www.nature.com/articles/srep00196
