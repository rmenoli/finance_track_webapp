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
  // Get portfolio summary (includes holdings, total_invested, total_fees)
  getPortfolioSummary: async () => {
    const response = await fetch(`${API_BASE_URL}/analytics/portfolio-summary`);
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
};

// ISIN Metadata API methods
export const isinMetadataAPI = {
  // Get all ISIN metadata with optional type filter
  getAll: async (params = {}) => {
    const query = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        query.append(key, value);
      }
    });

    const url = `${API_BASE_URL}/isin-metadata${query.toString() ? '?' + query.toString() : ''}`;
    const response = await fetch(url);
    return handleResponse(response);
  },

  // Get single ISIN metadata by ISIN
  getByIsin: async (isin) => {
    const response = await fetch(`${API_BASE_URL}/isin-metadata/${isin}`);
    return handleResponse(response);
  },

  // Create new ISIN metadata
  create: async (data) => {
    const response = await fetch(`${API_BASE_URL}/isin-metadata`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // Update existing ISIN metadata
  update: async (isin, data) => {
    const response = await fetch(`${API_BASE_URL}/isin-metadata/${isin}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // Delete ISIN metadata
  delete: async (isin) => {
    const response = await fetch(`${API_BASE_URL}/isin-metadata/${isin}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};

// Other Assets API methods
export const otherAssetsAPI = {
  // Create or update other asset (UPSERT)
  upsert: async (assetType, assetDetail, currency, value) => {
    const response = await fetch(`${API_BASE_URL}/other-assets`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        asset_type: assetType,
        asset_detail: assetDetail,
        currency: currency,
        value: value.toString(), // Send as string for Decimal precision
      }),
    });
    return handleResponse(response);
  },

  // Get all other assets with optional investments row
  getAll: async (includeInvestments = true) => {
    const url = `${API_BASE_URL}/other-assets?include_investments=${includeInvestments}`;
    const response = await fetch(url);
    return handleResponse(response);
  },

  // Get single other asset by type and optional detail
  get: async (assetType, assetDetail = null) => {
    const query = assetDetail ? `?asset_detail=${encodeURIComponent(assetDetail)}` : '';
    const response = await fetch(`${API_BASE_URL}/other-assets/${assetType}${query}`);
    return handleResponse(response);
  },

  // Delete other asset
  delete: async (assetType, assetDetail = null) => {
    const query = assetDetail ? `?asset_detail=${encodeURIComponent(assetDetail)}` : '';
    const response = await fetch(`${API_BASE_URL}/other-assets/${assetType}${query}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};

export default {
  transactions: transactionsAPI,
  analytics: analyticsAPI,
  positionValues: positionValuesAPI,
  isinMetadata: isinMetadataAPI,
  otherAssets: otherAssetsAPI,
};
