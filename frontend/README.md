# Flavor Pairing Frontend

React + Vite + D3.js frontend for the Flavor Pairing Knowledge Graph.

## Setup

```bash
npm install
npm run dev        # http://localhost:3000
```

The dev server expects the API at `http://localhost:8000`. To point at a
different backend, create `.env.local`:

```
VITE_API_URL=https://your-api-host
```

## Scripts

- `npm run dev` — development server with hot reload
- `npm run build` — production build into `dist/`
- `npm run preview` — serve the production build locally

## Project Structure

```
src/
├── api/
│   └── client.js          # fetch-based API client + backend warmup helper
├── components/
│   ├── SearchBar.jsx      # Autocomplete search
│   ├── IngredientCard.jsx
│   ├── PairingList.jsx
│   ├── GraphExplorer.jsx  # D3.js force-directed graph
│   ├── CompoundBadge.jsx
│   └── WarmupOverlay.jsx  # Overlay while the free-tier backend wakes up
├── context/
│   └── ThemeContext.jsx   # Light/dark theme
├── hooks/
│   └── useApi.js          # Data-fetching hooks
├── pages/
│   ├── Home.jsx           # Landing page with graph + stats
│   ├── Ingredient.jsx     # Ingredient detail
│   ├── Compare.jsx        # Side-by-side comparison
│   ├── Explore.jsx        # Full-screen graph exploration
│   └── About.jsx
├── App.jsx
└── main.jsx
```

## Pages

- `/` — home page with knowledge graph visualization and stats
- `/ingredient/:id` — ingredient detail with pairings and compounds
- `/compare` — compare two ingredients side-by-side
- `/explore` — interactive graph exploration with filters
- `/about` — project background
