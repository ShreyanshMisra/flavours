/**
 * Home Page
 *
 * Landing page with search, stats, and featured pairings.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SearchBar } from '../components/SearchBar';
import { IngredientCard } from '../components/IngredientCard';
import { useStats, useSurprisePairings, useCategories } from '../hooks/useApi';
import api from '../api/client';
import './Home.css';

export function Home() {
  const navigate = useNavigate();
  const { data: stats } = useStats();
  const { data: surprisePairings } = useSurprisePairings({ limit: 6 });
  const { data: categories } = useCategories();
  const [randomIngredient, setRandomIngredient] = useState(null);

  const handleSurpriseMe = async () => {
    try {
      const ingredient = await api.getRandomIngredient();
      setRandomIngredient(ingredient);
      // Navigate after a short delay to show the selection
      setTimeout(() => {
        navigate(`/ingredient/${ingredient.id}`);
      }, 500);
    } catch (error) {
      console.error('Failed to get random ingredient:', error);
    }
  };

  return (
    <div className="home-page">
      {/* Hero Section */}
      <section className="hero">
        <h1>Flavor Pairing Explorer</h1>
        <p className="hero-subtitle">
          Discover unexpected ingredient combinations backed by food science
        </p>

        <div className="hero-search">
          <SearchBar placeholder="Search for an ingredient..." />
        </div>

        <button className="surprise-button" onClick={handleSurpriseMe}>
          Surprise Me
        </button>

        {randomIngredient && (
          <div className="random-selection">
            Selected: <strong>{randomIngredient.name}</strong>
          </div>
        )}
      </section>

      {/* Stats Section */}
      {stats && (
        <section className="stats-section">
          <div className="stat-card">
            <span className="stat-number">{stats.ingredients.toLocaleString()}</span>
            <span className="stat-label">Ingredients</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">{stats.compounds.toLocaleString()}</span>
            <span className="stat-label">Flavor Compounds</span>
          </div>
          <div className="stat-card">
            <span className="stat-number">{stats.pairings.toLocaleString()}</span>
            <span className="stat-label">Pairings</span>
          </div>
        </section>
      )}

      {/* Surprise Pairings Section */}
      {surprisePairings && surprisePairings.length > 0 && (
        <section className="surprise-section">
          <h2>Unexpected Pairings</h2>
          <p className="section-subtitle">
            High-scoring combinations from different categories
          </p>

          <div className="surprise-grid">
            {surprisePairings.map((pairing, index) => (
              <div key={index} className="surprise-card">
                <div className="surprise-pair">
                  <IngredientCard
                    ingredient={pairing.ingredient_1}
                    showLink={true}
                  />
                  <span className="plus-sign">+</span>
                  <IngredientCard
                    ingredient={pairing.ingredient_2}
                    showLink={true}
                  />
                </div>
                <div className="surprise-score">
                  {Math.round(pairing.score * 100)}% match
                </div>
                <p className="surprise-explanation">{pairing.explanation}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Categories Section */}
      {categories && categories.length > 0 && (
        <section className="categories-section">
          <h2>Browse by Category</h2>

          <div className="category-grid">
            {categories.slice(0, 12).map((category) => (
              <button
                key={category.id}
                className="category-button"
                onClick={() => navigate(`/browse?category=${category.id}`)}
              >
                <span className="category-name">{category.name}</span>
                <span className="category-count">{category.count}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* About Section */}
      <section className="about-section">
        <h2>How It Works</h2>
        <div className="about-grid">
          <div className="about-card">
            <h3>Flavor Compounds</h3>
            <p>
              Every ingredient contains hundreds of flavor compounds - molecules
              that contribute to taste and aroma.
            </p>
          </div>
          <div className="about-card">
            <h3>Shared Chemistry</h3>
            <p>
              Ingredients that share key flavor compounds often pair well together,
              creating harmonious taste combinations.
            </p>
          </div>
          <div className="about-card">
            <h3>Discovery</h3>
            <p>
              Explore unexpected pairings like strawberry + balsamic or chocolate +
              blue cheese, backed by molecular analysis.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
