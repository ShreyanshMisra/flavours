/**
 * IngredientCard Component
 *
 * Display card for an ingredient with category badge.
 */

import { Link } from 'react-router-dom';
import './IngredientCard.css';

// Category colors
const categoryColors = {
  fruit: '#ff6b6b',
  vegetable: '#51cf66',
  dairy: '#ffd43b',
  protein: '#845ef7',
  grain: '#f59f00',
  spice: '#e67700',
  herb: '#40c057',
  seafood: '#339af0',
  beverage: '#20c997',
  nut: '#a0522d',
  legume: '#8b4513',
  fungus: '#9370db',
  oil: '#ffd700',
  plant: '#228b22',
  other: '#868e96',
};

export function getCategoryColor(category) {
  return categoryColors[category?.toLowerCase()] || categoryColors.other;
}

export function IngredientCard({ ingredient, onClick, showLink = true }) {
  const content = (
    <div
      className="ingredient-card"
      onClick={onClick}
      style={{ '--category-color': getCategoryColor(ingredient.category) }}
    >
      <div className="ingredient-card-header">
        <h3 className="ingredient-name">{ingredient.name}</h3>
        <span className="category-badge">{ingredient.category}</span>
      </div>
      {ingredient.subcategory && (
        <p className="ingredient-subcategory">{ingredient.subcategory}</p>
      )}
    </div>
  );

  if (showLink && !onClick) {
    return (
      <Link to={`/ingredient/${ingredient.id}`} className="ingredient-card-link">
        {content}
      </Link>
    );
  }

  return content;
}

export function IngredientCardCompact({ ingredient, onClick }) {
  return (
    <div
      className="ingredient-card-compact"
      onClick={onClick}
      style={{ '--category-color': getCategoryColor(ingredient.category) }}
    >
      <span className="ingredient-name">{ingredient.name}</span>
      <span className="category-dot" />
    </div>
  );
}

export default IngredientCard;
