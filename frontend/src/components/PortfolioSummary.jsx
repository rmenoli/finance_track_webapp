import './PortfolioSummary.css';
import DashboardHoldingsTable from './DashboardHoldingsTable';
import ClosedPositionsTable from './ClosedPositionsTable';
import FormattedNumber from './FormattedNumber';

function PortfolioSummary({ data, onDataChange }) {
  return (
    <div className="portfolio-summary">
      {/* Hero Section - Most Important Metrics */}
      <div className="hero-metrics">
        <div className="summary-card hero-card">
          <h3>Current Portfolio Value</h3>
          <p className="summary-value hero-value">
            <FormattedNumber
              value={data.total_current_portfolio_invested_value}
              currency={true}
            />
          </p>
        </div>

        <div className="summary-card hero-card">
          <h3>Total P/L</h3>
          <p className={`summary-value hero-value ${parseFloat(data.total_profit_loss) >= 0 ? 'positive' : 'negative'}`}>
            <FormattedNumber
              value={data.total_profit_loss}
              currency={true}
            />
          </p>
        </div>
      </div>

      {/* Details Section - Less Important Metrics */}
      <div className="summary-card details-card">
        <div className="details-grid">
          <div className="detail-item">
            <span className="detail-label">Total Invested</span>
            <span className="detail-value">
              <FormattedNumber value={data.total_invested} currency={true} />
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Total Fees</span>
            <span className="detail-value">
              <FormattedNumber value={data.total_fees} currency={true} />
            </span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Total Withdrawn</span>
            <span className="detail-value">
              <FormattedNumber value={data.total_withdrawn} currency={true} />
            </span>
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

      {/* Closed Positions Section */}
      <div className="summary-section full-width">
        <h3>Closed Positions</h3>
        {!data.closed_positions || data.closed_positions.length === 0 ? (
          <p>No closed positions yet.</p>
        ) : (
          <ClosedPositionsTable closedPositions={data.closed_positions} />
        )}
      </div>
    </div>
  );
}

export default PortfolioSummary;
