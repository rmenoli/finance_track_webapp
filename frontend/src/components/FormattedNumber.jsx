import { formatNumber, formatCurrency } from '../utils/numberFormat';
import './FormattedNumber.css';

/**
 * Component that renders a number with smaller decimal digits
 * @param {number} value - The number to display
 * @param {string} currency - If true, prepends € symbol (default: false)
 * @param {number} decimals - Number of decimal places (default: 2)
 * @param {string} className - Additional CSS classes
 */
function FormattedNumber({ value, currency = false, decimals = 2, className = '' }) {
  const formatted = currency
    ? formatCurrency(value, decimals)
    : formatNumber(value, decimals);

  return (
    <span className={`formatted-number ${className}`}>
      <span className="integer-part">{formatted.integer}</span>
      {decimals > 0 && (
        <>
          <span className="decimal-separator">.</span>
          <span className="decimal-part">{formatted.decimal}</span>
        </>
      )}
    </span>
  );
}

export default FormattedNumber;
