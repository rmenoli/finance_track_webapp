import { useEffect, useState } from 'react';
import { analyticsAPI } from '../services/api';
import './Analytics.css';

function Analytics() {
  const [costBases, setCostBases] = useState([]);
  const [realizedGains, setRealizedGains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const [costBasesData, gainsData] = await Promise.all([
        analyticsAPI.getAllCostBases(),
        analyticsAPI.getRealizedGains()
      ]);

      setCostBases(costBasesData || []);
      setRealizedGains(gainsData || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading analytics...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="analytics-page">
      <h1>Analytics</h1>

      <div className="analytics-section">
        <h2>Cost Basis by ISIN</h2>
        {costBases.length === 0 ? (
          <p>No cost basis data available.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>ISIN</th>
                  <th>Total Units</th>
                  <th>Average Cost</th>
                  <th>Total Cost</th>
                  <th>Transactions</th>
                </tr>
              </thead>
              <tbody>
                {costBases.map((cb) => (
                  <tr key={cb.isin}>
                    <td><strong>{cb.isin}</strong></td>
                    <td>{parseFloat(cb.total_units).toFixed(4)}</td>
                    <td>€{parseFloat(cb.average_cost_per_unit).toFixed(2)}</td>
                    <td>€{parseFloat(cb.total_cost).toFixed(2)}</td>
                    <td>{cb.transactions_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="analytics-section">
        <h2>Realized Gains</h2>
        {realizedGains.length === 0 ? (
          <p>No realized gains yet.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>ISIN</th>
                  <th>Total Realized Gain/Loss</th>
                  <th>Sell Transactions</th>
                </tr>
              </thead>
              <tbody>
                {realizedGains.map((rg) => (
                  <tr key={rg.isin}>
                    <td><strong>{rg.isin}</strong></td>
                    <td className={parseFloat(rg.total_realized_gain) >= 0 ? 'positive' : 'negative'}>
                      €{parseFloat(rg.total_realized_gain).toFixed(2)}
                    </td>
                    <td>{rg.sell_transactions_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Analytics;
