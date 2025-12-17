import './HoldingsTable.css';

function HoldingsTable({ holdings }) {
  return (
    <div className="holdings-table">
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>ISIN</th>
              <th>Units</th>
              <th>Average Cost/Unit</th>
              <th>Total Cost</th>
            </tr>
          </thead>
          <tbody>
            {holdings.map((holding) => (
              <tr key={holding.isin}>
                <td><strong>{holding.isin}</strong></td>
                <td>{parseFloat(holding.units).toFixed(4)}</td>
                <td>€{parseFloat(holding.average_cost_per_unit).toFixed(2)}</td>
                <td>€{parseFloat(holding.total_cost).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="total-row">
              <td><strong>Total</strong></td>
              <td><strong>{holdings.reduce((sum, h) => sum + parseFloat(h.units), 0).toFixed(4)}</strong></td>
              <td></td>
              <td><strong>€{holdings.reduce((sum, h) => sum + parseFloat(h.total_cost), 0).toFixed(2)}</strong></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

export default HoldingsTable;
