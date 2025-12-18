import { useState } from 'react';
import './DashboardHoldingsTable.css';

function DashboardHoldingsTable({ holdings }) {
  const [currentValues, setCurrentValues] = useState({});
  const [editingIsin, setEditingIsin] = useState(null);

  const updateCurrentValue = (isin, value) => {
    setCurrentValues(prev => ({ ...prev, [isin]: value }));
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

  return (
    <div className="table-container">
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
                      onBlur={() => setEditingIsin(null)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') setEditingIsin(null);
                        if (e.key === 'Escape') {
                          setEditingIsin(null);
                        }
                      }}
                      autoFocus
                      placeholder="Enter value"
                    />
                  ) : (
                    <>
                      <div>
                        {currentValue > 0 ? `€${currentValue.toFixed(2)}` : '€0.00 (click to edit)'}
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
