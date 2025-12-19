import { useState, useEffect } from 'react';
import { otherAssetsAPI } from '../services/api';
import OtherAssetsTable from '../components/OtherAssetsTable';
import OtherAssetsDistributionChart from '../components/OtherAssetsDistributionChart';
import './OtherAssets.css';

function OtherAssets() {
  const [assets, setAssets] = useState([]);
  const [exchangeRate, setExchangeRate] = useState(() => {
    // Load exchange rate from localStorage or default to 25.00
    const saved = localStorage.getItem('czkEurExchangeRate');
    return saved ? parseFloat(saved) : 25.00;
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
    loadAssets();
  }, []);

  const handleExchangeRateChange = (e) => {
    const value = e.target.value;
    const numValue = parseFloat(value);

    if (!isNaN(numValue) && numValue > 0) {
      setExchangeRate(numValue);
      localStorage.setItem('czkEurExchangeRate', numValue.toString());
    } else if (value === '') {
      setExchangeRate('');
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
            onChange={handleExchangeRateChange}
            className="exchange-rate-input"
          />
          CZK)
        </label>
        <p className="helper-text">
          Current rate: 1 EUR = {exchangeRate || '0.00'} CZK
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
