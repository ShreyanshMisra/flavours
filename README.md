# Flavor Pairing Knowledge Graph

A knowledge graph application that models ingredients, their flavor compounds, and pairing relationships based on shared chemistry. Discover why certain ingredients pair well together through molecular gastronomy science.

## Features

- **Search Ingredients**: Find ingredients and explore their flavor profiles
- **Pairing Recommendations**: Get scientifically-backed pairing suggestions with explanations
- **Ingredient Comparison**: Compare two ingredients to see shared compounds
- **Graph Exploration**: Interactive D3.js visualization of ingredient relationships
- **Surprise Pairings**: Discover unexpected but chemically-justified combinations

## Tech Stack

- **Database**: Neo4j Aura (graph database)
- **Backend**: FastAPI (Python) on Render
- **Frontend**: React 18 + Vite + D3.js on Vercel

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