import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import './SnapshotValueChart.css';

// Register Chart.js components
ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Title,
  Tooltip,
  Legend,
  Filler
);

function SnapshotValueChart({ snapshots, avgMonthlyIncrement, onFilterChange, activeFilter }) {
  // Handle empty state
  if (!snapshots || snapshots.length === 0) {
    return (
      <div className="snapshot-value-chart-container">
        <div className="no-data-message">
          No snapshot data available. Create a snapshot to see your portfolio value over time.
        </div>
      </div>
    );
  }

  // Sort snapshots by date (oldest first for chart)
  const sortedSnapshots = [...snapshots].sort((a, b) =>
    new Date(a.snapshot_date) - new Date(b.snapshot_date)
  );

  // Prepare chart data with time-based x-axis
  const chartData = {
    datasets: [
      {
        label: 'Total Portfolio Value',
        data: sortedSnapshots.map(s => ({
          x: new Date(s.snapshot_date),
          y: parseFloat(s.total_value_eur)
        })),
        borderColor: 'rgba(54, 162, 235, 1)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderWidth: 2,
        tension: 0.3,
        fill: true,
        pointRadius: 3,
        pointHoverRadius: 6,
        pointBackgroundColor: 'rgba(54, 162, 235, 1)',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
      },
    ],
  };

  // Chart options
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        padding: 12,
        titleFont: {
          size: 14,
        },
        bodyFont: {
          size: 13,
        },
        callbacks: {
          title: (context) => {
            const date = new Date(context[0].parsed.x);
            return date.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            });
          },
          label: (context) => {
            const value = parseFloat(context.parsed.y);
            return `Total Value: €${value.toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: false,
        ticks: {
          callback: (value) => `€${value.toLocaleString('en-US')}`,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
      x: {
        type: 'time',
        time: {
          unit: 'day',
          displayFormats: {
            day: "MMM yy",
            week: "MMM yy",
            month: "MMM yy",
          },
          tooltipFormat: 'MMM d, yyyy HH:mm',
        },
        grid: {
          display: false,
        },
        ticks: {
          source: 'auto',
          maxRotation: 0,
          autoSkip: true,
        },
      },
    },
  };

  // Get current snapshot (most recent = last in sorted array)
  const currentSnapshot = sortedSnapshots[sortedSnapshots.length - 1];
  const currentValue = currentSnapshot?.total_value_eur || 0;

  // Use backend-calculated changes from oldest snapshot
  const change = parseFloat(currentSnapshot?.absolute_change_from_oldest || 0);
  const changePercent = parseFloat(currentSnapshot?.percentage_change_from_oldest || 0);

  return (
    <div className="snapshot-value-chart-container">
      <div className="chart-header">
        <div className="chart-title-section">
          <h3>NW Over Time</h3>
          <div className="current-value">
            <span className="value">€{parseFloat(currentValue).toLocaleString('en-US', {
              minimumFractionDigits: 2,
              maximumFractionDigits: 2,
            })}</span>
            <span className={`change ${change >= 0 ? 'positive' : 'negative'}`}>
              {change >= 0 ? '+' : ''}€{Math.abs(change).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
              {' '}({change >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
            </span>
          </div>
          {avgMonthlyIncrement !== null && avgMonthlyIncrement !== undefined && (
            <div className="monthly-average">
              <span className="label">Monthly Avg Value Increase: </span>
              <span className={`value ${parseFloat(avgMonthlyIncrement) >= 0 ? 'positive' : 'negative'}`}>
                {parseFloat(avgMonthlyIncrement) >= 0 ? '+' : ''}€{Math.abs(parseFloat(avgMonthlyIncrement)).toLocaleString('en-US', {
                  minimumFractionDigits: 2,
                  maximumFractionDigits: 2,
                })}
              </span>
            </div>
          )}
        </div>
        <div className="quick-filters">
          {['YTD', '1Y', '2Y', '3Y', 'ALL'].map(filter => (
            <button
              key={filter}
              className={`filter-btn ${activeFilter === filter ? 'active' : ''}`}
              onClick={() => onFilterChange(filter)}
            >
              {filter}
            </button>
          ))}
        </div>
      </div>
      <div className="chart-wrapper">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}

export default SnapshotValueChart;
