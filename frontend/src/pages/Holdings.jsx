import { useEffect, useState } from 'react';
import { analyticsAPI } from '../services/api';
import HoldingsTable from '../components/HoldingsTable';
import './Holdings.css';

function Holdings() {
  const [holdings, setHoldings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadHoldings();
  }, []);

  const loadHoldings = async () => {
    try {
      setLoading(true);
      const data = await analyticsAPI.getHoldings();
      setHoldings(data || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading holdings...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="holdings-page">
      <h1>Current Holdings</h1>

      {holdings.length === 0 ? (
        <div className="empty-state">
          <p>No holdings found. <a href="/transactions/add">Add your first transaction</a></p>
        </div>
      ) : (
        <HoldingsTable holdings={holdings} />
      )}
    </div>
  );
}

export default Holdings;
