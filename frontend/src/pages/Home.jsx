/**
 * Home Page
 *
 * Main landing page with knowledge graph visualization and stats.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { GraphExplorer } from '../components/GraphExplorer';
import { useStats } from '../hooks/useApi';
import api, { waitForBackend } from '../api/client';
import './Home.css';

export function Home() {
  const navigate = useNavigate();
  const { data: stats } = useStats();
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchGraph = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // The free-tier backend may still be waking up on first load
      await waitForBackend();
      const randomIng = await api.getRandomIngredient();
      const data = await api.getGraphData(randomIng.id, { minScore: 0.3, limit: 25 });
      setGraphData(data);
    } catch (err) {
      console.error('Failed to load graph:', err);
      setError('Could not load the knowledge graph. The server may still be waking up.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch graph data on mount
  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  // Handle resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({
          width: rect.width,
          height: Math.max(400, rect.height)
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  return (
    <div className="home-page">
      <header className="home-header">
        <h1>Flavour Pairing Knowledge Graph</h1>
        <p>Discover ingredient pairings through shared flavor compounds</p>
      </header>

      {stats && (
        <div className="stats-row">
          <div className="stat-item">
            <span className="stat-value">{stats.ingredients.toLocaleString()}</span>
            <span className="stat-label">Ingredients</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-value">{stats.compounds.toLocaleString()}</span>
            <span className="stat-label">Compounds</span>
          </div>
          <div className="stat-divider" />
          <div className="stat-item">
            <span className="stat-value">{stats.pairings.toLocaleString()}</span>
            <span className="stat-label">Pairings</span>
          </div>
        </div>
      )}

      <div className="graph-container" ref={containerRef}>
        {loading && (
          <div className="graph-loading">
            <div className="spinner" aria-label="Loading graph" />
            <span>Loading knowledge graph...</span>
          </div>
        )}

        {!loading && error && (
          <div className="graph-error" role="alert">
            <p>{error}</p>
            <button onClick={fetchGraph} className="refresh-btn">
              Retry
            </button>
          </div>
        )}

        {!loading && !error && graphData && (
          <>
            <GraphExplorer
              className="frameless"
              data={graphData}
              width={dimensions.width}
              height={dimensions.height}
              onNodeClick={(node) => navigate(`/ingredient/${node.id}`)}
            />
            <div className="graph-actions">
              <button onClick={fetchGraph} className="refresh-btn" aria-label="Load different ingredient graph">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <path d="M23 4v6h-6M1 20v-6h6" />
                  <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
                </svg>
                New Graph
              </button>
            </div>
            <p className="graph-hint">Click any node to explore. Drag to rearrange. Scroll to zoom.</p>
          </>
        )}
      </div>
    </div>
  );
}

export default Home;
