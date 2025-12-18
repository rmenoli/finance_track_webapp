import { useState, useEffect } from 'react';
import { positionValuesAPI } from '../services/api';
import './DashboardHoldingsTable.css';

function DashboardHoldingsTable({ holdings }) {
  const [currentValues, setCurrentValues] = useState({});
  const [editingIsin, setEditingIsin] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [savingIsin, setSavingIsin] = useState(null);

  // Load existing position values on mount
  useEffect(() => {
    const loadPositionValues = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await positionValuesAPI.getAll();

        // Convert array to map: { ISIN: value }
        const valuesMap = {};
        response.position_values.forEach(pv => {
          valuesMap[pv.isin] = parseFloat(pv.current_value);
        });

        setCurrentValues(valuesMap);
      } catch (err) {
        console.error('Failed to load position values:', err);
        setError('Failed to load saved values. You can still enter new ones.');
      } finally {
        setLoading(false);
      }
    };

    loadPositionValues();
  }, []);

  const updateCurrentValue = (isin, value) => {
    setCurrentValues(prev => ({ ...prev, [isin]: value }));
  };

  const savePositionValue = async (isin, value) => {
    if (!value || value <= 0) {
      // Don't save invalid values
      return;
    }

    try {
      setSavingIsin(isin);
      await positionValuesAPI.upsert(isin, value);
      // Value already updated in local state, no need to reload
    } catch (err) {
      console.error(`Failed to save position value for ${isin}:`, err);
      // Show error to user but keep local value
      alert(`Failed to save value for ${isin}. Please try again.`);
    } finally {
      setSavingIsin(null);
    }
  };

  const handleBlur = (isin) => {
    setEditingIsin(null);
    const value = currentValues[isin];
    if (value && value > 0) {
      savePositionValue(isin, value);
    }
  };

  const handleKeyDown = (e, isin) => {
    if (e.key === 'Enter') {
      setEditingIsin(null);
      const value = currentValues[isin];
      if (value && value > 0) {
        savePositionValue(isin, value);
      }
    } else if (e.key === 'Escape') {
      setEditingIsin(null);
    }
  };

  const getCurrentPricePerUnit = (holding, currentValue) => {
    if (!currentValue || currentValue === 0) return 0;
    return currentValue / parseFloat(holding.units);
  };

  const calculatePL = (holding, currentValue) => {
    const totalCost = parseFloat(holding.total_cost);
    const absolutePL = currentValue - totalCost;
    const percentagePL = totalCost > 0 ? (absolutePL / totalCost) * 100 : 0;
    return { absolutePL, percentagePL };
  };

  if (!holdings || holdings.length === 0) {
    return <p>No holdings yet.</p>;
  }

  if (loading) {
    return <p>Loading position values...</p>;
  }

  return (
    <div className="table-container">
      {error && (
        <div className="error-message" style={{ color: 'orange', marginBottom: '10px' }}>
          {error}
        </div>
      )}

      <table className="table dashboard-holdings-table">
        <thead>
          <tr>
            <th>ISIN</th>
            <th>Buy In</th>
            <th>Current Position</th>
            <th>P/L</th>
          </tr>
        </thead>
        <tbody>
          {holdings.map(holding => {
            const currentValue = currentValues[holding.isin] || 0;
            const currentPricePerUnit = getCurrentPricePerUnit(holding, currentValue);
            const { absolutePL, percentagePL } = calculatePL(holding, currentValue);
            const isSaving = savingIsin === holding.isin;

            return (
              <tr key={holding.isin}>
                {/* ISIN */}
                <td>
                  <strong>{holding.isin}</strong>
                </td>

                {/* Buy In */}
                <td>
                  <div>€{parseFloat(holding.total_cost).toFixed(2)}</div>
                  <div className="sub-value">
                    €{parseFloat(holding.average_cost_per_unit).toFixed(2)}/unit
                  </div>
                </td>

                {/* Current Position - Editable */}
                <td
                  className="editable-cell"
                  onClick={() => setEditingIsin(holding.isin)}
                  title="Click to enter current value"
                >
                  {editingIsin === holding.isin ? (
                    <input
                      type="number"
                      step="0.01"
                      value={currentValue || ''}
                      onChange={(e) => updateCurrentValue(holding.isin, parseFloat(e.target.value) || 0)}
                      onBlur={() => handleBlur(holding.isin)}
                      onKeyDown={(e) => handleKeyDown(e, holding.isin)}
                      autoFocus
                      placeholder="Enter value"
                    />
                  ) : (
                    <>
                      <div>
                        {currentValue > 0 ? `€${currentValue.toFixed(2)}` : '€0.00 (click to edit)'}
                        {isSaving && <span style={{ marginLeft: '5px', fontSize: '0.9em' }}>💾</span>}
                      </div>
                      {currentValue > 0 && (
                        <div className="sub-value">
                          €{currentPricePerUnit.toFixed(2)}/unit
                        </div>
                      )}
                    </>
                  )}
                </td>

                {/* P/L */}
                <td>
                  {currentValue > 0 ? (
                    <>
                      <div className={absolutePL >= 0 ? 'positive' : 'negative'}>
                        {absolutePL >= 0 ? '+' : ''}€{absolutePL.toFixed(2)}
                      </div>
                      <div className={`sub-value ${percentagePL >= 0 ? 'positive' : 'negative'}`}>
                        {percentagePL >= 0 ? '↑' : '↓'}{Math.abs(percentagePL).toFixed(2)}%
                      </div>
                    </>
                  ) : (
                    <div className="sub-value">-</div>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default DashboardHoldingsTable;
