import { useEffect, useState, useCallback } from 'react';
import { analyticsAPI, transactionsAPI, isinMetadataAPI } from '../services/api';
import PortfolioSummary from '../components/PortfolioSummary';
import FormattedNumber from '../components/FormattedNumber';
import './InvestmentDashboard.css';

function InvestmentDashboard() {
  const [summary, setSummary] = useState(null);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [isinNames, setIsinNames] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [summaryData, transactionsData, isinMetadataData] = await Promise.all([
        analyticsAPI.getPortfolioSummary(),
        transactionsAPI.getAll({ limit: 5, sort_by: 'date', sort_order: 'desc' }),
        isinMetadataAPI.getAll()
      ]);

      setSummary(summaryData);
      setRecentTransactions(transactionsData.transactions || []);

      // Convert ISIN metadata array to map: { ISIN: name }
      const namesMap = {};
      isinMetadataData.items.forEach(metadata => {
        namesMap[metadata.isin] = metadata.name;
      });
      setIsinNames(namesMap);

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

      {summary && <PortfolioSummary data={summary} onDataChange={loadDashboardData} isinNames={isinNames} />}

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
                    <td>
                      <FormattedNumber value={txn.units} currency={false} decimals={4} />
                    </td>
                    <td>
                      <FormattedNumber value={txn.price_per_unit} currency={true} />
                    </td>
                    <td>
                      <FormattedNumber value={txn.total_without_fees} currency={true} />
                    </td>
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
