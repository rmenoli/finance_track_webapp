import { useState, useEffect } from 'react';
import { otherAssetsAPI, settingsAPI, snapshotsAPI } from '../services/api';
import OtherAssetsTable from '../components/OtherAssetsTable';
import OtherAssetsDistributionChart from '../components/OtherAssetsDistributionChart';
import './OtherAssets.css';

function OtherAssets() {
  const [assets, setAssets] = useState([]);
  const [exchangeRate, setExchangeRate] = useState(25.00);
  const [expectedReturnInvestment, setExpectedReturnInvestment] = useState(7.00);
  const [expectedReturnCD, setExpectedReturnCD] = useState(4.00);
  const [monthlyReturnInvestment, setMonthlyReturnInvestment] = useState(0);
  const [monthlyReturnCD, setMonthlyReturnCD] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSavingExchangeRate, setIsSavingExchangeRate] = useState(false);
  const [isSavingReturnInvestment, setIsSavingReturnInvestment] = useState(false);
  const [isSavingReturnCD, setIsSavingReturnCD] = useState(false);
  const [isCreatingSnapshot, setIsCreatingSnapshot] = useState(false);
  const [snapshotSuccess, setSnapshotSuccess] = useState(false);

  const loadAssets = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await otherAssetsAPI.getAll(true); // Include investments
      setAssets(response.other_assets || []);

      // Extract monthly returns from response
      setMonthlyReturnInvestment(parseFloat(response.monthly_expected_return_investment || 0));
      setMonthlyReturnCD(parseFloat(response.monthly_expected_return_cd || 0));
    } catch (err) {
      console.error('Failed to load other assets:', err);
      setError('Failed to load assets. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load all settings from backend on mount
    const loadSettings = async () => {
      try {
        // Load exchange rate
        const exchangeRateData = await settingsAPI.getExchangeRate();
        setExchangeRate(parseFloat(exchangeRateData.exchange_rate));

        // Load expected return investment
        const returnInvestmentData = await settingsAPI.getExpectedReturnInvestment();
        setExpectedReturnInvestment(parseFloat(returnInvestmentData.expected_return));

        // Load expected return CD
        const returnCDData = await settingsAPI.getExpectedReturnCD();
        setExpectedReturnCD(parseFloat(returnCDData.expected_return));
      } catch (err) {
        console.error('Failed to load settings:', err);
        // Use defaults if backend fails
        setExchangeRate(25.00);
        setExpectedReturnInvestment(7.00);
        setExpectedReturnCD(4.00);
      }
    };

    loadSettings();
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

  // ---------- Expected Return Investment Handlers ----------

  // Called on every keystroke - updates local state only
  const handleReturnInvestmentInputChange = (e) => {
    const value = e.target.value;

    // Allow empty string (user is clearing the field)
    if (value === '') {
      setExpectedReturnInvestment('');
      return;
    }

    // Update local state immediately for responsive UI
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setExpectedReturnInvestment(numValue);
    }
  };

  // Called on blur or Enter - saves to backend
  const saveReturnInvestment = async () => {
    const numValue = parseFloat(expectedReturnInvestment);

    // Validate before saving
    if (isNaN(numValue) || numValue < 0 || numValue > 100) {
      setError('Expected return must be between 0% and 100%');
      return;
    }

    try {
      setIsSavingReturnInvestment(true);
      setError(null);

      await settingsAPI.updateExpectedReturnInvestment(numValue);

      // Note: No need to reload assets - this is reference only
    } catch (err) {
      console.error('Failed to update expected return investment:', err);
      setError('Failed to save expected return. Please try again.');
    } finally {
      setIsSavingReturnInvestment(false);
    }
  };

  // Handle Enter key press
  const handleReturnInvestmentKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.target.blur(); // Trigger onBlur to save
    }
  };

  // ---------- Expected Return CD Handlers ----------

  // Called on every keystroke - updates local state only
  const handleReturnCDInputChange = (e) => {
    const value = e.target.value;

    // Allow empty string (user is clearing the field)
    if (value === '') {
      setExpectedReturnCD('');
      return;
    }

    // Update local state immediately for responsive UI
    const numValue = parseFloat(value);
    if (!isNaN(numValue)) {
      setExpectedReturnCD(numValue);
    }
  };

  // Called on blur or Enter - saves to backend
  const saveReturnCD = async () => {
    const numValue = parseFloat(expectedReturnCD);

    // Validate before saving
    if (isNaN(numValue) || numValue < 0 || numValue > 100) {
      setError('Expected return must be between 0% and 100%');
      return;
    }

    try {
      setIsSavingReturnCD(true);
      setError(null);

      await settingsAPI.updateExpectedReturnCD(numValue);

      // Note: No need to reload assets - this is reference only
    } catch (err) {
      console.error('Failed to update expected return CD:', err);
      setError('Failed to save expected return. Please try again.');
    } finally {
      setIsSavingReturnCD(false);
    }
  };

  // Handle Enter key press
  const handleReturnCDKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.target.blur(); // Trigger onBlur to save
    }
  };

  const handleDataChange = () => {
    // Reload assets when data changes
    loadAssets();
  };

  const handleCreateSnapshot = async () => {
    try {
      setIsCreatingSnapshot(true);
      setError(null);
      setSnapshotSuccess(false);

      await snapshotsAPI.create();

      // Show success message
      setSnapshotSuccess(true);
      // Hide success message after 3 seconds
      setTimeout(() => setSnapshotSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to create snapshot:', err);
      setError('Failed to create snapshot. Please try again.');
    } finally {
      setIsCreatingSnapshot(false);
    }
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
      <div className="page-header">
        <h1>Other Assets</h1>
        <button
          onClick={handleCreateSnapshot}
          disabled={isCreatingSnapshot}
          className="snapshot-button"
        >
          {isCreatingSnapshot ? 'Creating Snapshot...' : 'Create Snapshot'}
        </button>
      </div>

      {snapshotSuccess && (
        <div className="success-message">Snapshot created successfully!</div>
      )}

      <div className="settings-section">
        <h2 className="settings-title">Settings</h2>

        <div className="settings-grid">
          {/* Exchange Rate Setting */}
          <div className="setting-item">
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
                className="setting-input"
              />
              CZK)
              {isSavingExchangeRate && <span className="saving-indicator">💾 Saving...</span>}
            </label>
            <p className="helper-text">
              Current rate: 1 EUR = {exchangeRate || '0.00'} CZK
              {!isSavingExchangeRate && exchangeRate && ' (Press Enter or click outside to save)'}
            </p>
          </div>

          {/* Expected Return Investment Setting */}
          <div className="setting-item">
            <label htmlFor="returnInvestment">
              Expected Return - Investment:
              <input
                id="returnInvestment"
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={expectedReturnInvestment}
                onChange={handleReturnInvestmentInputChange}
                onBlur={saveReturnInvestment}
                onKeyDown={handleReturnInvestmentKeyDown}
                disabled={isSavingReturnInvestment}
                className="setting-input"
              />
              %
              {isSavingReturnInvestment && <span className="saving-indicator">💾 Saving...</span>}
            </label>
            <p className="helper-text">
              Expected annual return: {expectedReturnInvestment || '0.00'}%
              {!isSavingReturnInvestment && expectedReturnInvestment !== '' && ' (Press Enter or click outside to save)'}
            </p>
          </div>

          {/* Expected Return CD Setting */}
          <div className="setting-item">
            <label htmlFor="returnCD">
              Expected Return - CD:
              <input
                id="returnCD"
                type="number"
                step="0.01"
                min="0"
                max="100"
                value={expectedReturnCD}
                onChange={handleReturnCDInputChange}
                onBlur={saveReturnCD}
                onKeyDown={handleReturnCDKeyDown}
                disabled={isSavingReturnCD}
                className="setting-input"
              />
              %
              {isSavingReturnCD && <span className="saving-indicator">💾 Saving...</span>}
            </label>
            <p className="helper-text">
              Expected annual return: {expectedReturnCD || '0.00'}%
              {!isSavingReturnCD && expectedReturnCD !== '' && ' (Press Enter or click outside to save)'}
            </p>
          </div>
        </div>
      </div>

      <OtherAssetsTable
        assets={assets}
        exchangeRate={exchangeRate || 25.00}
        onDataChange={handleDataChange}
      />

      {/* Monthly Expected Returns Display */}
      <div className="monthly-returns-section">
        <h2>Monthly Expected Returns</h2>
        <div className="returns-grid">
          <div className="return-card">
            <h3>Investment Returns</h3>
            <p className="return-value">€{monthlyReturnInvestment.toFixed(2)}</p>
            <p className="return-description">per month from investments</p>
          </div>

          <div className="return-card">
            <h3>CD Account Returns</h3>
            <p className="return-value">€{monthlyReturnCD.toFixed(2)}</p>
            <p className="return-description">per month from CD accounts</p>
          </div>

          <div className="return-card total-return">
            <h3>Total Monthly Returns</h3>
            <p className="return-value">€{(monthlyReturnInvestment + monthlyReturnCD).toFixed(2)}</p>
            <p className="return-description">total expected per month</p>
          </div>
        </div>
      </div>

      <OtherAssetsDistributionChart
        assets={assets}
        exchangeRate={exchangeRate || 25.00}
      />
    </div>
  );
}

export default OtherAssets;
