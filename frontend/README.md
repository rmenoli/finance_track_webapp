# ETF Portfolio Tracker - Frontend

React frontend for the ETF Portfolio Tracker application. Built with Vite for fast development and hot module replacement.

## Tech Stack

- **React 18**: Modern React with hooks
- **Vite**: Fast build tool and dev server
- **React Router v6**: Client-side routing
- **Chart.js**: Interactive charts and visualizations
- **CSS**: Component-scoped styling
- **Fetch API**: HTTP requests to backend

## Getting Started

### Prerequisites

- Node.js 18+ (Node.js 20+ recommended)
- npm (comes with Node.js)
- Backend server running on http://localhost:8000

### Installation

```bash
# Install dependencies
npm install
```

### Development

```bash
# Start development server (port 3000)
npm run dev
```

The application will be available at http://localhost:3000

**Features during development:**
- Hot Module Replacement (HMR) - instant updates on save
- Automatic proxy to backend API at port 8000
- Fast refresh for React components

### Build for Production

```bash
# Create optimized production build
npm run build

# Preview production build locally
npm run preview
```

The production build will be in the `dist/` directory.

## Project Structure

```
src/
├── components/                        # Reusable React components
│   ├── Layout.jsx/css                # Main layout with navigation
│   ├── Navigation.jsx/css            # Navigation bar
│   ├── TransactionForm.jsx/css       # Add/edit transaction form
│   ├── TransactionList.jsx/css       # Transaction table
│   ├── DashboardHoldingsTable.jsx/css # Holdings table for dashboard
│   ├── HoldingsDistributionChart.jsx/css # Portfolio distribution pie chart
│   ├── ClosedPositionsTable.jsx/css  # Closed positions table
│   ├── ISINMetadataForm.jsx/css      # ISIN metadata form
│   ├── ISINMetadataList.jsx/css      # ISIN metadata list
│   └── PortfolioSummary.jsx/css      # Dashboard summary cards
├── pages/                             # Page-level components
│   ├── InvestmentDashboard.jsx/css   # Portfolio overview page
│   ├── Transactions.jsx/css          # Transaction management
│   └── AddTransaction.jsx/css        # Add/edit transaction page
├── services/                          # API client
│   └── api.js                        # Backend API client
├── App.jsx                            # Main app with routing
├── main.jsx                           # Application entry point
├── App.css                            # App-level styles
└── index.css                          # Global styles and utilities
```

## Features

### Pages

1. **Investment Dashboard** (`/`)
   - Portfolio summary with key metrics (total value, invested amount, realized gains)
   - Portfolio distribution pie chart showing asset allocation by percentage
   - Current holdings table with asset names and detailed position information
   - Closed positions table showing realized gains/losses
   - Average cost and total cost per holding
   - Interactive tooltips with asset values and percentages
   - Comprehensive portfolio overview

2. **Transactions** (`/transactions`)
   - Full transaction list with all details
   - Filter by ISIN, broker, type, date range
   - Edit and delete transactions
   - Navigation to add new transaction

3. **Add/Edit Transaction** (`/transactions/add`, `/transactions/edit/:id`)
   - Form for creating and editing transactions
   - Client-side validation matching backend rules
   - Success/error feedback

### Components

- **Layout**: Main wrapper with navigation
- **Navigation**: Nav links for all pages
- **TransactionForm**: Reusable form for add/edit transactions
- **TransactionList**: Table view of all transactions with filters
- **DashboardHoldingsTable**: Detailed holdings table with asset names and editable position values
- **HoldingsDistributionChart**: Pie chart showing portfolio distribution by asset with percentages (uses Chart.js)
- **ClosedPositionsTable**: Table showing closed positions with realized P/L
- **ISINMetadataForm**: Form for creating/editing ISIN metadata (name and type)
- **ISINMetadataList**: Table displaying ISIN metadata with type-based filtering
- **PortfolioSummary**: Dashboard summary cards showing portfolio metrics

### Visualization Features

- **Portfolio Distribution Chart**:
  - Interactive pie chart built with Chart.js and react-chartjs-2
  - Shows percentage allocation of each asset in the portfolio
  - Displays asset names (from ISIN metadata) in legend with percentages
  - Interactive tooltips showing asset name, current value, and percentage share
  - Auto-updates when position values are modified
  - Color-coded segments for easy visual distinction
  - Responsive design adapting to different screen sizes

- **Asset Name Display**:
  - Asset names from ISIN metadata displayed above ISIN codes in holdings tables
  - Bold asset names for easy recognition
  - Italic ISIN codes for secondary information
  - Seamless integration with ISIN metadata management

### Validation

