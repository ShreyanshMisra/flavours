/**
 * Ingredient Detail Page
 *
 * Shows ingredient details, compounds, and pairing recommendations.
 */

import { useParams, useNavigate, Link } from 'react-router-dom';
import { useIngredient, useGraphData } from '../hooks/useApi';
import { PairingList } from '../components/PairingList';
import { CompoundBadge } from '../components/CompoundBadge';
import { GraphExplorer } from '../components/GraphExplorer';
import { getCategoryColor } from '../components/IngredientCard';
import './Ingredient.css';

export function Ingredient() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { ingredient, compounds, pairings, loading, error } = useIngredient(id);
  const { graphData } = useGraphData(id, { minScore: 0.4, limit: 15 });

  if (loading) {
    return (
      <div className="ingredient-page">
        <div className="loading">Loading ingredient...</div>
      </div>
    );
  }

  if (error || !ingredient) {
    return (
      <div className="ingredient-page">
        <div className="error">
          <h2>Ingredient Not Found</h2>
          <p>{error || "The requested ingredient doesn't exist."}</p>
          <Link to="/" className="back-link">Go back home</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="ingredient-page">
      {/* Header */}
      <header
        className="ingredient-header"
        style={{ '--category-color': getCategoryColor(ingredient.category) }}
      >
        <div className="header-content">
          <div className="breadcrumb">
            <Link to="/">Home</Link>
            <span>/</span>
            <Link to={`/browse?category=${ingredient.category}`}>
              {ingredient.category}
            </Link>
          </div>

          <h1>{ingredient.name}</h1>

          <div className="ingredient-meta">
            <span className="category-badge">{ingredient.category}</span>
            {ingredient.subcategory && (
              <span className="subcategory">{ingredient.subcategory}</span>
            )}
          </div>

          {ingredient.aliases && ingredient.aliases.length > 0 && (
            <p className="aliases">
              Also known as: {ingredient.aliases.join(', ')}
            </p>
          )}
        </div>
      </header>

      <div className="ingredient-content">
        {/* Pairings Section */}
        <section className="pairings-section">
          <div className="section-header">
            <h2>Best Pairings</h2>
            <span className="section-count">{pairings.length} found</span>
          </div>

          <PairingList
            pairings={pairings}
            onSelect={(pairing) => navigate(`/ingredient/${pairing.id}`)}
          />

          {pairings.length > 0 && (
            <div className="compare-cta">
              <p>Want to compare with another ingredient?</p>
              <Link to={`/compare?ing1=${id}`} className="compare-link">
                Compare ingredients
              </Link>
            </div>
          )}
        </section>

        {/* Sidebar */}
        <aside className="ingredient-sidebar">
          {/* Compounds */}
          <section className="compounds-section">
            <h3>Flavor Compounds ({compounds.length})</h3>

            {compounds.length > 0 ? (
              <div className="compounds-list">
                {compounds.slice(0, 10).map((compound) => (
                  <CompoundBadge
                    key={compound.id}
                    compound={compound}
                    showConcentration={true}
                  />
                ))}
                {compounds.length > 10 && (
                  <p className="compounds-more">
                    +{compounds.length - 10} more compounds
                  </p>
                )}
              </div>
            ) : (
              <p className="no-compounds">No compound data available</p>
            )}
          </section>

          {/* Graph Preview */}
          {graphData.nodes.length > 1 && (
            <section className="graph-section">
              <h3>Pairing Network</h3>
              <GraphExplorer
                data={graphData}
                width={350}
                height={300}
                onNodeClick={(node) => {
                  if (node.id !== id) {
                    navigate(`/ingredient/${node.id}`);
                  }
                }}
              />
              <Link to={`/explore?center=${id}`} className="explore-link">
                Explore full graph
              </Link>
            </section>
          )}
        </aside>
      </div>
    </div>
  );
}

export default Ingredient;
