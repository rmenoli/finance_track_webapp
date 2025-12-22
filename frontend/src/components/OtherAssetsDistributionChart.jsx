import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { ASSET_TYPES, ACCOUNTS } from '../constants/otherAssets';
import { generateChartColors } from '../constants/chartColors';
import './HoldingsDistributionChart.css'; // Reuse the same CSS

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, ChartDataLabels);

function OtherAssetsDistributionChart({ assets, exchangeRate }) {
  // Transform assets array to map: { assetType: { account: { value, currency, value_eur } } }
  const assetsMap = {};
  assets.forEach((asset) => {
    if (!assetsMap[asset.asset_type]) {
      assetsMap[asset.asset_type] = {};
    }

    const key = asset.asset_detail || 'default';
    assetsMap[asset.asset_type][key] = {
      value: parseFloat(asset.value) || 0,
      currency: asset.currency,
      value_eur: parseFloat(asset.value_eur) || 0, // EUR value from backend
    };
  });

  // Calculate EUR value for each asset type (using backend-calculated EUR values)
  const calculateRowTotalEur = (assetType, config) => {
    let totalInEur = 0;

    if (config.hasAccounts) {
      // Sum all accounts
      ACCOUNTS.forEach((account) => {
        totalInEur += assetsMap[assetType]?.[account]?.value_eur || 0;
      });
    } else {
      // Single value
      totalInEur = assetsMap[assetType]?.default?.value_eur || 0;
    }

    return totalInEur;
  };

  // Prepare chart data
  const chartData = Object.entries(ASSET_TYPES)
    .map(([assetType, config]) => {
      const valueInEur = calculateRowTotalEur(assetType, config);
      return {
        assetType: assetType,
        label: config.label,
        value: valueInEur,
      };
    })
    .filter(item => item.value > 0) // Only include assets with value
    .sort((a, b) => b.value - a.value); // Sort by value descending

  // Calculate total
  const totalValue = chartData.reduce((sum, item) => sum + item.value, 0);

  // Calculate percentages
  const chartDataWithPercentages = chartData.map(item => ({
    ...item,
    percentage: totalValue > 0 ? (item.value / totalValue) * 100 : 0,
  }));

  // If no data, show message
  if (chartDataWithPercentages.length === 0) {
    return (
      <div className="holdings-chart-container">
        <div className="no-data-message">
          No assets data available. Please enter values for your assets.
        </div>
      </div>
    );
  }

  // Generate colors using centralized color configuration
  const { colors, borderColors } = generateChartColors(chartDataWithPercentages, 'assetType');

  const data = {
    labels: chartDataWithPercentages.map(item => item.label),
    datasets: [
      {
        label: 'Other Assets Distribution',
        data: chartDataWithPercentages.map(item => item.value),
        backgroundColor: colors,
        borderColor: borderColors,
        borderWidth: 2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          padding: 15,
          font: {
            size: 12,
          },
          generateLabels: (chart) => {
            const data = chart.data;
            if (data.labels.length && data.datasets.length) {
              return data.labels.map((label, i) => {
                const percentage = chartDataWithPercentages[i].percentage.toFixed(1);
                return {
                  text: `${label} (${percentage}%)`,
                  fillStyle: data.datasets[0].backgroundColor[i],
                  strokeStyle: data.datasets[0].borderColor[i],
                  lineWidth: data.datasets[0].borderWidth,
                  hidden: false,
                  index: i,
                };
              });
            }
            return [];
          },
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const item = chartDataWithPercentages[context.dataIndex];
            return [
              `${item.label}`,
              `Value: €${item.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
              `Share: ${item.percentage.toFixed(2)}%`
            ];
          },
        },
      },
      datalabels: {
        color: '#fff',
        font: {
          weight: 'bold',
          size: 14,
        },
        formatter: (value, context) => {
          const percentage = chartDataWithPercentages[context.dataIndex].percentage;
          // Only show label if percentage is >= 4%
          if (percentage >= 4) {
            return `${percentage.toFixed(0)}%`;
          }
          return null; // Don't show label for very small slices
        },
      },
    },
  };

  return (
    <div className="holdings-chart-container">
      <h3>Other Assets Distribution</h3>
      <div className="chart-wrapper">
        <Pie data={data} options={options} />
      </div>
    </div>
  );
}

export default OtherAssetsDistributionChart;
