import { useEffect, useState, useRef } from 'react';
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
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

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

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      setImportResult({
        total_rows: 0,
        successful: 0,
        failed: 1,
        results: [],
        errors: [{ row: 0, errors: ['Please select a CSV file'] }],
        success_rate: 0,
      });
      e.target.value = '';
      return;
    }

    try {
      setImporting(true);
      setImportResult(null);

      const result = await transactionsAPI.importCSV(file);
      setImportResult(result);

      // Reload transactions if any were successfully imported
      if (result.successful > 0) {
        loadTransactions();
      }
    } catch (err) {
      setImportResult({
        total_rows: 0,
        successful: 0,
        failed: 1,
        results: [],
        errors: [{ row: 0, errors: [err.message || 'Import failed'] }],
        success_rate: 0,
      });
    } finally {
      setImporting(false);
      // Reset file input
      e.target.value = '';
    }
  };

  const handleDismissImportResult = () => {
    setImportResult(null);
  };

  return (
    <div className="transactions-page">
      <div className="page-header">
        <h1>Transactions</h1>
        <div className="button-group">
          <button
            className="btn btn-primary"
            onClick={() => navigate('/transactions/add')}
          >
            + Add Transaction
          </button>
          <button
            className="btn btn-secondary"
            onClick={handleImportClick}
            disabled={importing}
          >
            {importing ? 'Importing...' : '📁 Import DEGIRO CSV'}
          </button>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".csv"
        style={{ display: 'none' }}
      />

      {/* Import Results */}
      {importResult && (
        <div className={`import-results ${
          importResult.failed === 0 ? 'success' :
          importResult.successful > 0 ? 'partial' : 'error'
        }`}>
          <h3>Import Results</h3>
          <p className="import-summary">
            {importResult.failed === 0 ? '✓' : '⚠️'}
            {' '}Successfully imported {importResult.successful} of {importResult.total_rows} transactions
            ({importResult.success_rate}%)
          </p>

          {importResult.errors.length > 0 && (
            <div className="import-errors">
              <h4>Errors:</h4>
              <ul className="import-error-list">
                {importResult.errors.map((error, index) => (
                  <li key={index} className="import-error-item">
                    Row {error.row}
                    {error.isin && ` (${error.isin})`}
                    {error.date && `, ${error.date}`}
                    : {error.errors.join(', ')}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button
            className="btn btn-secondary"
            onClick={handleDismissImportResult}
          >
            Dismiss
          </button>
        </div>
      )}

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
