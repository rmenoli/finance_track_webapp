const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Helper function to handle API responses
async function handleResponse(response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `HTTP error! status: ${response.status}`
    }));
    throw new Error(error.detail || 'An error occurred');
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

// Transaction API methods
export const transactionsAPI = {
  // Get all transactions with optional filters
  getAll: async (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        query.append(key, value);
      }
    });

    const url = `${API_BASE_URL}/transactions${query.toString() ? '?' + query.toString() : ''}`;
    const response = await fetch(url);
    return handleResponse(response);
  },

  // Get single transaction by ID
  getById: async (id) => {
    const response = await fetch(`${API_BASE_URL}/transactions/${id}`);
    return handleResponse(response);
  },

  // Create new transaction
  create: async (data) => {
    const response = await fetch(`${API_BASE_URL}/transactions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // Update existing transaction
  update: async (id, data) => {
    const response = await fetch(`${API_BASE_URL}/transactions/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // Delete transaction
  delete: async (id) => {
    const response = await fetch(`${API_BASE_URL}/transactions/${id}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};

// Analytics API methods
export const analyticsAPI = {
  // Get portfolio summary
  getPortfolioSummary: async () => {
    const response = await fetch(`${API_BASE_URL}/analytics/portfolio-summary`);
    return handleResponse(response);
  },

  // Get all holdings
  getHoldings: async () => {
    const response = await fetch(`${API_BASE_URL}/analytics/holdings`);
    return handleResponse(response);
  },

  // Get all cost bases
  getAllCostBases: async () => {
    const response = await fetch(`${API_BASE_URL}/analytics/cost-basis`);
    return handleResponse(response);
  },

  // Get cost basis for specific ISIN
  getCostBasis: async (isin) => {
    const response = await fetch(`${API_BASE_URL}/analytics/cost-basis/${isin}`);
    return handleResponse(response);
  },

  // Get realized gains
  getRealizedGains: async (isin = null) => {
    const url = isin
      ? `${API_BASE_URL}/analytics/realized-gains?isin=${isin}`
      : `${API_BASE_URL}/analytics/realized-gains`;
    const response = await fetch(url);
    return handleResponse(response);
  },
};

// Position Values API methods
export const positionValuesAPI = {
  // Create or update position value (UPSERT)
  upsert: async (isin, currentValue) => {
    const response = await fetch(`${API_BASE_URL}/position-values`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        isin: isin,
        current_value: currentValue.toString(), // Send as string for Decimal precision
      }),
    });
    return handleResponse(response);
  },

  // Get all position values
  getAll: async () => {
    const response = await fetch(`${API_BASE_URL}/position-values`);
    return handleResponse(response);
  },

  // Get position value for specific ISIN
  getByIsin: async (isin) => {
    const response = await fetch(`${API_BASE_URL}/position-values/${isin}`);
    return handleResponse(response);
  },

  // Delete position value
  delete: async (isin) => {
    const response = await fetch(`${API_BASE_URL}/position-values/${isin}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};

export default {
  transactions: transactionsAPI,
  analytics: analyticsAPI,
  positionValues: positionValuesAPI,
};
