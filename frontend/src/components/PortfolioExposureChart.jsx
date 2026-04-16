import { useState, useMemo } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { generateChartColors } from '../constants/chartColors';
import './PortfolioExposureChart.css';

ChartJS.register(ArcElement, Tooltip, Legend);

const TABS = [
  { key: 'by_country', label: 'Country' },
  { key: 'by_sector', label: 'Sector' },
  { key: 'by_currency', label: 'Currency' },
  { key: 'by_ticker', label: 'Ticker' },
];

const OTHER_THRESHOLD = 0.01;

function PortfolioExposureChart({ breakdowns, holdings, isinNames = {} }) {
  const [activeTab, setActiveTab] = useState('by_country');
  const [excludedIsins, setExcludedIsins] = useState(new Set());
  const [filterOpen, setFilterOpen] = useState(false);

  const availableIsins = useMemo(() => {
    return holdings
      .map(h => ({
        isin: h.isin,
        name: isinNames[h.isin] || h.isin,
        hasBreakdown: !!breakdowns[h.isin],
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [holdings, breakdowns, isinNames]);

  const toggleIsin = (isin) => {
    setExcludedIsins(prev => {
      const next = new Set(prev);
      if (next.has(isin)) {
        next.delete(isin);
      } else {
        next.add(isin);
      }
      return next;
    });
  };

  const filteredHoldings = holdings.filter(h => !excludedIsins.has(h.isin));

  const totalValue = filteredHoldings.reduce((sum, h) => {
    const val = parseFloat(h.current_value) || 0;
    return sum + val;
  }, 0);

  if (totalValue === 0 || Object.keys(breakdowns).length === 0) {
    return (
      <div className="exposure-chart-container">
        <h3>Portfolio Exposure</h3>
        <div className="exposure-no-data">
          No breakdown data available. Ensure position values are set for your holdings.
        </div>
      </div>
    );
  }

  const merged = {};
  const noBreakdownWeight = {};

  filteredHoldings.forEach(holding => {
    const bd = breakdowns[holding.isin];
    const weight = (parseFloat(holding.current_value) || 0) / totalValue;
    if (weight <= 0) return;

    if (!bd) {
      const name = isinNames[holding.isin] || holding.isin;
      noBreakdownWeight[name] = (noBreakdownWeight[name] || 0) + weight;
      return;
    }

    const entries = bd[activeTab] || [];
    entries.forEach(entry => {
      const name = entry.name;
      merged[name] = (merged[name] || 0) + entry.weight_pct * weight;
    });
  });

  let items = Object.entries(merged)
    .map(([name, weight]) => ({ name, weight }))
    .sort((a, b) => b.weight - a.weight);

  const otherWeight = items
    .filter(i => i.weight < OTHER_THRESHOLD)
    .reduce((sum, i) => sum + i.weight, 0);

  items = items.filter(i => i.weight >= OTHER_THRESHOLD);
  if (otherWeight > 0) {
    items.push({ name: 'Other', weight: otherWeight });
  }

  Object.entries(noBreakdownWeight).forEach(([name, weight]) => {
    items.push({ name, weight });
  });

  const totalWeight = items.reduce((s, i) => s + i.weight, 0);
  const chartItems = items.map(i => ({
    ...i,
    percentage: totalWeight > 0 ? (i.weight / totalWeight) * 100 : 0,
  }));

  const { colors, borderColors } = generateChartColors(chartItems, null);

  const data = {
    labels: chartItems.map(i => i.name),
    datasets: [
      {
        label: 'Portfolio Exposure',
        data: chartItems.map(i => i.weight),
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
        display: false,
      },
      legend: {
        position: 'right',
        labels: {
          padding: 15,
          font: {
            size: 12,
          },
          generateLabels: (chart) => {
            const d = chart.data;
            if (d.labels.length && d.datasets.length) {
              return d.labels.map((label, i) => ({
                text: `${label} (${chartItems[i].percentage.toFixed(1)}%)`,
                fillStyle: d.datasets[0].backgroundColor[i],
                strokeStyle: d.datasets[0].borderColor[i],
                lineWidth: d.datasets[0].borderWidth,
                hidden: false,
                index: i,
              }));
            }
            return [];
          },
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const item = chartItems[context.dataIndex];
            return [
              `${item.name}`,
              `Weight: ${item.percentage.toFixed(2)}%`,
            ];
          },
        },
      },
    },
  };

  return (
    <div className="exposure-chart-container">
      <div className="exposure-header">
        <h3>Portfolio Exposure</h3>
        {availableIsins.length > 1 && (
          <div className="exposure-filter">
            <button
              className={`exposure-filter-btn ${excludedIsins.size > 0 ? 'has-filter' : ''}`}
              onClick={() => setFilterOpen(prev => !prev)}
            >
              Filter ETFs {excludedIsins.size > 0 && `(${availableIsins.length - excludedIsins.size}/${availableIsins.length})`}
            </button>
            {filterOpen && (
              <div className="exposure-filter-dropdown">
                <div className="exposure-filter-actions">
                  <button onClick={() => setExcludedIsins(new Set())}>Select All</button>
                  <button onClick={() => setExcludedIsins(new Set(availableIsins.map(i => i.isin)))}>Deselect All</button>
                </div>
                {availableIsins.map(({ isin, name, hasBreakdown }) => (
                  <label key={isin} className={`exposure-filter-item ${!hasBreakdown ? 'no-breakdown' : ''}`}>
                    <input
                      type="checkbox"
                      checked={!excludedIsins.has(isin)}
                      onChange={() => toggleIsin(isin)}
                    />
                    <span className="exposure-filter-name" title={isin}>{name}</span>
                    <span className="exposure-filter-isin">{isin}{!hasBreakdown && ' (no data)'}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      <div className="exposure-tabs">
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={`exposure-tab ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="exposure-chart-wrapper">
        <Pie data={data} options={options} />
      </div>
    </div>
  );
}

export default PortfolioExposureChart;
