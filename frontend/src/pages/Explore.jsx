/**
 * Explore Page
 *
 * Full-screen graph exploration view.
 */

import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { SearchBar } from '../components/SearchBar';
import { GraphExplorer } from '../components/GraphExplorer';
import { IngredientCard } from '../components/IngredientCard';
import { useGraphData } from '../hooks/useApi';
import api from '../api/client';
import './Explore.css';

export function Explore() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [centerIngredient, setCenterIngredient] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [minScore, setMinScore] = useState(0.4);
  const [nodeLimit, setNodeLimit] = useState(20);

  const centerId = centerIngredient?.id;
  const { graphData, loading, error, refetch } = useGraphData(centerId, {
    minScore,
    limit: nodeLimit,
  });

  // Load center ingredient from URL
  useEffect(() => {
    const center = searchParams.get('center');
    if (center && !centerIngredient) {
      api.getIngredient(center)
        .then(setCenterIngredient)
        .catch(console.error);
    }
  }, [searchParams]);

  // Update URL when center changes
  useEffect(() => {
    if (centerIngredient) {
      setSearchParams({ center: centerIngredient.id }, { replace: true });
    }
  }, [centerIngredient, setSearchParams]);

  const handleSelectCenter = (ingredient) => {
    setCenterIngredient(ingredient);
    setSelectedNode(null);
  };

  const handleNodeClick = (node) => {
    if (node.id === centerId) {
      setSelectedNode(null);
    } else {
      setSelectedNode(node);
    }
  };

  const handleRecenter = () => {
    if (selectedNode) {
      api.getIngredient(selectedNode.id)
        .then((ing) => {
          setCenterIngredient(ing);
          setSelectedNode(null);
        })
        .catch(console.error);
    }
  };

  const handleViewDetails = () => {
    if (selectedNode) {
      navigate(`/ingredient/${selectedNode.id}`);
    }
  };

  return (
    <div className="explore-page">
      {/* Sidebar */}
      <aside className="explore-sidebar">
        <div className="sidebar-section">
          <h3>Center Ingredient</h3>
          {centerIngredient ? (
            <div className="center-ingredient">
              <IngredientCard
                ingredient={centerIngredient}
                showLink={false}
              />
              <button
                className="change-center"
                onClick={() => setCenterIngredient(null)}
              >
                Change
              </button>
            </div>
          ) : (
            <SearchBar
              onSelect={handleSelectCenter}
              placeholder="Select center..."
            />
          )}
        </div>

        <div className="sidebar-section">
          <h3>Filters</h3>

          <label className="filter-label">
            Min Pairing Score: {Math.round(minScore * 100)}%
            <input
              type="range"
              min="0"
              max="0.9"
              step="0.1"
              value={minScore}
              onChange={(e) => setMinScore(parseFloat(e.target.value))}
            />
          </label>

          <label className="filter-label">
            Max Connections: {nodeLimit}
            <input
              type="range"
              min="5"
              max="50"
              step="5"
              value={nodeLimit}
              onChange={(e) => setNodeLimit(parseInt(e.target.value))}
            />
          </label>
        </div>

        {selectedNode && (
          <div className="sidebar-section selected-section">
            <h3>Selected</h3>
            <div className="selected-info">
              <strong>{selectedNode.name}</strong>
              <span className="selected-category">{selectedNode.category}</span>
            </div>
            <div className="selected-actions">
              <button onClick={handleRecenter}>
                Make Center
              </button>
              <button onClick={handleViewDetails}>
                View Details
              </button>
            </div>
          </div>
        )}

        <div className="sidebar-section">
          <h3>Legend</h3>
          <div className="legend">
            <div className="legend-item">
              <span className="legend-node center" />
              <span>Center ingredient</span>
            </div>
            <div className="legend-item">
              <span className="legend-node" />
              <span>Connected ingredient</span>
            </div>
            <div className="legend-item">
              <span className="legend-line thick" />
              <span>Strong pairing</span>
            </div>
            <div className="legend-item">
              <span className="legend-line thin" />
              <span>Weaker pairing</span>
            </div>
          </div>
        </div>

        <div className="sidebar-section">
          <h3>Tips</h3>
          <ul className="tips-list">
            <li>Drag nodes to rearrange</li>
            <li>Scroll to zoom in/out</li>
            <li>Click a node to select it</li>
            <li>Thicker lines = stronger pairings</li>
          </ul>
        </div>
      </aside>

      {/* Main Graph Area */}
      <main className="explore-main">
        {!centerIngredient && (
          <div className="explore-empty">
            <h2>Select an ingredient to explore</h2>
            <p>Use the search in the sidebar to choose a starting point</p>
          </div>
        )}

        {loading && (
          <div className="explore-loading">
            Loading graph...
          </div>
        )}

        {error && (
          <div className="explore-error">
            Error loading graph: {error}
          </div>
        )}

        {centerIngredient && !loading && graphData.nodes.length > 0 && (
          <GraphExplorer
            data={graphData}
            width={window.innerWidth - 320}
            height={window.innerHeight - 40}
            onNodeClick={handleNodeClick}
          />
        )}

        {centerIngredient && !loading && graphData.nodes.length <= 1 && (
          <div className="explore-no-connections">
            <h2>No connections found</h2>
            <p>
              Try lowering the minimum score or this ingredient may not have
              strong pairings in our database.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

export default Explore;
