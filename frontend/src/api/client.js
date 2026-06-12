/**
 * API Client for Flavor Pairing API
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Make an API request
 */
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = new Error(`API Error: ${response.status}`);
    error.status = response.status;
    try {
      error.data = await response.json();
    } catch {
      error.data = null;
    }
    throw error;
  }

  return response.json();
}

/**
 * Backend readiness
 *
 * The backend runs on Render's free tier and sleeps after inactivity, so
 * the first request can take 30-60s. waitForBackend() polls /health until
 * it responds, and is shared so the warmup overlay and pages waiting on
 * data reuse the same poll.
 */
let backendReadyPromise = null;

export function waitForBackend({ pollInterval = 2500, timeoutMs = 120000 } = {}) {
  if (!backendReadyPromise) {
    backendReadyPromise = (async () => {
      const start = Date.now();
      for (;;) {
        try {
          await api.getHealth();
          return true;
        } catch {
          if (Date.now() - start >= timeoutMs) {
            throw new Error('Backend did not wake up in time');
          }
        }
        await new Promise((resolve) => setTimeout(resolve, pollInterval));
      }
    })();
    // Allow another attempt after a failed wait
    backendReadyPromise.catch(() => {
      backendReadyPromise = null;
    });
  }
  return backendReadyPromise;
}

export function resetBackendWait() {
  backendReadyPromise = null;
}

/**
 * API methods
 */
export const api = {
  // Ingredients
  getIngredients: (params = {}) => {
    const searchParams = new URLSearchParams();
    if (params.search) searchParams.set('search', params.search);
    if (params.category) searchParams.set('category', params.category);
    if (params.skip) searchParams.set('skip', params.skip);
    if (params.limit) searchParams.set('limit', params.limit);

    const query = searchParams.toString();
    return apiRequest(`/ingredients${query ? `?${query}` : ''}`);
  },

  getIngredient: (id) => {
    return apiRequest(`/ingredients/${id}`);
  },

  getIngredientCompounds: (id) => {
    return apiRequest(`/ingredients/${id}/compounds`);
  },

  getIngredientPairings: (id, params = {}) => {
    const searchParams = new URLSearchParams();
    if (params.minScore) searchParams.set('min_score', params.minScore);
    if (params.limit) searchParams.set('limit', params.limit);

    const query = searchParams.toString();
    return apiRequest(`/ingredients/${id}/pairings${query ? `?${query}` : ''}`);
  },

  compareIngredients: (id1, id2) => {
    return apiRequest(`/ingredients/${id1}/compare/${id2}`);
  },

  // Compounds
  getCompounds: (params = {}) => {
    const searchParams = new URLSearchParams();
    if (params.skip) searchParams.set('skip', params.skip);
    if (params.limit) searchParams.set('limit', params.limit);

    const query = searchParams.toString();
    return apiRequest(`/compounds${query ? `?${query}` : ''}`);
  },

  getCompound: (id) => {
    return apiRequest(`/compounds/${id}`);
  },

  getCompoundIngredients: (id, params = {}) => {
    const searchParams = new URLSearchParams();
    if (params.limit) searchParams.set('limit', params.limit);

    const query = searchParams.toString();
    return apiRequest(`/compounds/${id}/ingredients${query ? `?${query}` : ''}`);
  },

  // Explore
  getCategories: () => {
    return apiRequest('/explore/categories');
  },

  getTasteProfiles: () => {
    return apiRequest('/explore/taste-profiles');
  },

  getSurprisePairings: (params = {}) => {
    const searchParams = new URLSearchParams();
    if (params.minScore) searchParams.set('min_score', params.minScore);
    if (params.limit) searchParams.set('limit', params.limit);

    const query = searchParams.toString();
    return apiRequest(`/explore/surprise${query ? `?${query}` : ''}`);
  },

  getGraphData: (center, params = {}) => {
    const searchParams = new URLSearchParams();
    searchParams.set('center', center);
    if (params.minScore) searchParams.set('min_score', params.minScore);
    if (params.limit) searchParams.set('limit', params.limit);

    return apiRequest(`/explore/graph?${searchParams.toString()}`);
  },

  getStats: () => {
    return apiRequest('/explore/stats');
  },

  getRandomIngredient: (category = null) => {
    const query = category ? `?category=${category}` : '';
    return apiRequest(`/explore/random${query}`);
  },

  // Health
  getHealth: () => {
    return apiRequest('/health');
  },
};

export default api;
