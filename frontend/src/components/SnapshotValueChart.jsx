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
import FormattedNumber from './FormattedNumber';
import { formatCurrency } from '../utils/numberFormat';
import { ASSET_TYPES } from '../constants/otherAssets';
import { ASSET_TYPE_COLORS, FALLBACK_CHART_COLORS } from '../constants/chartColors';
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

// Color scheme imported from centralized configuration

function SnapshotValueChart({ snapshots, avgMonthlyIncrement, onFilterChange, activeFilter }) {
  // Helper function: Extract unique asset types from snapshots
  const extractUniqueAssetTypes = (snapshots) => {
    const assetTypesSet = new Set();
    snapshots.forEach(snapshot => {
      if (snapshot.by_asset_type && Array.isArray(snapshot.by_asset_type)) {
        snapshot.by_asset_type.forEach(assetData => {
          assetTypesSet.add(assetData.asset_type);
        });
      }
    });
    return Array.from(assetTypesSet).sort();
  };

  // Helper function: Build dataset for specific asset type
  const buildAssetTypeDataset = (sortedSnapshots, assetType) => {
    return sortedSnapshots.map(snapshot => {
      const assetData = snapshot.by_asset_type?.find(
        item => item.asset_type === assetType
      );
      return {
        x: new Date(snapshot.snapshot_date),
        y: assetData ? parseFloat(assetData.total_value_eur) : 0
      };
    });
  };

  // Helper function: Format asset type labels
  const formatAssetTypeLabel = (assetType) => {
    if (ASSET_TYPES[assetType]?.label) {
      return ASSET_TYPES[assetType].label;
    }
    return assetType
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Helper function: Get color for asset type
  const getAssetTypeColor = (assetType, index) => {
    if (ASSET_TYPE_COLORS[assetType]) {
      return ASSET_TYPE_COLORS[assetType];
    }
    const fallbackIndex = index % FALLBACK_CHART_COLORS.length;
    const borderColor = FALLBACK_CHART_COLORS[fallbackIndex].replace('0.8', '1');
    return {
      border: borderColor,
      background: borderColor.replace('1)', '0.1)'),
    };
  };

  // Helper function: Transform snapshots to chart datasets
  const transformToChartDatasets = (sortedSnapshots) => {
    const datasets = [];
    const assetTypes = extractUniqueAssetTypes(sortedSnapshots);

    // Create dataset for each asset type
    assetTypes.forEach((assetType, index) => {
      const data = buildAssetTypeDataset(sortedSnapshots, assetType);
      const color = getAssetTypeColor(assetType, index);
      const label = formatAssetTypeLabel(assetType);

      datasets.push({
        label: label,
        data: data,
        borderColor: color.border,
        backgroundColor: color.background,
        borderWidth: 2,
        tension: 0.3,
        fill: false,
        pointRadius: 2,
        pointHoverRadius: 5,
        pointBackgroundColor: color.border,
        pointBorderColor: '#fff',
        pointBorderWidth: 1,
      });
    });

    // Add prominent total line (last = renders on top)
    datasets.push({
      label: 'Total Portfolio',
      data: sortedSnapshots.map(s => ({
        x: new Date(s.snapshot_date),
        y: parseFloat(s.total_value_eur)
      })),
      borderColor: 'rgba(44, 62, 80, 1)',
      backgroundColor: 'rgba(44, 62, 80, 0.1)',
      borderWidth: 3,
      borderDash: [5, 5],
      tension: 0.3,
      fill: true,
      pointRadius: 4,
      pointHoverRadius: 7,
      pointBackgroundColor: 'rgba(44, 62, 80, 1)',
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
    });

    return datasets;
  };

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

  // Prepare chart data with multiple lines
  const chartData = {
    datasets: transformToChartDatasets(sortedSnapshots)
  };

  // Chart options
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    layout: {
      padding: {
        bottom: 5,
      },
    },
    plugins: {
      datalabels: {
        display: false, // Disable datalabels for line chart
      },
      legend: {
        display: true,
        position: 'bottom',
        align: 'start',
        labels: {
          padding: 15,
          font: {
            size: 12,
          },
          usePointStyle: true,
        },
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
            const formatted = formatCurrency(value);
            const label = context.dataset.label;

            const prefix = label === 'Total Portfolio' ? '  ' : '';
            return `${prefix}${label}: ${formatted.integer}.${formatted.decimal}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value) => {
            const formatted = formatCurrency(value);
            return `${formatted.integer}.${formatted.decimal}`;
          },
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
            <span className="value">
              <FormattedNumber value={parseFloat(currentValue)} currency decimals={2} />
            </span>
            <span className={`change ${change >= 0 ? 'positive' : 'negative'}`}>
              {change >= 0 ? '+' : ''}
              <FormattedNumber value={Math.abs(change)} currency decimals={2} />
              {' '}({change >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
            </span>
          </div>
          {avgMonthlyIncrement !== null && avgMonthlyIncrement !== undefined && (
            <div className="monthly-average">
              <span className="label">Monthly Avg Value Increase: </span>
              <span className={`value ${parseFloat(avgMonthlyIncrement) >= 0 ? 'positive' : 'negative'}`}>
                {parseFloat(avgMonthlyIncrement) >= 0 ? '+' : ''}
                <FormattedNumber value={Math.abs(parseFloat(avgMonthlyIncrement))} currency decimals={2} />
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
