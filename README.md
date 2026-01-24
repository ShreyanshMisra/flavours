# Flavor Pairing Knowledge Graph

A knowledge graph application that models ingredients, their flavor compounds, and pairing relationships based on shared chemistry. Discover why certain ingredients pair well together through molecular gastronomy science.

## Features

- **Search Ingredients**: Find ingredients and explore their flavor profiles
- **Pairing Recommendations**: Get scientifically-backed pairing suggestions with explanations
- **Ingredient Comparison**: Compare two ingredients to see shared compounds
- **Graph Exploration**: Interactive D3.js visualization of ingredient relationships
- **Surprise Pairings**: Discover unexpected but chemically-justified combinations

## Tech Stack

- **Database**: Neo4j 5 (graph database)
- **Backend**: FastAPI (Python)
- **Frontend**: React 18 + Vite + D3.js
- **ETL**: Python (requests, pandas)
- **Deployment**: Docker Compose (local), Vercel (frontend)

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    FlavorDB     │────>│   ETL Pipeline  │────>│     Neo4j       │
│   (Data Source) │     │    (Python)     │     │ (Graph Database)│
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         v
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │<────│  FastAPI        │<────│  Cypher Queries │
│  (Vite + D3.js) │     │  (REST API)     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.10+
- Node.js 18+

### Local Development

1. **Start Neo4j**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up neo4j
   ```

2. **Load Data** (first time only):
   ```bash
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python -m etl.load
   ```

3. **Start API**:
   ```bash
   cd api && uvicorn main:app --reload
   ```

4. **Start Frontend**:
   ```bash
   cd frontend && npm install && npm run dev
   ```

5. Open http://localhost:5173

### Full Stack with Docker

```bash
export NEO4J_PASSWORD=yourpassword
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /ingredients` | List/search ingredients |
| `GET /ingredients/{id}` | Get ingredient details |
| `GET /ingredients/{id}/pairings` | Get pairing recommendations |
| `GET /ingredients/{id}/compounds` | Get flavor compounds |
| `GET /ingredients/{id1}/compare/{id2}` | Compare two ingredients |
| `GET /explore/graph` | Get graph visualization data |
| `GET /explore/surprise` | Get unexpected pairings |
| `GET /explore/categories` | List ingredient categories |
| `GET /health` | Health check |

Full API documentation available at `/docs` when running.

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

## Project Structure

```
flavor-pairing-kg/
├── api/                    # FastAPI backend
│   ├── routes/             # API endpoints
│   ├── models/             # Pydantic schemas
│   └── services/           # Neo4j connection
├── etl/                    # Data pipeline
│   ├── fetch.py            # FlavorDB acquisition
│   ├── clean.py            # Data normalization
│   ├── transform.py        # Pairing computation
│   └── load.py             # Neo4j import
├── frontend/               # React application
│   ├── src/pages/          # Main views
│   ├── src/components/     # UI components
│   └── src/hooks/          # API hooks
├── data/                   # Data files
│   ├── neo4j/              # Import CSVs
│   └── processed/          # Cleaned JSON
└── tests/                  # Test suite
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | Required |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000,http://localhost:5173` |
| `VITE_API_URL` | API URL for frontend | `http://localhost:8000` |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=api --cov=etl
```

## Data Sources & References

- **FlavorDB**: https://cosylab.iiitd.edu.in/flavordb/ - Primary data source for flavor compounds mapped to ingredients
- **FooDB**: https://foodb.ca/ - Supplementary food composition data
- **Foodpairing Research**: Ahn et al., "Flavor network and the principles of food pairing" (Scientific Reports, 2011) - https://www.nature.com/articles/srep00196

## Resources

- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [D3.js Force Simulation](https://d3js.org/d3-force)
- *The Flavor Bible* by Karen Page & Andrew Dornenburg
- *The Flavor Matrix* by James Briscione

## License

MIT
