import { useState, useEffect } from 'react';
import { otherAssetsAPI, settingsAPI } from '../services/api';
import OtherAssetsTable from '../components/OtherAssetsTable';
import OtherAssetsDistributionChart from '../components/OtherAssetsDistributionChart';
import './OtherAssets.css';

function OtherAssets() {
  const [assets, setAssets] = useState([]);
  const [exchangeRate, setExchangeRate] = useState(25.00);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSavingExchangeRate, setIsSavingExchangeRate] = useState(false);

  const loadAssets = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await otherAssetsAPI.getAll(true); // Include investments
      setAssets(response.other_assets || []);
    } catch (err) {
      console.error('Failed to load other assets:', err);
      setError('Failed to load assets. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load exchange rate from backend on mount
    const loadExchangeRate = async () => {
      try {
        const data = await settingsAPI.getExchangeRate();
        setExchangeRate(parseFloat(data.exchange_rate));
      } catch (err) {
        console.error('Failed to load exchange rate:', err);
        // Use default if backend fails
        setExchangeRate(25.00);
      }
    };

    loadExchangeRate();
    loadAssets();
  }, []);

  // Called on every keystroke - updates local state only
  const handleExchangeRateInputChange = (e) => {
    const value = e.target.value;

    // Allow empty string (user is clearing the field)
    if (value === '') {
      setExchangeRate('');
      return;
    }

    // Update local state immediately for responsive UI
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setExchangeRate(numValue);
    }
  };

  // Called on blur or Enter - saves to backend
  const saveExchangeRate = async () => {
    const numValue = parseFloat(exchangeRate);

    // Validate before saving
    if (isNaN(numValue) || numValue <= 0) {
      setError('Please enter a valid exchange rate (must be > 0)');
      return;
    }

    try {
      setIsSavingExchangeRate(true);
      setError(null);

      await settingsAPI.updateExchangeRate(numValue);

      // Reload assets to get new EUR conversions
      await loadAssets();
    } catch (err) {
      console.error('Failed to update exchange rate:', err);
      setError('Failed to save exchange rate. Please try again.');
    } finally {
      setIsSavingExchangeRate(false);
    }
  };

  // Handle Enter key press
  const handleExchangeRateKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.target.blur(); // Trigger onBlur to save
    }
  };

  const handleDataChange = () => {
    // Reload assets when data changes
    loadAssets();
  };

  if (loading) {
    return (
      <div className="other-assets-page">
        <h1>Other Assets</h1>
        <p>Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="other-assets-page">
        <h1>Other Assets</h1>
        <div className="error-message">{error}</div>
        <button onClick={loadAssets}>Retry</button>
      </div>
    );
  }

  return (
    <div className="other-assets-page">
      <h1>Other Assets</h1>

      <div className="exchange-rate-section">
        <label htmlFor="exchangeRate">
          Exchange Rate (1 EUR =
          <input
            id="exchangeRate"
            type="number"
            step="0.01"
            min="0.01"
            value={exchangeRate}
            onChange={handleExchangeRateInputChange}
            onBlur={saveExchangeRate}
            onKeyDown={handleExchangeRateKeyDown}
            disabled={isSavingExchangeRate}
            className="exchange-rate-input"
          />
          CZK)
          {isSavingExchangeRate && <span className="saving-indicator">💾 Saving...</span>}
        </label>
        <p className="helper-text">
          Current rate: 1 EUR = {exchangeRate || '0.00'} CZK
          {!isSavingExchangeRate && exchangeRate && ' (Press Enter or click outside to save)'}
        </p>
      </div>

      <OtherAssetsTable
        assets={assets}
        exchangeRate={exchangeRate || 25.00}
        onDataChange={handleDataChange}
      />

      <OtherAssetsDistributionChart
        assets={assets}
        exchangeRate={exchangeRate || 25.00}
      />
    </div>
  );
}

export default OtherAssets;
