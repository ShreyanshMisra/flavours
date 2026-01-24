# Flavor Pairing Frontend

React frontend for the Flavor Pairing Knowledge Graph.

## Setup

The frontend source files are pre-created in `src/`. You need to initialize the Vite project:

```bash
# From the frontend directory
cd frontend

# Initialize Vite (select React when prompted)
npm create vite@latest . -- --template react

# When prompted about existing files, choose to ignore/skip
# Or manually merge the package.json

# Install dependencies
npm install axios react-router-dom d3

# Start development server
npm run dev
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js       # API client
│   ├── components/
│   │   ├── SearchBar.jsx   # Autocomplete search
│   │   ├── IngredientCard.jsx
│   │   ├── PairingList.jsx
│   │   ├── GraphExplorer.jsx  # D3.js visualization
│   │   └── CompoundBadge.jsx
│   ├── hooks/
│   │   └── useApi.js       # Data fetching hooks
│   ├── pages/
│   │   ├── Home.jsx        # Landing page
│   │   ├── Ingredient.jsx  # Ingredient detail
│   │   ├── Compare.jsx     # Side-by-side comparison
│   │   └── Explore.jsx     # Graph exploration
│   ├── App.jsx
│   ├── App.css
│   ├── main.jsx
│   └── index.css
```

## Environment Variables

Create a `.env.local` file:

```
VITE_API_URL=http://localhost:8000
```

## Available Pages

- `/` - Home page with search, stats, and featured pairings
- `/ingredient/:id` - Ingredient detail with pairings and compounds
- `/compare` - Compare two ingredients side-by-side
- `/explore` - Interactive graph visualization
