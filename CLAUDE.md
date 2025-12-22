# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ETF Portfolio Tracker - Full-stack web application for tracking ETF transactions with automatic cost basis calculations using the average cost method. Single-user system with no authentication.

**Tech Stack**:
- **Backend**: FastAPI, SQLAlchemy 2.0, SQLite, Alembic, Pydantic 2.x, UV package manager
- **Frontend**: React 18, Vite, React Router v6, CSS (component-scoped)

**Documentation Structure**:
- **README.md** (root): High-level overview, quick start, and project status
- **backend/README.md**: Comprehensive backend documentation (architecture, API, testing, deployment)
- **frontend/README.md**: Frontend-specific documentation (components, pages, styling)
- **CLAUDE.md** (this file): Essential commands and development guidance for Claude Code

## Essential Commands

### Development Servers

**Backend** (Terminal 1):
```bash
cd backend

# Start with auto-reload (development)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode with workers
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Frontend** (Terminal 2):
```bash
cd frontend

# Development server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

**Access URLs**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**IMPORTANT**: Backend MUST run on port 8000 with `--host 0.0.0.0` for frontend to connect properly.

**Quick Check**:
```bash
# Backend health check
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# Frontend should load
curl -I http://localhost:3000
# Should return: HTTP/1.1 200 OK
```

### Dependencies

**Backend**:
```bash
cd backend

# Install all dependencies including dev tools
uv sync --all-extras

# Install production dependencies only
uv sync
```

**Frontend**:
```bash
cd frontend

# Install all dependencies
npm install

# Add new dependency
npm install <package-name>

# Add dev dependency
npm install -D <package-name>
```

**Key Frontend Dependencies**:
- `chart.js` (v4.5.1) - Chart library for data visualization
- `react-chartjs-2` (v5.3.1) - React wrapper for Chart.js
- `react-router-dom` - Client-side routing
- `react` / `react-dom` - React framework

### Database Migrations
```bash
cd backend

# Create migration after model changes
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history

# Check current revision
uv run alembic current
```

### Code Quality
```bash
cd backend

# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Logging

**Enable different log levels:**
```bash
cd backend

# Default INFO level (recommended)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Debug level for troubleshooting
LOG_LEVEL=DEBUG uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Human-readable text format for local development
LOG_FORMAT=text uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Log output includes:**
- HTTP requests/responses with timing and request IDs
- Audit trail for all CREATE/UPDATE/DELETE operations
- Exception tracking with full context
- Performance metrics for slow operations (>100ms)

All logs are structured JSON for easy parsing and filtering.

### Testing
```bash
cd backend

# Run all tests (254 tests, 95% coverage)
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=app --cov-report=term-missing --cov-report=html

# Run specific test file
uv run pytest tests/test_transaction_service.py -v

# Run specific test class
uv run pytest tests/test_api_transactions.py::TestTransactionAPI -v

# Run specific test
uv run pytest tests/test_cost_basis_service.py::TestCostBasisService::test_calculate_cost_basis_single_buy -v
```

### Database Inspection
```bash
# Connect to SQLite database
sqlite3 backend/portfolio.db

# Inside sqlite3:
.tables                    # List tables
.schema transactions       # View schema
SELECT * FROM transactions; # Query data
.quit                      # Exit
```

## Project Structure

