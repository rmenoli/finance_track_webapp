import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import './HoldingsDistributionChart.css'; // Reuse the same CSS

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

// Asset type configurations (same as in OtherAssetsTable)
const ASSET_TYPES = {
  investments: {
    label: 'Investimenti',
    hasAccounts: false,
    currency: 'EUR',
  },
  crypto: {
    label: 'Crypto',
    hasAccounts: false,
    currency: 'EUR',
  },
  cash_eur: {
    label: 'Cash EUR',
    hasAccounts: true,
    currency: 'EUR',
  },
  cash_czk: {
    label: 'Cash CZK',
    hasAccounts: true,
    currency: 'CZK',
  },
  cd_account: {
    label: 'CD svincolabile',
    hasAccounts: false,
    currency: 'CZK',
  },
  pension_fund: {
    label: 'Fondo Pensione',
    hasAccounts: false,
    currency: 'CZK',
  },
};

const ACCOUNTS = ['CSOB', 'RAIF', 'Revolut', 'Wise', 'Degiro'];

function OtherAssetsDistributionChart({ assets, exchangeRate }) {
  // Transform assets array to map: { assetType: { account: { value, currency } } }
  const assetsMap = {};
  assets.forEach((asset) => {
    if (!assetsMap[asset.asset_type]) {
      assetsMap[asset.asset_type] = {};
    }

    const key = asset.asset_detail || 'default';
    assetsMap[asset.asset_type][key] = {
      value: parseFloat(asset.value) || 0,
      currency: asset.currency,
    };
  });

  // Calculate EUR value for each asset type
  const calculateRowTotalEur = (assetType, config) => {
    let totalInNative = 0;

    if (config.hasAccounts) {
      // Sum all accounts
      ACCOUNTS.forEach((account) => {
        const value = assetsMap[assetType]?.[account]?.value || 0;
        totalInNative += value;
      });
    } else {
      // Single value
      totalInNative = assetsMap[assetType]?.default?.value || 0;
    }

    // Convert to EUR if CZK
    const totalInEur =
      config.currency === 'CZK' ? totalInNative / exchangeRate : totalInNative;

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

  // Generate colors for the pie chart
  const generateColors = (count) => {
    const colors = [
      'rgba(54, 162, 235, 0.8)',   // Blue
      'rgba(255, 99, 132, 0.8)',   // Red
      'rgba(255, 206, 86, 0.8)',   // Yellow
      'rgba(75, 192, 192, 0.8)',   // Teal
      'rgba(153, 102, 255, 0.8)',  // Purple
      'rgba(255, 159, 64, 0.8)',   // Orange
      'rgba(199, 199, 199, 0.8)',  // Gray
      'rgba(83, 102, 255, 0.8)',   // Indigo
      'rgba(255, 99, 255, 0.8)',   // Pink
      'rgba(99, 255, 132, 0.8)',   // Green
    ];

    // If we have more assets than colors, generate additional colors
    if (count > colors.length) {
      for (let i = colors.length; i < count; i++) {
        const hue = (i * 137.5) % 360; // Golden angle
        colors.push(`hsla(${hue}, 70%, 60%, 0.8)`);
      }
    }

    return colors.slice(0, count);
  };

  const colors = generateColors(chartDataWithPercentages.length);
  const borderColors = colors.map(color => color.replace('0.8', '1'));

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
