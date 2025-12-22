import { useEffect, useState } from 'react';
import { snapshotsAPI } from '../services/api';
import SnapshotsTable from '../components/SnapshotsTable';
import SnapshotValueChart from '../components/SnapshotValueChart';
import './Snapshots.css';

function Snapshots() {
  // State management
  const [snapshots, setSnapshots] = useState([]);
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
  });
  const [activeQuickFilter, setActiveQuickFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load snapshots when filters change
  useEffect(() => {
    loadSnapshots();
  }, [filters]);

  const loadSnapshots = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await snapshotsAPI.getSummary(
        filters.start_date || null,
        filters.end_date || null
      );
      setSnapshots(data.summaries || []);
    } catch (err) {
      console.error('Failed to load snapshots:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({ ...prev, [name]: value }));
    setActiveQuickFilter('');
  };

  const handleClearFilters = () => {
    setFilters({ start_date: '', end_date: '' });
    setActiveQuickFilter('ALL');
  };

  const handleQuickFilterChange = (filterType) => {
    setActiveQuickFilter(filterType);

    if (filterType === 'ALL') {
      setFilters({ start_date: '', end_date: '' });
      return;
    }

    const end = new Date();
    const start = new Date();

    switch(filterType) {
      case 'YTD':
        // Year to date - from January 1st of current year
        start.setMonth(0); // January
        start.setDate(1);  // 1st day
        break;
      case '1Y':
        start.setFullYear(end.getFullYear() - 1);
        break;
      case '2Y':
        start.setFullYear(end.getFullYear() - 2);
        break;
      case '3Y':
        start.setFullYear(end.getFullYear() - 3);
        break;
    }

    setFilters({
      start_date: start.toISOString().split('T')[0],
      end_date: end.toISOString().split('T')[0],
    });
  };

  return (
    <div className="snapshots-page">
      <div className="page-header">
        <h1>Asset Snapshots</h1>
      </div>

      <div className="filters-card">
        <h3>Filters</h3>
        <div className="filters-grid">
          <div>
            <label>Start Date</label>
            <input
              type="date"
              name="start_date"
              value={filters.start_date}
              onChange={handleFilterChange}
              className="input"
            />
          </div>
          <div>
            <label>End Date</label>
            <input
              type="date"
              name="end_date"
              value={filters.end_date}
              onChange={handleFilterChange}
              className="input"
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button
              onClick={handleClearFilters}
              className="btn btn-secondary"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {loading && <div className="loading">Loading snapshots...</div>}
      {error && <div className="error">Error: {error}</div>}
      {!loading && !error && (
        <>
          <SnapshotValueChart
            snapshots={snapshots}
            onFilterChange={handleQuickFilterChange}
            activeFilter={activeQuickFilter}
          />
          <SnapshotsTable snapshots={snapshots} />
        </>
      )}
    </div>
  );
}

export default Snapshots;
