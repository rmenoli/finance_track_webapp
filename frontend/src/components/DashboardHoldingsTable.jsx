import { useState } from 'react';
import { positionValuesAPI } from '../services/api';
import './DashboardHoldingsTable.css';
import FormattedNumber from './FormattedNumber';
import HoldingsDistributionChart from './HoldingsDistributionChart';

function DashboardHoldingsTable({ holdings, onPositionValueChange, isinNames = {} }) {
  const [editingIsin, setEditingIsin] = useState(null);
  const [editingValue, setEditingValue] = useState(null);
  const [error, setError] = useState(null);
  const [savingIsin, setSavingIsin] = useState(null);

  const startEditing = (holding) => {
    setEditingIsin(holding.isin);
    setEditingValue(holding.current_value || '');
  };

  const savePositionValue = async (isin, value) => {
    const numValue = parseFloat(value);
    if (!numValue || numValue <= 0) {
      setError('Please enter a valid position value greater than 0');
      setEditingIsin(null);
      setEditingValue(null);
      return;
    }

    try {
      setSavingIsin(isin);
      setError(null);

      // Upsert position value
      await positionValuesAPI.upsert(isin, numValue);

      // Notify parent to refresh data (will fetch updated P/L from backend)
      if (onPositionValueChange) {
        onPositionValueChange();
      }

      setEditingIsin(null);
      setEditingValue(null);
    } catch (err) {
      console.error('Failed to save position value:', err);
      setError(`Failed to save value for ${isin}. Please try again.`);
      setSavingIsin(null);
    }
  };

  const handleBlur = (isin) => {
    if (editingValue !== null && editingValue !== '') {
      savePositionValue(isin, editingValue);
    } else {
      setEditingIsin(null);
      setEditingValue(null);
    }
  };

  const handleKeyDown = (e, isin) => {
    if (e.key === 'Enter') {
      if (editingValue !== null && editingValue !== '') {
        savePositionValue(isin, editingValue);
      } else {
        setEditingIsin(null);
        setEditingValue(null);
      }
    } else if (e.key === 'Escape') {
      setEditingIsin(null);
      setEditingValue(null);
    }
  };

  if (!holdings || holdings.length === 0) {
    return <p>No holdings yet.</p>;
  }

  // Create currentValues map from holdings for the chart
  const currentValues = holdings.reduce((map, holding) => {
    if (holding.current_value) {
      map[holding.isin] = parseFloat(holding.current_value);
    }
    return map;
  }, {});

  return (
    <>
      {/* Holdings Distribution Chart */}
      <HoldingsDistributionChart
        holdings={holdings}
        currentValues={currentValues}
        isinNames={isinNames}
      />

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
            <th>Total Fees</th>
            <th>P/L (incl. fees)</th>
          </tr>
        </thead>
        <tbody>
          {holdings.map(holding => {
            const currentValue = holding.current_value ? parseFloat(holding.current_value) : 0;
            const currentPricePerUnit = currentValue > 0 && holding.total_units > 0
              ? currentValue / parseFloat(holding.total_units)
              : 0;
            const isSaving = savingIsin === holding.isin;
            const isEditing = editingIsin === holding.isin;

            return (
              <tr key={holding.isin}>
                {/* ISIN */}
                <td>
                  {isinNames[holding.isin] && (
                    <div style={{ fontWeight: 'bold', fontSize: '0.9em', color: '#333', marginBottom: '2px' }}>
                      {isinNames[holding.isin]}
                    </div>
                  )}
                  <span style={{ fontStyle: 'italic' }}>{holding.isin}</span>
                </td>

                {/* Buy In */}
                <td>
                  <div>
                    <FormattedNumber
                      value={parseFloat(holding.total_cost_without_fees) - parseFloat(holding.total_gains_without_fees)}
                      currency={true}
                    />
                  </div>
                  {holding.total_units > 0 && (
                    <div className="sub-value">
                      <FormattedNumber
                        value={(parseFloat(holding.total_cost_without_fees) - parseFloat(holding.total_gains_without_fees)) / parseFloat(holding.total_units)}
                        currency={true}
                      />
                      /unit
                    </div>
                  )}
                </td>

                {/* Current Position - Editable */}
                <td
                  className="editable-cell"
                  onClick={() => !isEditing && startEditing(holding)}
                  title="Click to enter current value"
                >
                  {isEditing ? (
                    <input
                      type="number"
                      step="0.01"
                      value={editingValue}
                      onChange={(e) => setEditingValue(e.target.value)}
                      onBlur={() => handleBlur(holding.isin)}
                      onKeyDown={(e) => handleKeyDown(e, holding.isin)}
                      autoFocus
                      placeholder="Enter value"
                    />
                  ) : (
                    <>
                      <div>
                        {currentValue > 0 ? (
                          <FormattedNumber value={currentValue} currency={true} />
                        ) : (
                          '€0.00 (click to edit)'
                        )}
                        {isSaving && <span style={{ marginLeft: '5px', fontSize: '0.9em' }}>💾</span>}
                      </div>
                      {currentValue > 0 && (
                        <div className="sub-value">
                          <FormattedNumber value={currentPricePerUnit} currency={true} />
                          /unit
                        </div>
                      )}
                    </>
                  )}
                </td>

                {/* P/L (without fees) */}
                <td>
                  {holding.absolute_pl_without_fees !== null && holding.absolute_pl_without_fees !== undefined ? (
                    <>
                      <div className={parseFloat(holding.absolute_pl_without_fees) >= 0 ? 'positive' : 'negative'}>
                        {parseFloat(holding.absolute_pl_without_fees) >= 0 ? '+' : ''}
                        <FormattedNumber value={holding.absolute_pl_without_fees} currency={true} />
                      </div>
                      <div className={`sub-value ${parseFloat(holding.percentage_pl_without_fees) >= 0 ? 'positive' : 'negative'}`}>
                        {parseFloat(holding.percentage_pl_without_fees) >= 0 ? '↑' : '↓'}
                        <FormattedNumber value={Math.abs(parseFloat(holding.percentage_pl_without_fees))} currency={false} />
                        %
                      </div>
                    </>
                  ) : (
                    <div className="sub-value">N/A</div>
                  )}
                </td>

                {/* Total Fees */}
                <td>
                  <div>
                    <FormattedNumber value={holding.total_fees} currency={true} />
                  </div>
                </td>

                {/* P/L (including fees) */}
                <td>
                  {holding.absolute_pl_with_fees !== null && holding.absolute_pl_with_fees !== undefined ? (
                    <>
                      <div className={parseFloat(holding.absolute_pl_with_fees) >= 0 ? 'positive' : 'negative'}>
                        {parseFloat(holding.absolute_pl_with_fees) >= 0 ? '+' : ''}
                        <FormattedNumber value={holding.absolute_pl_with_fees} currency={true} />
                      </div>
                      <div className={`sub-value ${parseFloat(holding.percentage_pl_with_fees) >= 0 ? 'positive' : 'negative'}`}>
                        {parseFloat(holding.percentage_pl_with_fees) >= 0 ? '↑' : '↓'}
                        <FormattedNumber value={Math.abs(parseFloat(holding.percentage_pl_with_fees))} currency={false} />
                        %
                      </div>
                    </>
                  ) : (
                    <div className="sub-value">N/A</div>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
    </>
  );
}

export default DashboardHoldingsTable;