```
finance_track_webapp/
├── backend/                    # Backend application
│   ├── app/                   # FastAPI application
│   │   ├── main.py            # Application entry point
│   │   ├── config.py          # Settings (Pydantic Settings)
│   │   ├── database.py        # Database connection and session
│   │   ├── logging_config.py  # Logging configuration and setup
│   │   ├── constants.py       # Constants and enums
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── models/            # SQLAlchemy models (database layer)
│   │   │   ├── transaction.py
│   │   │   ├── position_value.py
│   │   │   └── isin_metadata.py
│   │   ├── schemas/           # Pydantic schemas (validation layer)
│   │   │   ├── transaction.py
│   │   │   ├── analytics.py
│   │   │   ├── position_value.py
│   │   │   └── isin_metadata.py
│   │   ├── routers/           # API route handlers (HTTP layer)
│   │   │   ├── transactions.py
│   │   │   ├── analytics.py
│   │   │   ├── position_values.py
│   │   │   └── isin_metadata.py
│   │   └── services/          # Business logic (service layer)
│   │       ├── transaction_service.py
│   │       ├── cost_basis_service.py
│   │       ├── position_value_service.py
│   │       └── isin_metadata_service.py
│   ├── alembic/               # Database migrations
│   │   ├── versions/          # Migration files
│   │   ├── env.py             # Alembic environment
│   │   └── script.py.mako     # Migration template
│   ├── tests/                 # Test suite (95% coverage, 254 tests)
│   │   ├── conftest.py       # Test fixtures
│   │   ├── test_transaction_service.py
│   │   ├── test_cost_basis_service.py
│   │   ├── test_position_value_service.py
│   │   ├── test_isin_metadata_service.py
│   │   ├── test_api_transactions.py
│   │   ├── test_api_analytics.py
│   │   ├── test_api_position_values.py
│   │   ├── test_api_isin_metadata.py
│   │   ├── test_api_snapshots.py
│   │   ├── test_position_value_cleanup.py
│   │   └── test_schemas.py
│   ├── .env                   # Environment variables (gitignored)
│   ├── .env.example          # Environment template
│   ├── alembic.ini            # Alembic configuration
│   ├── pyproject.toml         # Dependencies and project metadata
│   ├── uv.lock                # Dependency lock file
│   ├── portfolio.db           # SQLite database (gitignored)
│   └── README.md             # 📖 Comprehensive backend documentation
│
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   │   ├── Layout.jsx     # Main layout wrapper
│   │   │   ├── Navigation.jsx # Navigation bar
│   │   │   ├── TransactionForm.jsx    # Add/edit transaction form
│   │   │   ├── TransactionList.jsx    # Transaction table
│   │   │   ├── ISINMetadataForm.jsx   # Add/edit ISIN metadata form
│   │   │   ├── ISINMetadataList.jsx   # ISIN metadata table
│   │   │   ├── DashboardHoldingsTable.jsx  # Holdings table for dashboard
│   │   │   ├── HoldingsDistributionChart.jsx # Portfolio distribution pie chart (Chart.js)
│   │   │   ├── ClosedPositionsTable.jsx    # Closed positions table
│   │   │   ├── SnapshotValueChart.jsx      # Time-series area chart with growth tracking
│   │   │   ├── SnapshotsTable.jsx          # Snapshots table
│   │   │   ├── SnapshotAssetTypeChart.jsx  # Compact pie chart for asset distribution
│   │   │   ├── OtherAssetsTable.jsx        # Other assets editable table
│   │   │   ├── OtherAssetsDistributionChart.jsx # Other assets pie chart
│   │   │   └── PortfolioSummary.jsx   # Dashboard summary cards
│   │   ├── pages/             # Page-level components
│   │   │   ├── InvestmentDashboard.jsx  # Portfolio overview page
│   │   │   ├── Transactions.jsx         # Transaction management
│   │   │   ├── AddTransaction.jsx       # Add/edit transaction page
│   │   │   ├── ISINMetadata.jsx         # ISIN metadata management
│   │   │   ├── AddISINMetadata.jsx      # Add/edit ISIN metadata page
│   │   │   ├── OtherAssets.jsx          # Other assets tracking page
│   │   │   └── Snapshots.jsx            # Snapshots with growth tracking
│   │   ├── constants/         # Application constants
│   │   │   ├── otherAssets.js # Other asset types and accounts
│   │   │   └── chartColors.js # Centralized chart color configuration
│   │   ├── services/          # API client
│   │   │   └── api.js         # Fetch-based API client (transactions, analytics, positionValues, isinMetadata)
│   │   ├── utils/             # Utility functions
│   │   │   └── numberFormat.js # Number formatting utilities
│   │   ├── App.jsx            # Main app with routing
│   │   └── main.jsx           # Entry point
│   ├── .env.development       # Development environment
│   ├── .env.production        # Production environment
│   ├── package.json           # Node dependencies
│   ├── vite.config.js         # Vite configuration
│   └── README.md             # 📖 Frontend documentation
│
├── .gitignore                 # Git ignore patterns
├── CLAUDE.md                  # This file (development guidance)
└── README.md                  # High-level overview
```

