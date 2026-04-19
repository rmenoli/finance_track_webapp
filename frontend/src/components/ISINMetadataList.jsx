import './ISINMetadataList.css';

function ISINMetadataList({ metadata, onEdit, onDelete }) {
  if (metadata.length === 0) {
    return (
      <div className="empty-state">
        <p>No ISIN metadata found.</p>
      </div>
    );
  }

  const getTypeLabel = (type) => {
    switch (type) {
      case 'STOCK':
        return 'Stock';
      case 'BOND':
        return 'Bond';
      case 'REAL_ASSET':
        return 'Real Asset';
      default:
        return type;
    }
  };

  const getTypeBadgeClass = (type) => {
    switch (type) {
      case 'STOCK':
        return 'badge-stock';
      case 'BOND':
        return 'badge-bond';
      case 'REAL_ASSET':
        return 'badge-real-asset';
      default:
        return 'badge-default';
    }
  };

  return (
    <div className="isin-metadata-list">
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>ISIN</th>
              <th>Name</th>
              <th>Type</th>
              <th className="th-narrow">Metadata<br/>information<br/>available</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {metadata.map((item) => (
              <tr key={item.isin}>
                <td><strong>{item.isin}</strong></td>
                <td>{item.name}</td>
                <td>
                  <span className={`badge ${getTypeBadgeClass(item.type)}`}>
                    {getTypeLabel(item.type)}
                  </span>
                </td>
                <td>
                  {item.has_breakdown ? (
                    <span className="badge badge-breakdown" title="ETF breakdown data available">
                      {'\u2713'}
                    </span>
                  ) : (
                    <span className="badge badge-no-breakdown" title="No ETF breakdown data">
                      {'\u2717'}
                    </span>
                  )}
                </td>
                <td>
                  <div className="action-buttons">
                    <button
                      onClick={() => onEdit(item.isin)}
                      className="btn-icon"
                      title="Edit"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => onDelete(item.isin)}
                      className="btn-icon"
                      title="Delete"
                    >
                      🗑️
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default ISINMetadataList;
