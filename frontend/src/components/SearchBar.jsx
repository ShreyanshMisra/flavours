/**
 * SearchBar Component
 *
 * Autocomplete search input for ingredients.
 */

import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSearch } from '../hooks/useApi';
import './SearchBar.css';

export function SearchBar({ onSelect, placeholder = "Search ingredients..." }) {
  const navigate = useNavigate();
  const { query, setQuery, results, loading } = useSearch();
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef(null);
  const listRef = useRef(null);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (inputRef.current && !inputRef.current.contains(event.target) &&
          listRef.current && !listRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (e) => {
    setQuery(e.target.value);
    setIsOpen(true);
    setSelectedIndex(-1);
  };

  const handleSelect = (ingredient) => {
    setQuery('');
    setIsOpen(false);

    if (onSelect) {
      onSelect(ingredient);
    } else {
      navigate(`/ingredient/${ingredient.id}`);
    }
  };

  const handleKeyDown = (e) => {
    if (!isOpen || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < results.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0) {
          handleSelect(results[selectedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  return (
    <div className="search-bar">
      <input
        ref={inputRef}
        type="text"
        value={query}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={() => query && setIsOpen(true)}
        placeholder={placeholder}
        className="search-input"
      />

      {loading && <span className="search-loading">...</span>}

      {isOpen && results.length > 0 && (
        <ul ref={listRef} className="search-results">
          {results.map((ingredient, index) => (
            <li
              key={ingredient.id}
              className={`search-result-item ${index === selectedIndex ? 'selected' : ''}`}
              onClick={() => handleSelect(ingredient)}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <span className="result-name">{ingredient.name}</span>
              <span className="result-category">{ingredient.category}</span>
            </li>
          ))}
        </ul>
      )}

      {isOpen && query && results.length === 0 && !loading && (
        <div className="search-no-results">No ingredients found</div>
      )}
    </div>
  );
}

export default SearchBar;
