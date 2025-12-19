/**
 * Formats a number with apostrophe as thousands separator
 * @param {number} value - The number to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {object} Object with 'integer' and 'decimal' parts
 *
 * Examples:
 * formatNumber(1000) -> { integer: "1'000", decimal: "00" }
 * formatNumber(10000.5) -> { integer: "10'000", decimal: "50" }
 * formatNumber(1234567.89) -> { integer: "1'234'567", decimal: "89" }
 */
export function formatNumber(value, decimals = 2) {
  if (value === null || value === undefined || isNaN(value)) {
    return { integer: '0', decimal: '0'.repeat(decimals) };
  }

  const num = parseFloat(value);
  const fixed = num.toFixed(decimals);
  const [integerPart, decimalPart] = fixed.split('.');

  // Add apostrophe as thousands separator
  const formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, "'");

  return {
    integer: formattedInteger,
    decimal: decimalPart || '0'.repeat(decimals)
  };
}

/**
 * Formats a currency value with € symbol
 * @param {number} value - The value to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {object} Object with 'integer' and 'decimal' parts, including currency symbol
 */
export function formatCurrency(value, decimals = 2) {
  const formatted = formatNumber(value, decimals);
  return {
    integer: `€${formatted.integer}`,
    decimal: formatted.decimal
  };
}
