import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { transactionsAPI } from '../services/api';
import TransactionList from '../components/TransactionList';
import './Transactions.css';

function Transactions() {
  const [transactions, setTransactions] = useState([]);
  const [filters, setFilters] = useState({
    isin: '',
    broker: '',
    transaction_type: '',
    start_date: '',
    end_date: '',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadTransactions();
  }, [filters]);

  const loadTransactions = async () => {
    try {
      setLoading(true);
      const params = {};
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params[key] = value;
      });

      const data = await transactionsAPI.getAll(params);
      setTransactions(data.transactions || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this transaction?')) {
      return;
    }

    try {
      await transactionsAPI.delete(id);
      loadTransactions();
    } catch (err) {
      alert('Error deleting transaction: ' + err.message);
    }
  };

  const handleEdit = (id) => {
    navigate(`/transactions/edit/${id}`);
  };

  return (
    <div className="transactions-page">
      <div className="page-header">
        <h1>Transactions</h1>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/transactions/add')}
        >
          + Add Transaction
        </button>
      </div>

      <div className="filters-card">
        <h3>Filters</h3>
        <div className="filters-grid">
          <input
            type="text"
            name="isin"
            placeholder="ISIN"
            value={filters.isin}
            onChange={handleFilterChange}
            className="input"
          />
          <input
            type="text"
            name="broker"
            placeholder="Broker"
            value={filters.broker}
            onChange={handleFilterChange}
            className="input"
          />
          <select
            name="transaction_type"
            value={filters.transaction_type}
            onChange={handleFilterChange}
            className="input"
          >
            <option value="">All Types</option>
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
          </select>
          <input
            type="date"
            name="start_date"
            placeholder="Start Date"
            value={filters.start_date}
            onChange={handleFilterChange}
            className="input"
          />
          <input
            type="date"
            name="end_date"
            placeholder="End Date"
            value={filters.end_date}
            onChange={handleFilterChange}
            className="input"
          />
          <button
            onClick={() => setFilters({
              isin: '',
              broker: '',
              transaction_type: '',
              start_date: '',
              end_date: '',
            })}
            className="btn btn-secondary"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {loading && <div className="loading">Loading transactions...</div>}
      {error && <div className="error">Error: {error}</div>}
      {!loading && !error && (
        <TransactionList
          transactions={transactions}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}
    </div>
  );
}

export default Transactions;
