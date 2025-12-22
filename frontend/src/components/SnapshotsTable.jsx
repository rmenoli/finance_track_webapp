import SnapshotAssetTypeChart from './SnapshotAssetTypeChart';
import FormattedNumber from './FormattedNumber';
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default SnapshotsTable;