## Architecture

### Three-Layer Architecture

The backend follows a clean three-layer architecture:

```
┌─────────────┐
│   Routers   │  ← HTTP layer (API endpoints, request/response)
└─────────────┘
      ↓
┌─────────────┐
│  Services   │  ← Business logic (calculations, validations)
└─────────────┘
      ↓
┌─────────────┐
│   Models    │  ← Data layer (database, SQLAlchemy ORM)
└─────────────┘
```

**1. Routers** (`backend/app/routers/`):
- API endpoints and HTTP concerns
- Request validation via Pydantic
- No business logic - thin wrappers around services

**2. Services** (`backend/app/services/`):
- Business logic and calculations
- No HTTP knowledge (pure Python functions)
- Testable in isolation

**3. Models** (`backend/app/models/`):
- Database schema via SQLAlchemy ORM
- Database constraints and indexes

**Key Patterns**:
- **Dependency Injection**: Database sessions via FastAPI's `Depends(get_db)`
- **Schema Separation**: `models/` (SQLAlchemy) vs `schemas/` (Pydantic)
- **Service Layer Pattern**: All business logic in `services/`

### Cost Basis Calculation Logic

**Average Cost Method** (in `backend/app/services/cost_basis_service.py`):

**BUY transactions**:
```python
total_cost += (price_per_unit × units) + fee
total_units += units
average_cost = total_cost / total_units
```

**SELL transactions**:
```python
proportion = units_sold / total_units
cost_removed = total_cost × proportion
realized_gain = (sell_price × units - fee) - cost_removed
total_cost -= cost_removed
total_units -= units_sold
```

**Critical**: Process transactions chronologically (`ORDER BY date ASC`) for accurate calculations.

### Profit/Loss (P/L) Calculation

**Important**: All P/L calculations are performed **on the backend** using Python `Decimal` for financial precision. The frontend displays these pre-calculated values.

**Backend P/L Calculation** (in `backend/app/services/cost_basis_service.py`):

For **open positions** (with current value entered):
```python
# P/L without fees
total_cost_without_fees = total_cost - total_gains_without_fees
absolute_pl_without_fees = current_value - total_cost_without_fees
percentage_pl_without_fees = (absolute_pl_without_fees / total_cost_without_fees * 100)

# P/L with fees
total_cost_with_fees = total_cost_without_fees + total_fees
absolute_pl_with_fees = current_value - total_cost_with_fees
percentage_pl_with_fees = (absolute_pl_with_fees / total_cost_with_fees * 100)
```

For **closed positions** (fully sold):
```python
# Realized P/L without fees
absolute_pl_without_fees = total_gains_without_fees - total_cost_without_fees
percentage_pl_without_fees = (absolute_pl_without_fees / total_cost_without_fees * 100)

# Realized P/L with fees
absolute_pl_with_fees = absolute_pl_without_fees - total_fees
percentage_pl_with_fees = (absolute_pl_with_fees / total_cost_with_fees * 100)
```

**Frontend Behavior**:
- Holdings table displays P/L from backend API response
- Shows "N/A" when no position value has been entered
- Users can manually enter position values, which triggers backend recalculation
- All financial calculations use backend `Decimal` type (no floating-point errors)

### Financial Precision

**Always use `Decimal`** for monetary values, never `float`:

```python
from decimal import Decimal

# Correct
fee = Decimal("1.50")

# Wrong - floating point errors
fee = 1.50  # Never use float for money
```

Database columns are `Numeric(10, 2)` for fees, `Numeric(10, 4)` for prices and units.

### Computed Fields Pattern

