// Centralized chart color configuration
// This ensures consistent colors across all chart components

// Asset type color mappings (based on SnapshotValueChart's ASSET_TYPE_COLORS)
export const ASSET_TYPE_COLORS = {
  investments: { border: 'hsla(9, 82%, 57%, 1.00)', background: 'rgba(54, 162, 235, 0.1)' },
  crypto: { border: 'hsla(317, 100%, 63%, 1.00)', background: 'rgba(255, 159, 64, 0.1)' },
  cash_eur: { border: 'rgba(75, 192, 192, 1)', background: 'rgba(75, 192, 192, 0.1)' },
  cash_czk: { border: 'hsla(213, 100%, 70%, 1.00)', background: 'rgba(153, 102, 255, 0.1)' },
  cd_account: { border: 'rgba(61, 212, 53, 1)', background: 'rgba(255, 206, 86, 0.1)' },
  pension_fund: { border: 'rgba(255, 202, 68, 1)', background: 'rgba(255, 99, 132, 0.1)' },
};

// Fallback colors for unmapped asset types (used in order)
export const FALLBACK_CHART_COLORS = [
  'rgba(199, 199, 199, 0.8)',  // Gray
  'rgba(83, 102, 255, 0.8)',   // Indigo
  'rgba(255, 99, 255, 0.8)',   // Pink
  'rgba(99, 255, 132, 0.8)',   // Green
];

/**
 * Generate colors for a list of items (asset types or ISINs)
 * @param {Array} items - Array of items to generate colors for
 * @param {string|null} assetTypeKey - Optional key to extract asset type from each item
 * @returns {{colors: string[], borderColors: string[]}} - Arrays of colors and border colors
 *
 * Usage examples:
 * - generateChartColors(chartData, 'assetType') - for asset type based coloring
 * - generateChartColors(holdings, null) - for sequential coloring without asset type mapping
 */
export const generateChartColors = (items, assetTypeKey = null) => {
  const colors = [];
  const borderColors = [];

  items.forEach((item, index) => {
    // If assetTypeKey provided, try to get color from ASSET_TYPE_COLORS
    const assetType = assetTypeKey ? item[assetTypeKey] : item;

    if (ASSET_TYPE_COLORS[assetType]) {
      // Use mapped color with 0.8 opacity for pie charts
      const color = ASSET_TYPE_COLORS[assetType].border.replace('1)', '0.8)');
      colors.push(color);
      borderColors.push(ASSET_TYPE_COLORS[assetType].border);
    } else {
      // Use fallback or generate with golden angle
      if (index < FALLBACK_CHART_COLORS.length) {
        colors.push(FALLBACK_CHART_COLORS[index]);
        borderColors.push(FALLBACK_CHART_COLORS[index].replace('0.8', '1'));
      } else {
        // Generate additional colors using golden angle for good distribution
        const hue = (index * 137.5) % 360; // Golden angle
        colors.push(`hsla(${hue}, 70%, 60%, 0.8)`);
        borderColors.push(`hsla(${hue}, 70%, 60%, 1)`);
      }
    }
  });

  return { colors, borderColors };
};
