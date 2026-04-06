const API_BASE_URL = import.meta.env.VITE_API_URL;

 // Fail fast if API URL is not configured
 if (!API_BASE_URL) {
   throw new Error('VITE_API_URL environment variable is not set. Check your .env file.');
 }

const API_KEY = import.meta.env.VITE_API_KEY || '';

function apiFetch(url, options = {}) {
  const headers = { ...options.headers };
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }
  return fetch(url, { ...options, headers });
}

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
    const response = await apiFetch(url);
    return handleResponse(response);
  },

  // Get single transaction by ID
  getById: async (id) => {
    const response = await apiFetch(`${API_BASE_URL}/transactions/${id}`);
    return handleResponse(response);
  },

  // Create new transaction
  create: async (data) => {
    const response = await apiFetch(`${API_BASE_URL}/transactions`, {
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
    const response = await apiFetch(`${API_BASE_URL}/transactions/${id}`, {
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
    const response = await apiFetch(`${API_BASE_URL}/transactions/${id}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },

  // Import transactions from CSV file
  importCSV: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiFetch(`${API_BASE_URL}/transactions/degiro-import-csv-transactions`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse(response);
  },
};

// Analytics API methods
export const analyticsAPI = {
  // Get portfolio summary (includes holdings, total_invested, total_fees)
  getPortfolioSummary: async () => {
    const response = await apiFetch(`${API_BASE_URL}/analytics/portfolio-summary`);
    return handleResponse(response);
  },
};

// Position Values API methods
export const positionValuesAPI = {
  // Create or update position value (UPSERT)
  upsert: async (isin, currentValue) => {
    const response = await apiFetch(`${API_BASE_URL}/position-values`, {
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
    const response = await apiFetch(`${API_BASE_URL}/position-values`);
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
    const response = await apiFetch(url);
    return handleResponse(response);
  },

  // Get single ISIN metadata by ISIN
  getByIsin: async (isin) => {
    const response = await apiFetch(`${API_BASE_URL}/isin-metadata/${isin}`);
    return handleResponse(response);
  },

  // Create new ISIN metadata
  create: async (data) => {
    const response = await apiFetch(`${API_BASE_URL}/isin-metadata`, {
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
    const response = await apiFetch(`${API_BASE_URL}/isin-metadata/${isin}`, {
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
    const response = await apiFetch(`${API_BASE_URL}/isin-metadata/${isin}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },
};

// Other Assets API methods
export const otherAssetsAPI = {
  // Create or update other asset (UPSERT)
  upsert: async (assetType, assetDetail, currency, value) => {
    const response = await apiFetch(`${API_BASE_URL}/other-assets`, {
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
    const response = await apiFetch(url);
    return handleResponse(response);
  },
};

// Settings API methods
export const settingsAPI = {
  // Get exchange rate setting
  getExchangeRate: async () => {
    const response = await apiFetch(`${API_BASE_URL}/settings/exchange-rate`);
    return handleResponse(response);
  },

  // Update exchange rate setting
  updateExchangeRate: async (rate) => {
    const response = await apiFetch(`${API_BASE_URL}/settings/exchange-rate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ exchange_rate: rate }),
    });
    return handleResponse(response);
  },

  // Get expected return investment setting
  getExpectedReturnInvestment: async () => {
    const response = await apiFetch(`${API_BASE_URL}/settings/expected-return-investment`);
    return handleResponse(response);
  },

  // Update expected return investment setting
  updateExpectedReturnInvestment: async (percentage) => {
    const response = await apiFetch(`${API_BASE_URL}/settings/expected-return-investment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ expected_return: percentage }),
    });
    return handleResponse(response);
  },

  // Get expected return CD setting
  getExpectedReturnCD: async () => {
    const response = await apiFetch(`${API_BASE_URL}/settings/expected-return-cd`);
    return handleResponse(response);
  },

  // Update expected return CD setting
  updateExpectedReturnCD: async (percentage) => {
    const response = await apiFetch(`${API_BASE_URL}/settings/expected-return-cd`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ expected_return: percentage }),
    });
    return handleResponse(response);
  },
};

// Snapshots API methods
export const snapshotsAPI = {
  // Create snapshot of current asset state
  create: async () => {
    const response = await apiFetch(`${API_BASE_URL}/snapshots`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}), // Empty body, uses default snapshot_datetime (now)
    });
    return handleResponse(response);
  },

  // Get snapshot summary statistics
  getSummary: async (startDate = null, endDate = null) => {
    let url = `${API_BASE_URL}/snapshots/summary`;
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (params.toString()) url += `?${params.toString()}`;

    const response = await apiFetch(url);
    return handleResponse(response);
  },

  // Delete snapshots by date
  deleteByDate: async (snapshotDate) => {
    const response = await apiFetch(`${API_BASE_URL}/snapshots/${snapshotDate}`, {
      method: 'DELETE',
    });
    return handleResponse(response);
  },

  // Import snapshots from CSV file
  importCSV: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiFetch(`${API_BASE_URL}/snapshots/import-csv`, {
      method: 'POST',
      body: formData,
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
  settings: settingsAPI,
  snapshots: snapshotsAPI,
};
