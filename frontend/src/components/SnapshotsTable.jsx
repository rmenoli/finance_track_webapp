import SnapshotAssetTypeChart from './SnapshotAssetTypeChart';
import './SnapshotsTable.css';

function SnapshotsTable({ snapshots }) {
  if (!snapshots || snapshots.length === 0) {
    return (
      <div className="empty-state">
        <p>No snapshots found. Try adjusting your filters or create a new snapshot.</p>
      </div>
    );
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (value, decimals = 2) => {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
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
          </tr>
        </thead>
        <tbody>
          {snapshots.map((snapshot, index) => (
            <tr key={`${snapshot.snapshot_date}-${index}`}>
              <td>{formatDate(snapshot.snapshot_date)}</td>
              <td className="currency-value">€{formatCurrency(snapshot.total_value_eur)}</td>
              <td>
                <div className="breakdown-list">
                  {snapshot.by_currency.map((item, idx) => (
                    <div key={`currency-${idx}`} className="breakdown-item">
                      <span className="breakdown-label">{item.currency}:</span>
                      <span className="breakdown-value">
                        {item.currency === 'EUR' ? '€' : ''}{formatCurrency(item.total_value)}
                      </span>
                    </div>
                  ))}
                </div>
              </td>
              <td>
                <div className="breakdown-list">
                  {snapshot.by_asset_type.map((item, idx) => (
                    <div key={`asset-${idx}`} className="breakdown-item">
                      <span className="breakdown-label">{item.asset_type}:</span>
                      <span className="breakdown-value">€{formatCurrency(item.total_value_eur)}</span>
                    </div>
                  ))}
                </div>
              </td>
              <td className="chart-cell">
                <SnapshotAssetTypeChart assetTypeBreakdown={snapshot.by_asset_type} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default SnapshotsTable;
