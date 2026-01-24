/**
 * Custom hooks for API data fetching
 */

import { useState, useEffect, useCallback } from 'react';
import api from '../api/client';

/**
 * Generic hook for API calls with loading and error states
 */
export function useApiCall(apiFunction, dependencies = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await apiFunction();
      setData(result);
    } catch (err) {
      setError(err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Hook for fetching ingredients with search and filters
 */
export function useIngredients(params = {}) {
  const [ingredients, setIngredients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchIngredients = useCallback(async (searchParams = params) => {
    setLoading(true);
    setError(null);

    try {
      const result = await api.getIngredients(searchParams);
      setIngredients(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIngredients(params);
  }, [params.search, params.category]);

  return { ingredients, loading, error, refetch: fetchIngredients };
}

/**
 * Hook for fetching a single ingredient with its details
 */
export function useIngredient(id) {
  const [ingredient, setIngredient] = useState(null);
  const [compounds, setCompounds] = useState([]);
  const [pairings, setPairings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!id) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        const [ingredientData, compoundsData, pairingsData] = await Promise.all([
          api.getIngredient(id),
          api.getIngredientCompounds(id),
          api.getIngredientPairings(id, { limit: 20 }),
        ]);

        setIngredient(ingredientData);
        setCompounds(compoundsData);
        setPairings(pairingsData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  return { ingredient, compounds, pairings, loading, error };
}

/**
 * Hook for comparing two ingredients
 */
export function useComparison(id1, id2) {
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!id1 || !id2) {
      setComparison(null);
      return;
    }

    const fetchComparison = async () => {
      setLoading(true);
      setError(null);

      try {
        const result = await api.compareIngredients(id1, id2);
        setComparison(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, [id1, id2]);

  return { comparison, loading, error };
}

/**
 * Hook for graph exploration data
 */
export function useGraphData(centerId, options = {}) {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchGraph = useCallback(async (newCenterId = centerId) => {
    if (!newCenterId) return;

    setLoading(true);
    setError(null);

    try {
      const result = await api.getGraphData(newCenterId, options);
      setGraphData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [centerId, options.minScore, options.limit]);

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  return { graphData, loading, error, refetch: fetchGraph };
}

/**
 * Hook for categories
 */
export function useCategories() {
  return useApiCall(() => api.getCategories(), []);
}

/**
 * Hook for surprise pairings
 */
export function useSurprisePairings(params = {}) {
  return useApiCall(() => api.getSurprisePairings(params), [params.minScore, params.limit]);
}

/**
 * Hook for database stats
 */
export function useStats() {
  return useApiCall(() => api.getStats(), []);
}

/**
 * Hook for search with debouncing
 */
export function useSearch(initialQuery = '') {
  const [query, setQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  // Debounce the query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Fetch results when debounced query changes
  useEffect(() => {
    if (!debouncedQuery) {
      setResults([]);
      return;
    }

    const fetchResults = async () => {
      setLoading(true);
      try {
        const result = await api.getIngredients({ search: debouncedQuery, limit: 10 });
        setResults(result);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [debouncedQuery]);

  return { query, setQuery, results, loading };
}
