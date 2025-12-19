import './DashboardHoldingsTable.css';
import FormattedNumber from './FormattedNumber';

function ClosedPositionsTable({ closedPositions, isinNames = {} }) {
  if (!closedPositions || closedPositions.length === 0) {
    return <p>No closed positions yet.</p>;
  }

  return (
    <div className="table-container">
      <table className="table dashboard-holdings-table">
        <thead>
          <tr>
            <th>ISIN</th>
            <th>Buy In</th>
            <th>Total Sold</th>
            <th>P/L</th>
            <th>Total Fees</th>
            <th>P/L (incl. fees)</th>
          </tr>
        </thead>
        <tbody>
          {closedPositions.map(position => {
            const totalCostWithoutFees = parseFloat(position.total_cost_without_fees);
            const totalGainsWithoutFees = parseFloat(position.total_gains_without_fees);

            return (
              <tr key={position.isin}>
                {/* ISIN */}
                <td>
                  {isinNames[position.isin] && (
                    <div style={{ fontWeight: 'bold', fontSize: '0.9em', color: '#333', marginBottom: '2px' }}>
                      {isinNames[position.isin]}
                    </div>
                  )}
                  <span style={{ fontStyle: 'italic' }}>{position.isin}</span>
                </td>

                {/* Buy In (total cost without fees) */}
                <td>
                  <div>
                    <FormattedNumber
                      value={totalCostWithoutFees}
                      currency={true}
                    />
                  </div>
                </td>

                {/* Total Sold (total gains without fees) */}
                <td>
                  <div>
                    <FormattedNumber
                      value={totalGainsWithoutFees}
                      currency={true}
                    />
                  </div>
                </td>

                {/* P/L (without fees) */}
                <td>
                  <div className={parseFloat(position.absolute_pl_without_fees) >= 0 ? 'positive' : 'negative'}>
                    {parseFloat(position.absolute_pl_without_fees) >= 0 ? '+' : ''}
                    <FormattedNumber value={position.absolute_pl_without_fees} currency={true} />
                  </div>
                  <div className={`sub-value ${parseFloat(position.percentage_pl_without_fees) >= 0 ? 'positive' : 'negative'}`}>
                    {parseFloat(position.percentage_pl_without_fees) >= 0 ? '↑' : '↓'}
                    <FormattedNumber value={Math.abs(parseFloat(position.percentage_pl_without_fees))} currency={false} />
                    %
                  </div>
                </td>

                {/* Total Fees */}
                <td>
                  <div>
                    <FormattedNumber value={position.total_fees} currency={true} />
                  </div>
                </td>

                {/* P/L (including fees) */}
                <td>
                  <div className={parseFloat(position.absolute_pl_with_fees) >= 0 ? 'positive' : 'negative'}>
                    {parseFloat(position.absolute_pl_with_fees) >= 0 ? '+' : ''}
                    <FormattedNumber value={position.absolute_pl_with_fees} currency={true} />
                  </div>
                  <div className={`sub-value ${parseFloat(position.percentage_pl_with_fees) >= 0 ? 'positive' : 'negative'}`}>
                    {parseFloat(position.percentage_pl_with_fees) >= 0 ? '↑' : '↓'}
                    <FormattedNumber value={Math.abs(parseFloat(position.percentage_pl_with_fees))} currency={false} />
                    %
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default ClosedPositionsTable;