**Backend Computed Fields**: The application uses Pydantic's `@computed_field` decorator to add calculated values to API responses without storing them in the database. This ensures all financial calculations happen on the backend using `Decimal` precision.

**Transaction Response Computed Fields** (`backend/app/schemas/transaction.py`):
- `total_without_fees: Decimal` - Calculated as `units × price_per_unit`
- `total_with_fees: Decimal` - Calculated as `total_without_fees + fee`

**Holdings Response Computed Fields** (`backend/app/schemas/analytics.py`):
- `net_buy_in_cost: Decimal` - Net cost basis (total_cost_without_fees - total_gains_without_fees)
- `net_buy_in_cost_per_unit: Optional[Decimal]` - Per-unit net cost (returns None if no units)
- `current_price_per_unit: Optional[Decimal]` - Current market price per unit (returns None if no current_value)

**Benefits**:
- Single source of truth for calculations
- No database migrations required for new computed fields
- Frontend becomes pure presentation layer
- All calculations tested in backend with `Decimal` precision

## API Structure

All routes prefixed with `/api/v1`:

**Transactions**:
- `POST /transactions` - Create
- `GET /transactions` - List with filters (isin, broker, type, date range)
- `GET /transactions/{id}` - Get one
- `PUT /transactions/{id}` - Update
- `DELETE /transactions/{id}` - Delete
- **Note**: All transaction responses include computed fields: `total_without_fees`, `total_with_fees`

**Analytics**:
- `GET /analytics/portfolio-summary` - Complete portfolio overview (includes holdings, total invested, total fees)
- **Note**: Holdings responses include computed fields: `net_buy_in_cost`, `net_buy_in_cost_per_unit`, `current_price_per_unit`

**Position Values**:
- `POST /position-values` - Create or update (UPSERT by ISIN)
- `GET /position-values` - List all position values
- `GET /position-values/{isin}` - Get by ISIN
- `DELETE /position-values/{isin}` - Delete by ISIN

**ISIN Metadata**:
- `POST /isin-metadata` - Create ISIN metadata (name and type)
- `POST /isin-metadata/upsert` - Create or update (UPSERT by ISIN)
- `GET /isin-metadata?type={type}` - List all with optional type filter
- `GET /isin-metadata/{isin}` - Get by ISIN
- `PUT /isin-metadata/{isin}` - Update metadata
- `DELETE /isin-metadata/{isin}` - Delete by ISIN

**Other Assets**:
- `POST /other-assets` - Create or update (UPSERT by asset_type and asset_detail)
- `GET /other-assets?include_investments={bool}` - List all with optional synthetic investments row
- `GET /other-assets/{type}?asset_detail={detail}` - Get by type and optional detail
- `DELETE /other-assets/{type}?asset_detail={detail}` - Delete by type and optional detail

**Asset Snapshots**:
- `POST /snapshots` - Create snapshot of current asset state (investments + other assets)
- `GET /snapshots` - List all snapshots with optional filters (date range, asset type)
- `GET /snapshots/summary` - Get aggregated summary statistics per snapshot date with growth tracking
- `GET /snapshots/{snapshot_date}` - Get all assets for specific snapshot date
- `DELETE /snapshots/{snapshot_date}` - Delete all snapshots for specific date
- **Note**: Each asset stored separately (no aggregation). Captures exchange rate for historical accuracy.
- **Summary endpoint** returns:
  - Total portfolio value in EUR for each snapshot date
  - Currency breakdown (EUR/CZK native values)
  - Asset type breakdown (EUR-converted values)
  - **Growth tracking**: `absolute_change_from_oldest` and `percentage_change_from_oldest` calculated from oldest snapshot in filtered dataset
  - Ordered by date DESC (most recent first)

Interactive docs: http://localhost:8000/docs (Swagger UI)

## Common Development Scenarios

### Adding a New Field to Transaction

