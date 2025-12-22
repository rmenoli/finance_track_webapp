import SnapshotAssetTypeChart from './SnapshotAssetTypeChart';
import FormattedNumber from './FormattedNumber';
import './SnapshotsTable.css';

function SnapshotsTable({ snapshots, onDelete }) {
  if (!snapshots || snapshots.length === 0) {
    return (
      <div className="empty-state">
        <p>No snapshots found. Try adjusting your filters or create a new snapshot.</p>
      </div>
    );
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const day = date.getDate();
    const month = date.toLocaleString('en-US', { month: 'short' });
    const year = date.getFullYear();
    return `${day} ${month} ${year}`;
  };

  const handleDelete = async (snapshot) => {
    const formattedDate = formatDate(snapshot.snapshot_date);

    if (!window.confirm(`Are you sure you want to delete the snapshot from ${formattedDate}? This action cannot be undone.`)) {
      return;
    }

    try {
      // Send full datetime string for exact matching
      // URL encoding is handled automatically by fetch API
      await onDelete(snapshot.snapshot_date);
    } catch (error) {
      console.error('Failed to delete snapshot:', error);
      alert('Failed to delete snapshot. Please try again.');
    }
  };

  return (
    <div className="table-container">
      <table className="table snapshots-table">
        <thead>
          <tr>
            <th>Snapshot Date</th>
            <th>Total Value (EUR)</th>
            <th>By Currency</th>
            <th>By Asset Type (EUR)</th>
            <th>Asset Distribution Chart</th>
            <th className="actions-header"></th>
          </tr>
        </thead>
        <tbody>
          {snapshots.map((snapshot, index) => (
            <tr key={`${snapshot.snapshot_date}-${index}`} className="snapshot-row">
              <td>{formatDate(snapshot.snapshot_date)}</td>
              <td className="currency-value">
                <FormattedNumber value={snapshot.total_value_eur} currency decimals={2} />
              </td>
              <td>
                <div className="breakdown-list">
                  {snapshot.by_currency.map((item, idx) => (
                    <div key={`currency-${idx}`} className="breakdown-item">
                      <span className="breakdown-label">{item.currency}:</span>
                      <span className="breakdown-value">
                        {item.currency === 'EUR' ? (
                          <FormattedNumber value={item.total_value} currency decimals={2} />
                        ) : (
                          <FormattedNumber value={item.total_value} decimals={2} />
                        )}
                      </span>
                    </div>
                  ))}
                  <div className="breakdown-item exchange-rate-info">
                    <span className="exchange-rate-label">
                      Rate: <FormattedNumber value={snapshot.exchange_rate_used} decimals={2} /> CZK/EUR
                    </span>
                  </div>
                </div>
              </td>
              <td>
                <div className="breakdown-list">
                  {snapshot.by_asset_type.map((item, idx) => (
                    <div key={`asset-${idx}`} className="breakdown-item">
                      <span className="breakdown-label">{item.asset_type}:</span>
                      <span className="breakdown-value">
                        <FormattedNumber value={item.total_value_eur} currency decimals={2} />
                      </span>
                    </div>
                  ))}
                </div>
              </td>
              <td className="chart-cell">
                <SnapshotAssetTypeChart assetTypeBreakdown={snapshot.by_asset_type} />
              </td>
              <td className="actions-cell">
                <button
                  className="delete-button"
                  onClick={() => handleDelete(snapshot)}
                  title="Delete snapshot"
                  aria-label="Delete snapshot"
                >
                  ✕
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default SnapshotsTable;
