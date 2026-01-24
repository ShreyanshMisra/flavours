/**
 * CompoundBadge Component
 *
 * Display badge for a flavor compound.
 */

import './CompoundBadge.css';

export function CompoundBadge({ compound, showConcentration = false, onClick }) {
  const concentrationPercent = compound.concentration
    ? Math.round(compound.concentration * 100)
    : null;

  return (
    <div
      className={`compound-badge-full ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
    >
      <div className="compound-header">
        <span className="compound-name">{compound.name}</span>
        {showConcentration && concentrationPercent !== null && (
          <span className="compound-concentration">{concentrationPercent}%</span>
        )}
      </div>
      {compound.common_name && compound.common_name !== compound.name && (
        <span className="compound-common-name">{compound.common_name}</span>
      )}
      {compound.odor_description && (
        <p className="compound-odor">{compound.odor_description}</p>
      )}
    </div>
  );
}

export function CompoundTag({ name, onClick }) {
  return (
    <span
      className={`compound-tag ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
    >
      {name}
    </span>
  );
}

export default CompoundBadge;
