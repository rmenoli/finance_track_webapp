import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { isinMetadataAPI } from '../services/api';
import ISINMetadataList from '../components/ISINMetadataList';
import './ISINMetadata.css';

function ISINMetadata() {
  const [metadata, setMetadata] = useState([]);
  const [filters, setFilters] = useState({
    type: '',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadMetadata();
  }, [filters]);

  const loadMetadata = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filters.type) {
        params.type = filters.type;
      }

      const data = await isinMetadataAPI.getAll(params);
      setMetadata(data.items || []);
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

  const handleDelete = async (isin) => {
    if (!window.confirm(`Are you sure you want to delete metadata for ${isin}?`)) {
      return;
    }

    try {
      await isinMetadataAPI.delete(isin);
      loadMetadata();
    } catch (err) {
      alert('Error deleting ISIN metadata: ' + err.message);
    }
  };

  const handleEdit = (isin) => {
    navigate(`/isin-metadata/edit/${isin}`);
  };

  const clearFilters = () => {
    setFilters({
      type: '',
    });
  };

  return (
    <div className="isin-metadata-page">
      <div className="page-header">
        <h1>ISIN Metadata</h1>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/isin-metadata/add')}
        >
          + Add ISIN Metadata
        </button>
      </div>

      <div className="filters-card">
        <h3>Filters</h3>
        <div className="filters-grid">
          <div className="filter-group">
            <label>Type</label>
            <select
              name="type"
              value={filters.type}
              onChange={handleFilterChange}
            >
              <option value="">All Types</option>
              <option value="STOCK">Stock</option>
              <option value="BOND">Bond</option>
              <option value="REAL_ASSET">Real Asset</option>
            </select>
          </div>
          <div className="filter-actions">
            <button className="btn btn-secondary" onClick={clearFilters}>
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <>
          <div className="results-summary">
            <p>{metadata.length} metadata record{metadata.length !== 1 ? 's' : ''} found</p>
          </div>
          <ISINMetadataList
            metadata={metadata}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        </>
      )}
    </div>
  );
}

export default ISINMetadata;