1. Update `backend/app/models/transaction.py` (SQLAlchemy model)
2. Update `backend/app/schemas/transaction.py` (Pydantic schemas)
3. Generate migration: `cd backend && uv run alembic revision --autogenerate -m "add_field_name"`
4. Review generated migration in `backend/alembic/versions/`
5. Apply: `cd backend && uv run alembic upgrade head`
6. Update tests as needed

### Adding a New Analytics Endpoint

1. Add calculation function in `backend/app/services/cost_basis_service.py`
2. Add response schema in `backend/app/schemas/analytics.py`
3. Add route in `backend/app/routers/analytics.py`
4. Write tests
5. Use existing patterns (dependency injection, error handling)

### Modifying Cost Basis Logic

All cost basis calculations are in `backend/app/services/cost_basis_service.py`:
- `calculate_cost_basis()`: Average cost for one ISIN
- `calculate_current_holdings()`: All holdings
- `get_portfolio_summary()`: Aggregates total invested, total fees, and holdings

When modifying, maintain chronological transaction processing (ORDER BY date).

### Position Value Tracking

**Purpose**: Store manually entered current market values for positions that persist across page refreshes.

**Key Files**:
- Model: `backend/app/models/position_value.py` - One row per ISIN with UNIQUE constraint
- Schemas: `backend/app/schemas/position_value.py` - Create, Response, ListResponse
- Service: `backend/app/services/position_value_service.py` - UPSERT logic, CRUD operations
- Router: `backend/app/routers/position_values.py` - API endpoints
- Frontend: `frontend/src/components/DashboardHoldingsTable.jsx` - Load/save on mount/blur

**UPSERT Pattern**: POST to `/position-values` creates new row if ISIN doesn't exist, updates if it does. Only one current value per ISIN stored. `updated_at` timestamp auto-updates on modification.

**Frontend Behavior**: Component loads all position values on mount, converts to map `{ISIN: value}`, saves to backend on blur/Enter with validation (must be > 0).

## Frontend Architecture

**Pattern**: Functional components with hooks (useState, useEffect)

**No state management library**: Simple useState/useEffect for all state (adequate for single-user app)

**Current Pages**:
1. **Investment Dashboard** (`/`) - Portfolio summary, portfolio distribution chart, holdings table, key metrics
2. **Transactions** (`/transactions`) - Full transaction list with filters and CRUD operations
3. **Add/Edit Transaction** (`/transactions/add`, `/transactions/edit/:id`) - Transaction form
4. **ISIN Metadata** (`/isin-metadata`) - ISIN metadata list with type filtering and CRUD operations
5. **Add/Edit ISIN Metadata** (`/isin-metadata/add`, `/isin-metadata/edit/:isin`) - ISIN metadata form
6. **Other Assets** (`/other-assets`) - Track non-ETF holdings with multi-currency support and distribution chart

**Key Components**:
- **Layout**: Main wrapper with navigation for all pages
- **Navigation**: Navigation bar with route links (Dashboard, Transactions, ISIN Metadata, Other Assets)
- **TransactionForm**: Reusable form for creating/editing transactions
- **TransactionList**: Table view with filters and actions
- **OtherAssetsTable**: Editable table for tracking non-ETF assets with multi-currency support
- **OtherAssetsDistributionChart**: Pie chart visualization for other assets distribution
- **ISINMetadataForm**: Reusable form for creating/editing ISIN metadata (ISIN, name, type)
- **ISINMetadataList**: Table view with type badges and actions
- **DashboardHoldingsTable**: Detailed holdings display with asset names above ISIN codes
- **HoldingsDistributionChart**: Interactive pie chart showing portfolio distribution by asset (Chart.js)
- **ClosedPositionsTable**: Table showing closed positions with realized P/L
- **PortfolioSummary**: Summary cards showing portfolio metrics

**Visualization Features**:
- **Portfolio Distribution Chart**: Interactive pie chart built with Chart.js showing percentage allocation of each asset
- **Asset Name Display**: ISIN names from metadata displayed above ISIN codes in holdings tables (bold names, italic ISINs)
- **Interactive Tooltips**: Chart tooltips show asset name, current value, and percentage share
- **Auto-updates**: Chart refreshes when position values change
- **Consistent Colors**: Centralized color configuration ensures same asset type has same color across all charts

