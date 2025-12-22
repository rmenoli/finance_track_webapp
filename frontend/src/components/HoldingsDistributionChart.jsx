import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import './HoldingsDistributionChart.css';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

function HoldingsDistributionChart({ holdings, currentValues, isinNames }) {
  // Calculate total portfolio value
  const totalValue = holdings.reduce((sum, holding) => {
    const currentValue = currentValues[holding.isin] || 0;
    return sum + currentValue;
  }, 0);

  // Filter out holdings with no current value and prepare chart data
  const chartData = holdings
    .map(holding => {
      const currentValue = currentValues[holding.isin] || 0;
      const percentage = totalValue > 0 ? (currentValue / totalValue) * 100 : 0;

      return {
        isin: holding.isin,
        name: isinNames[holding.isin] || holding.isin,
        value: currentValue,
        percentage: percentage
      };
    })
    .filter(item => item.value > 0) // Only include holdings with value
    .sort((a, b) => b.value - a.value); // Sort by value descending

  // If no data, show message
  if (chartData.length === 0) {
    return (
      <div className="holdings-chart-container">
        <div className="no-data-message">
          No holdings data available. Please enter current values for your positions.
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

    // If we have more holdings than colors, generate additional colors
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
    labels: chartData.map(item => item.name),
    datasets: [
      {
        label: 'Portfolio Distribution',
        data: chartData.map(item => item.value),
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
      datalabels: {
        display: false, // Disable datalabels for this chart
      },
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
                const value = data.datasets[0].data[i];
                const percentage = chartData[i].percentage.toFixed(1);
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
            const item = chartData[context.dataIndex];
            return [
              `${item.name}`,
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
      <h3>Portfolio Distribution</h3>
      <div className="chart-wrapper">
        <Pie data={data} options={options} />
      </div>
    </div>
  );
}

export default HoldingsDistributionChart;
