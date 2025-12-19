import './TransactionList.css';
import FormattedNumber from './FormattedNumber';

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
              <th>Total - (no fees)</th>
              <th>Fee</th>
              <th>Total - With fees</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((txn) => {
              const total = parseFloat(txn.units) * parseFloat(txn.price_per_unit);
              const totalWithFees = total + parseFloat(txn.fee);
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
                  <td>
                    <FormattedNumber value={txn.units} currency={false} decimals={0} />
                  </td>
                  <td>
                    <FormattedNumber value={txn.price_per_unit} currency={true} />
                  </td>
                  <td>
                    <FormattedNumber value={total} currency={true} />
                  </td>
                  <td>
                    <FormattedNumber value={txn.fee} currency={true} />
                  </td>
                  <td>
                    <FormattedNumber value={totalWithFees} currency={true} />
                  </td>
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