**Chart Color System** (`frontend/src/constants/chartColors.js`):
- **Centralized Configuration**: Single source of truth for all chart colors
- **Asset Type Mapping**: Pre-defined colors for known asset types (investments=blue, crypto=orange, etc.)
- **Fallback Colors**: Dynamic color generation for unmapped items using golden angle algorithm
- **Benefits**: Consistency (same asset = same color), maintainability (one place to update), predictability (users learn associations)
- **Usage**: `import { generateChartColors } from '../constants/chartColors'` then call `generateChartColors(data, 'assetType')`
- **Components**: Used by SnapshotValueChart, SnapshotAssetTypeChart, OtherAssetsDistributionChart

**Routing**: React Router v6 with nested routes
- Layout component wraps all pages
- Routes: `/`, `/transactions`, `/transactions/add`, `/transactions/edit/:id`, `/isin-metadata`, `/isin-metadata/add`, `/isin-metadata/edit/:isin`

**API Client** (`frontend/src/services/api.js`):
- `transactionsAPI`: CRUD operations for transactions
- `analyticsAPI`: Portfolio analytics (summary with holdings, total invested, total fees)
- `positionValuesAPI`: Manual position value tracking (UPSERT, list, get, delete)
- `isinMetadataAPI`: ISIN metadata management (CRUD, UPSERT, type filtering)
- `snapshotsAPI`: Asset snapshot operations (create, getSummary with date filters)

**Styling**: Component-scoped CSS files with global utility classes in `index.css`

**Vite Proxy**: Frontend proxies `/api/*` to backend during development (avoids CORS issues)

## Important Constraints

1. **No Authentication**: Single-user system, no user model or auth
2. **SQLite Only**: Not designed for high concurrency (but WAL mode enabled for local dev)
3. **Synchronous**: Using sync SQLAlchemy (adequate for single user)
4. **Date Validation**: Transaction dates cannot be in the future
5. **No Soft Deletes**: Transactions are hard-deleted
6. **Financial Precision**: Always use Decimal for money, never float

## Validation Rules

**Transaction Schema**:
- **ISIN**: Exactly 12 characters (2 letters + 9 alphanumeric + 1 digit)
- **Date**: Cannot be in future
- **Units**: Must be > 0
- **Price per unit**: Must be > 0
- **Fee**: Must be >= 0
- **Transaction type**: "BUY" or "SELL"

**Position Value Schema**:
- **ISIN**: 1-12 characters (no format validation - allows any string)
- **Current value**: Must be > 0

**ISIN Metadata Schema**:
- **ISIN**: Exactly 12 characters (2 letters + 9 alphanumeric + 1 digit), auto-uppercase
- **Name**: 1-255 characters, whitespace stripped
- **Type**: Must be one of `STOCK`, `BOND`, or `REAL_ASSET`

ISIN format validation in `backend/app/constants.py`: `ISIN_PATTERN`

## Configuration

**Backend Environment Variables** (`.env` in `backend/`):
```env
DATABASE_URL=sqlite:///./portfolio.db
API_V1_PREFIX=/api/v1
PROJECT_NAME=ETF Portfolio Tracker
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
```

**Frontend Environment Variables**:
- `.env.development`: `VITE_API_URL=http://localhost:8000/api/v1`
- `.env.production`: `VITE_API_URL=/api/v1`

## Testing

**Test Suite**: 254 tests, 95% coverage

