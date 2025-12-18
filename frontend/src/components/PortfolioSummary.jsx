import './PortfolioSummary.css';
import DashboardHoldingsTable from './DashboardHoldingsTable';

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

      <div className="summary-section full-width">
        <h3>Current Holdings</h3>
        {data.holdings.length === 0 ? (
          <p>No holdings yet.</p>
        ) : (
          <DashboardHoldingsTable holdings={data.holdings} />
        )}
      </div>
    </div>
  );
}

export default PortfolioSummary;
