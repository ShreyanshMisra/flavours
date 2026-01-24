/**
 * Compare Page
 *
 * Side-by-side comparison of two ingredients.
 */

import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SearchBar } from '../components/SearchBar';
import { IngredientCard, getCategoryColor } from '../components/IngredientCard';
import { CompoundBadge } from '../components/CompoundBadge';
import { useComparison } from '../hooks/useApi';
import api from '../api/client';
import './Compare.css';

export function Compare() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [ingredient1, setIngredient1] = useState(null);
  const [ingredient2, setIngredient2] = useState(null);

  const { comparison, loading, error } = useComparison(
    ingredient1?.id,
    ingredient2?.id
  );

  // Load ingredients from URL params on mount
  useEffect(() => {
    const loadFromParams = async () => {
      const ing1 = searchParams.get('ing1');
      const ing2 = searchParams.get('ing2');

      if (ing1) {
        try {
          const data = await api.getIngredient(ing1);
          setIngredient1(data);
        } catch (e) {
          console.error('Failed to load ingredient 1:', e);
        }
      }

      if (ing2) {
        try {
          const data = await api.getIngredient(ing2);
          setIngredient2(data);
        } catch (e) {
          console.error('Failed to load ingredient 2:', e);
        }
      }
    };

    loadFromParams();
  }, []);

  // Update URL when ingredients change
  useEffect(() => {
    const params = new URLSearchParams();
    if (ingredient1) params.set('ing1', ingredient1.id);
    if (ingredient2) params.set('ing2', ingredient2.id);
    setSearchParams(params, { replace: true });
  }, [ingredient1, ingredient2, setSearchParams]);

  const handleSelect1 = (ingredient) => {
    setIngredient1(ingredient);
  };

  const handleSelect2 = (ingredient) => {
    setIngredient2(ingredient);
  };

  const handleSwap = () => {
    const temp = ingredient1;
    setIngredient1(ingredient2);
    setIngredient2(temp);
  };

  const handleClear = () => {
    setIngredient1(null);
    setIngredient2(null);
  };

  return (
    <div className="compare-page">
      <header className="compare-header">
        <h1>Compare Ingredients</h1>
        <p>See what flavor compounds two ingredients share</p>
      </header>

      {/* Selection Area */}
      <div className="compare-selection">
        <div className="selection-slot">
          <h3>Ingredient 1</h3>
          {ingredient1 ? (
            <div className="selected-ingredient">
              <IngredientCard ingredient={ingredient1} showLink={false} />
              <button
                className="clear-button"
                onClick={() => setIngredient1(null)}
              >
                ×
              </button>
            </div>
          ) : (
            <SearchBar
              onSelect={handleSelect1}
              placeholder="Search first ingredient..."
            />
          )}
        </div>

        <div className="selection-controls">
          <button
            className="swap-button"
            onClick={handleSwap}
            disabled={!ingredient1 && !ingredient2}
          >
            ⇄
          </button>
        </div>

        <div className="selection-slot">
          <h3>Ingredient 2</h3>
          {ingredient2 ? (
            <div className="selected-ingredient">
              <IngredientCard ingredient={ingredient2} showLink={false} />
              <button
                className="clear-button"
                onClick={() => setIngredient2(null)}
              >
                ×
              </button>
            </div>
          ) : (
            <SearchBar
              onSelect={handleSelect2}
              placeholder="Search second ingredient..."
            />
          )}
        </div>
      </div>

      {/* Results */}
      {loading && (
        <div className="compare-loading">
          Analyzing shared compounds...
        </div>
      )}

      {error && (
        <div className="compare-error">
          Error comparing ingredients: {error}
        </div>
      )}

      {comparison && (
        <div className="compare-results">
          {/* Score Banner */}
          {comparison.pairing_score !== null && (
            <div
              className="pairing-banner"
              style={{
                '--score-color': comparison.pairing_score > 0.6 ? '#2b8a3e' :
                                 comparison.pairing_score > 0.4 ? '#e67700' : '#c92a2a'
              }}
            >
              <div className="banner-score">
                {Math.round(comparison.pairing_score * 100)}%
              </div>
              <div className="banner-text">
                <strong>Pairing Score</strong>
                <span>{comparison.explanation}</span>
              </div>
            </div>
          )}

          {/* Shared Compounds */}
          <section className="shared-compounds">
            <h2>
              Shared Compounds
              <span className="count">({comparison.shared_count})</span>
            </h2>

            {comparison.shared_compounds.length > 0 ? (
              <div className="compounds-comparison">
                {comparison.shared_compounds.map((compound) => (
                  <div key={compound.id} className="compound-comparison-row">
                    <div
                      className="concentration-bar left"
                      style={{
                        '--width': `${compound.concentration_1 * 100}%`,
                        '--color': getCategoryColor(ingredient1?.category)
                      }}
                    >
                      <span>{Math.round(compound.concentration_1 * 100)}%</span>
                    </div>

                    <div className="compound-center">
                      <strong>{compound.name}</strong>
                      {compound.common_name && compound.common_name !== compound.name && (
                        <span className="common-name">{compound.common_name}</span>
                      )}
                    </div>

                    <div
                      className="concentration-bar right"
                      style={{
                        '--width': `${compound.concentration_2 * 100}%`,
                        '--color': getCategoryColor(ingredient2?.category)
                      }}
                    >
                      <span>{Math.round(compound.concentration_2 * 100)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-shared">
                These ingredients don't share any flavor compounds in our database.
              </p>
            )}
          </section>

          <button className="clear-all" onClick={handleClear}>
            Compare different ingredients
          </button>
        </div>
      )}

      {/* Empty State */}
      {!ingredient1 && !ingredient2 && (
        <div className="compare-empty">
          <p>Select two ingredients above to compare their flavor profiles</p>
        </div>
      )}
    </div>
  );
}

export default Compare;
