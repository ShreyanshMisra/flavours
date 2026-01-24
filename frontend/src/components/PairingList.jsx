/**
 * PairingList Component
 *
 * Display list of pairing recommendations with scores and explanations.
 */

import { Link } from 'react-router-dom';
import { getCategoryColor } from './IngredientCard';
import './PairingList.css';

export function PairingList({ pairings, onSelect }) {
  if (!pairings || pairings.length === 0) {
    return (
      <div className="pairing-list-empty">
        No pairings found
      </div>
    );
  }

  return (
    <div className="pairing-list">
      {pairings.map((pairing) => (
        <PairingCard
          key={pairing.id}
          pairing={pairing}
          onSelect={onSelect}
        />
      ))}
    </div>
  );
}

export function PairingCard({ pairing, onSelect }) {
  const scorePercent = Math.round(pairing.score * 100);
  const scoreClass = pairing.score > 0.7 ? 'excellent' :
                     pairing.score > 0.5 ? 'good' : 'moderate';

  const content = (
    <div
      className="pairing-card"
      onClick={() => onSelect?.(pairing)}
      style={{ '--category-color': getCategoryColor(pairing.category) }}
    >
      <div className="pairing-header">
        <div className="pairing-info">
          <span className="pairing-name">{pairing.name}</span>
          <span className="pairing-category">{pairing.category}</span>
        </div>
        <div className={`pairing-score ${scoreClass}`}>
          {scorePercent}%
        </div>
      </div>

      {pairing.key_compounds && pairing.key_compounds.length > 0 && (
        <div className="pairing-compounds">
          {pairing.key_compounds.slice(0, 3).map((compound, i) => (
            <span key={i} className="compound-badge">
              {compound}
            </span>
          ))}
          {pairing.key_compounds.length > 3 && (
            <span className="compound-more">
              +{pairing.key_compounds.length - 3} more
            </span>
          )}
        </div>
      )}

      {pairing.explanation && (
        <p className="pairing-explanation">{pairing.explanation}</p>
      )}

      <div className="pairing-meta">
        <span>{pairing.shared_compounds} shared compounds</span>
      </div>
    </div>
  );

  if (!onSelect) {
    return (
      <Link to={`/ingredient/${pairing.id}`} className="pairing-card-link">
        {content}
      </Link>
    );
  }

  return content;
}

export default PairingList;