Client-side validation matches backend rules:
- **ISIN**: 12 characters (2 letters + 9 alphanumeric + 1 digit)
- **Date**: Cannot be in future
- **Units**: Must be greater than 0
- **Price per unit**: Must be greater than 0
- **Fee**: Must be greater than or equal to 0
- **Transaction type**: Must be BUY or SELL

## Configuration

### Environment Variables

**`.env.development`** (development mode):
```env
VITE_API_URL=http://localhost:8000/api/v1
```

**`.env.production`** (production build):
```env
VITE_API_URL=/api/v1
```

Access in code with `import.meta.env.VITE_API_URL`

### Vite Proxy

The Vite dev server proxies `/api` requests to the backend (configured in `vite.config.js`):

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    }
  }
}
```

This avoids CORS issues during development.

## API Client

All backend communication goes through `src/services/api.js`.

### Transactions API

```javascript
import { transactionsAPI } from './services/api';

// Get all transactions with optional filters
const transactions = await transactionsAPI.getAll({
  isin: 'IE00B4L5Y983',
  broker: 'Interactive Brokers',
  transaction_type: 'BUY',
  start_date: '2025-01-01',
  end_date: '2025-12-31',
  skip: 0,
  limit: 50
});

// Get single transaction
const transaction = await transactionsAPI.getById(1);

// Create transaction
const newTransaction = await transactionsAPI.create({
  date: '2025-01-15',
  isin: 'IE00B4L5Y983',
  broker: 'Interactive Brokers',
  fee: 1.50,
  price_per_unit: 450.25,
  units: 10.0,
  transaction_type: 'BUY'
});

// Update transaction
await transactionsAPI.update(1, { fee: 2.00 });

// Delete transaction
await transactionsAPI.delete(1);
```

### Analytics API

```javascript
import { analyticsAPI } from './services/api';

// Get portfolio summary
const summary = await analyticsAPI.getPortfolioSummary();

// Get current holdings
const holdings = await analyticsAPI.getHoldings();

// Get all cost bases
const costBases = await analyticsAPI.getAllCostBases();

// Get cost basis for specific ISIN
const costBasis = await analyticsAPI.getCostBasis('IE00B4L5Y983');

// Get realized gains (all or filtered by ISIN)
const gains = await analyticsAPI.getRealizedGains();
const gainsForIsin = await analyticsAPI.getRealizedGains('IE00B4L5Y983');
```

## Styling

### Global Styles

Global utility classes in `index.css`:

**Buttons**:
- `.btn` - Base button style
- `.btn-primary` - Primary action button (blue)
- `.btn-secondary` - Secondary action button (gray)

**Inputs**:
- `.input` - Base input style
- `.input-error` - Error state for inputs

**Tables**:
- `.table` - Base table style
- `.table-container` - Responsive table wrapper

**Badges**:
- `.badge` - Base badge style
- `.badge-buy` - Green badge for BUY transactions
- `.badge-sell` - Red badge for SELL transactions

**Utility**:
- `.loading` - Loading state container
- `.error` - Error state container

### Component Styles

Each component has its own CSS file imported directly in the component:

```javascript
import './MyComponent.css';
```

## Development Guidelines

### Adding a New Page

1. Create page component: `src/pages/MyPage.jsx`
2. Create styles: `src/pages/MyPage.css`
3. Add route in `src/App.jsx`
4. Add navigation link in `src/components/Navigation.jsx`

### Adding a New Component

1. Create component: `src/components/MyComponent.jsx`
2. Create styles: `src/components/MyComponent.css`
3. Import and use in pages

### Styling Best Practices

- Use component-scoped CSS files
- Use global utility classes from `index.css` when applicable
- Follow existing color scheme (blues, greens, reds)
- Maintain responsive design with mobile breakpoints
- Test on mobile viewports (< 768px)

### Form Handling

- Always validate client-side before API calls
- Match backend validation rules exactly
- Display inline error messages
- Show loading states during submission
- Disable submit buttons to prevent double-clicks
- Navigate or show success feedback after successful operations

## Troubleshooting

### Port Already in Use

If port 3000 is in use:

```bash
# Kill the process
lsof -i :3000
kill -9 <PID>

# Or use different port
npm run dev -- --port 3001
```

### Backend Connection Issues

Ensure backend is running at http://localhost:8000:

```bash
# In backend directory
cd backend
uv run uvicorn app.main:app --reload
```

Check backend health: http://localhost:8000/health

### CORS Issues

The Vite proxy should handle CORS during development. If you still have issues:

1. Check backend `.env` includes frontend origin:
   ```env
   CORS_ORIGINS=["http://localhost:3000"]
   ```

2. Restart both servers

### Build Issues

Clear node_modules and reinstall:

```bash
rm -rf node_modules package-lock.json
npm install
```

## Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint (if configured)
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## License

This project is licensed under the MIT License.

---

**Part of the ETF Portfolio Tracker application**. See the [main README](../README.md) for full project documentation.
