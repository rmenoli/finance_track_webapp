import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { formatCurrency } from '../utils/numberFormat';
import { generateChartColors } from '../constants/chartColors';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, ChartDataLabels);

function SnapshotAssetTypeChart({ assetTypeBreakdown }) {
  // If no data, return empty div
  if (!assetTypeBreakdown || assetTypeBreakdown.length === 0) {
    return <div className="snapshot-chart-empty">No data</div>;
  }

  // Calculate total and percentages
  const total = assetTypeBreakdown.reduce((sum, item) => sum + parseFloat(item.total_value_eur), 0);

  const chartData = assetTypeBreakdown.map(item => ({
    assetType: item.asset_type,
    value: parseFloat(item.total_value_eur),
    percentage: total > 0 ? (parseFloat(item.total_value_eur) / total) * 100 : 0,
  }));

  // Generate colors using centralized color configuration
  const { colors, borderColors } = generateChartColors(chartData, 'assetType');

  const data = {
    labels: chartData.map(item => item.assetType),
    datasets: [
      {
        label: 'Asset Type Distribution',
        data: chartData.map(item => item.value),
        backgroundColor: colors,
        borderColor: borderColors,
        borderWidth: 1,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        display: false, // Hide legend for compact display
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const item = chartData[context.dataIndex];
            const formatted = formatCurrency(item.value);
            return [
              `${item.assetType}`,
              `${formatted.integer}.${formatted.decimal}`,
              `${item.percentage.toFixed(1)}%`
            ];
          },
        },
      },
      datalabels: {
        color: '#fff',
        font: {
          weight: 'bold',
          size: 12,
        },
        formatter: (value, context) => {
          const percentage = chartData[context.dataIndex].percentage;
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
    <div className="snapshot-chart-wrapper">
      <Pie data={data} options={options} />
    </div>
  );
}

export default SnapshotAssetTypeChart;