**Test Structure**:
- `tests/conftest.py`: Fixtures for database and test client
- `tests/test_transaction_service.py`: Service layer (14 tests)
- `tests/test_cost_basis_service.py`: Cost basis calculations including P/L (22 tests)
- `tests/test_position_value_service.py`: Position value service (9 tests)
- `tests/test_other_asset_service.py`: Other asset service (15 tests)
- `tests/test_api_transactions.py`: Transaction API (20 tests)
- `tests/test_api_analytics.py`: Analytics API (3 tests)
- `tests/test_api_position_values.py`: Position values API (9 tests)
- `tests/test_api_other_assets.py`: Other assets API (15 tests)
- `tests/test_isin_metadata_service.py`: ISIN metadata service (15 tests)
- `tests/test_api_isin_metadata.py`: ISIN metadata API (20 tests)
- `tests/test_position_value_cleanup.py`: Position value cleanup (5 tests)
- `tests/test_schemas.py`: Pydantic validation (49 tests, includes OtherAssetSchemas)

**Key Test Patterns**:
- Database isolation via fixtures
- API testing with FastAPI TestClient
- Decimal precision for financial calculations
- Chronological transaction processing

## Troubleshooting

### Frontend "Failed to fetch" Error

**Common cause**: Backend not running on correct port or wrong host.

**Solution**:
```bash
# 1. Verify backend is running
curl http://localhost:8000/health

# 2. Check correct process on port 8000
lsof -i :8000

# 3. Start backend correctly
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Port Conflicts

```bash
# Find process on port
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Issues

```bash
cd backend

# Check current migration
uv run alembic current

# Apply migrations
uv run alembic upgrade head

# Reset database (destructive)
rm portfolio.db
uv run alembic upgrade head
```

### CORS Issues

Update `CORS_ORIGINS` in `backend/.env`:
```env
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

## Deployment Considerations

**Current Setup (Local Development)**:
- Backend: Uvicorn + SQLite
- Frontend: Vite dev server

**AWS Deployment (Future)**:
- Backend: ECS/Lambda/EC2 with RDS PostgreSQL
- Frontend: S3 + CloudFront or separate container
- Change only `DATABASE_URL` environment variable for PostgreSQL

**Containerization**:
- `backend/` directory becomes Docker build context
- `pyproject.toml` and `uv.lock` in backend/ for dependency installation
- See `backend/README.md` for Dockerfile example

## Migration Notes

When importing models in `backend/alembic/env.py`, use `# noqa: F401` to silence unused import warnings. This is required for autogenerate to detect models.

```python
from app.models.transaction import Transaction  # noqa: F401
```

## Additional Documentation

For detailed information, see:
- **Backend details**: `backend/README.md` (complete API docs, architecture, testing, deployment)
- **Frontend details**: `frontend/README.md` (component architecture, styling, API client)
- **Quick overview**: `README.md` (root, getting started guide, project status)

## Project Status Summary

**Current Version**: Development
**Test Coverage**: 95% (254 tests)
**Backend Endpoints**: 27 total (5 transaction, 1 analytics, 4 position values, 6 ISIN metadata, 4 other assets, 5 snapshots, 2 settings)
**Frontend Pages**: 7 (Investment Dashboard, Transactions, Add/Edit Transaction, ISIN Metadata, Add/Edit ISIN Metadata, Other Assets, Snapshots with Growth Tracking)
**Frontend Components**: 15 main components (Layout, Navigation, TransactionForm, TransactionList, ISINMetadataForm, ISINMetadataList, DashboardHoldingsTable, HoldingsDistributionChart, ClosedPositionsTable, PortfolioSummary, OtherAssetsTable, OtherAssetsDistributionChart, SnapshotValueChart, SnapshotsTable, SnapshotAssetTypeChart)
**Visualization**: Portfolio distribution pie charts with Chart.js, time-series area chart with growth tracking, inline asset distribution charts, asset name display in holdings tables
**Multi-Currency**: EUR/CZK support with backend Decimal precision for other assets
**Exchange Rate**: User-friendly input with onBlur/Enter save pattern (prevents UI blocking)
**Architecture**: Backend-first calculations - all financial math performed on backend using Decimal, frontend is pure presentation layer
**Logging**: Structured JSON logging with audit trail for all operations, request tracing, and performance monitoring

---

**Development Philosophy**: Keep it simple, test thoroughly, maintain separation of concerns, use Decimal for money, all calculations on backend.
