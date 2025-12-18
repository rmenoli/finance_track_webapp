import './PortfolioSummary.css';
import DashboardHoldingsTable from './DashboardHoldingsTable';

function PortfolioSummary({ data, onDataChange }) {
  return (
    <div className="portfolio-summary">
      {/* Hero Section - Most Important Metrics */}
      <div className="hero-metrics">
        <div className="summary-card hero-card">
          <h3>Current Portfolio Value</h3>
          <p className="summary-value hero-value">
            €{parseFloat(data.total_current_portfolio_invested_value).toFixed(2)}
          </p>
        </div>

        <div className="summary-card hero-card">
          <h3>Total P/L</h3>
          <p className={`summary-value hero-value ${parseFloat(data.total_profit_loss) >= 0 ? 'positive' : 'negative'}`}>
            €{parseFloat(data.total_profit_loss).toFixed(2)}
          </p>
        </div>
      </div>

      {/* Details Section - Less Important Metrics */}
      <div className="summary-card details-card">
        <div className="details-grid">
          <div className="detail-item">
            <span className="detail-label">Total Invested</span>
            <span className="detail-value">€{parseFloat(data.total_invested).toFixed(2)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Total Fees</span>
            <span className="detail-value">€{parseFloat(data.total_fees).toFixed(2)}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Total Withdrawn</span>
            <span className="detail-value">€{parseFloat(data.total_withdrawn).toFixed(2)}</span>
          </div>
        </div>
      </div>

      {/* Holdings Section - Keep Existing */}
      <div className="summary-section full-width">
        <h3>Current Holdings</h3>
        {data.holdings.length === 0 ? (
          <p>No holdings yet.</p>
        ) : (
          <DashboardHoldingsTable holdings={data.holdings} onPositionValueChange={onDataChange} />
        )}
      </div>
    </div>
  );
}

export default PortfolioSummary;
