import { useEffect, useState, useCallback } from 'react';
import { analyticsAPI, transactionsAPI } from '../services/api';
import PortfolioSummary from '../components/PortfolioSummary';
import './InvestmentDashboard.css';

function InvestmentDashboard() {
  const [summary, setSummary] = useState(null);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [summaryData, transactionsData] = await Promise.all([
        analyticsAPI.getPortfolioSummary(),
        transactionsAPI.getAll({ limit: 5, sort_by: 'date', sort_order: 'desc' })
      ]);

      setSummary(summaryData);
      setRecentTransactions(transactionsData.transactions || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="dashboard">
      <h1>Investment Dashboard</h1>

      {summary && <PortfolioSummary data={summary} onDataChange={loadDashboardData} />}

      <div className="dashboard-section">
        <h2>Recent Transactions</h2>
        {recentTransactions.length === 0 ? (
          <p>No transactions yet. <a href="/transactions/add">Add your first transaction</a></p>
        ) : (
          <div className="transactions-preview">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>ISIN</th>
                  <th>Type</th>
                  <th>Units</th>
                  <th>Price</th>
                  <th>Total</th>
                </tr>
              </thead>
              <tbody>
                {recentTransactions.map((txn) => (
                  <tr key={txn.id}>
                    <td>{new Date(txn.date).toLocaleDateString()}</td>
                    <td>{txn.isin}</td>
                    <td>
                      <span className={`badge badge-${txn.transaction_type.toLowerCase()}`}>
                        {txn.transaction_type}
                      </span>
                    </td>
                    <td>{parseFloat(txn.units).toFixed(4)}</td>
                    <td>€{parseFloat(txn.price_per_unit).toFixed(2)}</td>
                    <td>€{(parseFloat(txn.units) * parseFloat(txn.price_per_unit)).toFixed(2)}</td>
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

export default InvestmentDashboard;
