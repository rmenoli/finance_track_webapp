import './DashboardHoldingsTable.css';
import FormattedNumber from './FormattedNumber';

function ClosedPositionsTable({ closedPositions, isinNames = {} }) {
  const calculatePL = (position) => {
    // P/L without fees
    const totalCostWithoutFees = parseFloat(position.total_cost_without_fees);
    const totalGainsWithoutFees = parseFloat(position.total_gains_without_fees);
    const absolutePLWithoutFees = totalGainsWithoutFees - totalCostWithoutFees;
    const percentagePLWithoutFees = totalCostWithoutFees > 0 ? (absolutePLWithoutFees / totalCostWithoutFees) * 100 : 0;

    // P/L including fees
    const totalFees = parseFloat(position.total_fees);
    const absolutePLWithFees = absolutePLWithoutFees - totalFees;
    const percentagePLWithFees = totalCostWithoutFees > 0 ? (absolutePLWithFees / totalCostWithoutFees) * 100 : 0;

    return {
      withoutFees: { absolutePL: absolutePLWithoutFees, percentagePL: percentagePLWithoutFees },
      withFees: { absolutePL: absolutePLWithFees, percentagePL: percentagePLWithFees }
    };
  };

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
            const plData = calculatePL(position);
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
                  <div className={plData.withoutFees.absolutePL >= 0 ? 'positive' : 'negative'}>
                    {plData.withoutFees.absolutePL >= 0 ? '+' : ''}
                    <FormattedNumber value={plData.withoutFees.absolutePL} currency={true} />
                  </div>
                  <div className={`sub-value ${plData.withoutFees.percentagePL >= 0 ? 'positive' : 'negative'}`}>
                    {plData.withoutFees.percentagePL >= 0 ? '↑' : '↓'}
                    <FormattedNumber value={Math.abs(plData.withoutFees.percentagePL)} currency={false} />
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
                  <div className={plData.withFees.absolutePL >= 0 ? 'positive' : 'negative'}>
                    {plData.withFees.absolutePL >= 0 ? '+' : ''}
                    <FormattedNumber value={plData.withFees.absolutePL} currency={true} />
                  </div>
                  <div className={`sub-value ${plData.withFees.percentagePL >= 0 ? 'positive' : 'negative'}`}>
                    {plData.withFees.percentagePL >= 0 ? '↑' : '↓'}
                    <FormattedNumber value={Math.abs(plData.withFees.percentagePL)} currency={false} />
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
