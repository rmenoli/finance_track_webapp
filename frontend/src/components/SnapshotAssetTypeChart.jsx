import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { formatCurrency } from '../utils/numberFormat';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

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

    // If we have more items than colors, generate additional colors
    if (count > colors.length) {
      for (let i = colors.length; i < count; i++) {
        const hue = (i * 137.5) % 360; // Golden angle
        colors.push(`hsla(${hue}, 70%, 60%, 0.8)`);
      }
    }

    return colors.slice(0, count);
  };

  const colors = generateColors(chartData.length);
  const borderColors = colors.map(color => color.replace('0.8', '1'));

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
    },
  };

  return (
    <div className="snapshot-chart-wrapper">
      <Pie data={data} options={options} />
    </div>
  );
}

export default SnapshotAssetTypeChart;
