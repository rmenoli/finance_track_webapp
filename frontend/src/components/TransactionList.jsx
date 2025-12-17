import './TransactionList.css';

function TransactionList({ transactions, onEdit, onDelete }) {
  if (transactions.length === 0) {
    return (
      <div className="empty-state">
        <p>No transactions found.</p>
      </div>
    );
  }

  return (
    <div className="transaction-list">
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Date</th>
              <th>ISIN</th>
              <th>Broker</th>
              <th>Type</th>
              <th>Units</th>
              <th>Price/Unit</th>
              <th>Fee</th>
              <th>Total</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn) => {
              const total = parseFloat(txn.units) * parseFloat(txn.price_per_unit);
              return (
                <tr key={txn.id}>
                  <td>{new Date(txn.date).toLocaleDateString()}</td>
                  <td><strong>{txn.isin}</strong></td>
                  <td>{txn.broker}</td>
                  <td>
                    <span className={`badge badge-${txn.transaction_type.toLowerCase()}`}>
                      {txn.transaction_type}
                    </span>
                  </td>
                  <td>{parseFloat(txn.units).toFixed(4)}</td>
                  <td>€{parseFloat(txn.price_per_unit).toFixed(2)}</td>
                  <td>€{parseFloat(txn.fee).toFixed(2)}</td>
                  <td>€{total.toFixed(2)}</td>
                  <td>
                    <div className="action-buttons">
                      <button
                        onClick={() => onEdit(txn.id)}
                        className="btn-icon"
                        title="Edit"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => onDelete(txn.id)}
                        className="btn-icon"
                        title="Delete"
                      >
                        🗑️
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default TransactionList;
