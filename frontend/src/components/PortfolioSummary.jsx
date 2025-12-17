import './PortfolioSummary.css';

function PortfolioSummary({ data }) {
  return (
    <div className="portfolio-summary">
      <div className="summary-card">
        <h3>Total Invested</h3>
        <p className="summary-value">€{parseFloat(data.total_invested).toFixed(2)}</p>
      </div>

      <div className="summary-card">
        <h3>Total Fees</h3>
        <p className="summary-value">€{parseFloat(data.total_fees).toFixed(2)}</p>
      </div>

      <div className="summary-card">
        <h3>Realized Gains</h3>
        <p className={`summary-value ${parseFloat(data.net_realized_gains) >= 0 ? 'positive' : 'negative'}`}>
          €{parseFloat(data.net_realized_gains).toFixed(2)}
        </p>
      </div>

      <div className="summary-card">
        <h3>Unique ISINs</h3>
        <p className="summary-value">{data.unique_isins}</p>
      </div>

      <div className="summary-card full-width">
        <h3>Current Holdings</h3>
        <p className="summary-value">
          €{data.holdings.reduce((sum, h) => sum + parseFloat(h.total_cost), 0).toFixed(2)}
        </p>
        <p className="summary-detail">{data.holdings.length} positions</p>
      </div>
    </div>
  );
}

export default PortfolioSummary;
