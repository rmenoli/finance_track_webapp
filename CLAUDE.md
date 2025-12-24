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

# Run all tests (245 tests, 95% coverage)
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

**ISIN Metadata**:
- `POST /isin-metadata` - Create ISIN metadata (name and type)
- `GET /isin-metadata?type={type}` - List all with optional type filter
- `GET /isin-metadata/{isin}` - Get by ISIN
- `PUT /isin-metadata/{isin}` - Update metadata
- `DELETE /isin-metadata/{isin}` - Delete by ISIN

**Other Assets**:
- `POST /other-assets` - Create or update (UPSERT by asset_type and asset_detail)
- `GET /other-assets?include_investments={bool}` - List all with optional synthetic investments row
- `DELETE /other-assets/{type}?asset_detail={detail}` - Delete by type and optional detail

**Asset Snapshots**:
- `POST /snapshots` - Create snapshot of current asset state (investments + other assets)
- `GET /snapshots` - List all snapshots with optional filters (date range, asset type)
- `GET /snapshots/summary` - Get aggregated summary statistics per snapshot date with growth tracking
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

### Snapshot Management

**Purpose**: Capture and display historical point-in-time portfolio states with exchange rates for tracking growth over time.

**Key Files**:
- Model: `backend/app/models/asset_snapshot.py` - Individual snapshot rows with datetime, asset details, and exchange rate
- Schemas: `backend/app/schemas/asset_snapshot.py` - SnapshotSummary with growth tracking fields
- Service: `backend/app/services/asset_snapshot_service.py` - Snapshot creation, aggregation, and deletion logic
- Router: `backend/app/routers/asset_snapshots.py` - API endpoints for snapshots
- Frontend Table: `frontend/src/components/SnapshotsTable.jsx` - Display with exchange rate and delete functionality
- Frontend Page: `frontend/src/pages/Snapshots.jsx` - Snapshot list with filters and charts

**Delete Pattern - CRITICAL**:
- Backend DELETE endpoint expects **full datetime** in ISO 8601 format (e.g., `2025-12-22T14:30:45.123456`)
- Uses exact datetime matching in database filter
- Frontend MUST send `snapshot.snapshot_date` as-is (full datetime string), NOT just date part
- Browser's fetch API automatically URL-encodes special characters
- **Common Error**: Sending `"2025-12-22"` (date only) won't match snapshots stored with time component

**SnapshotsTable Component Features**:
- Exchange rate display: Shows "Rate: X.XX CZK/EUR" for each snapshot
- Hover-to-delete: Red X button appears on row hover
- Confirmation dialog: Prompts user before deletion with formatted date
- Auto-refresh: Reloads snapshot list after successful deletion
- CSS pattern: `.snapshot-row:hover .delete-button { opacity: 1 }` for reveal effect

**Example Delete Implementation**:
```javascript
// CORRECT - Send full datetime
const handleDelete = async (snapshot) => {
  await onDelete(snapshot.snapshot_date); // Full ISO datetime string
};

// WRONG - Don't extract date part
const date = new Date(snapshot.snapshot_date);
const isoDate = date.toISOString().split('T')[0]; // ❌ Missing time component
```

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
7. **Snapshots** (`/snapshots`) - Historical portfolio snapshots with growth tracking, exchange rate display, and delete functionality

**Key Components**:
- **Layout**: Main wrapper with navigation for all pages
- **Navigation**: Navigation bar with route links (Dashboard, Transactions, ISIN Metadata, Other Assets, Snapshots)
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
- **SnapshotsTable**: Snapshot list with exchange rate display and hover-to-delete functionality
- **SnapshotValueChart**: Time-series area chart showing portfolio value over time
- **SnapshotAssetTypeChart**: Compact pie chart for asset type distribution per snapshot

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
- `snapshotsAPI`: Asset snapshot operations (create, getSummary with date filters, deleteByDate)

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

**Important - Production Build Configuration**:

In CI/CD, the `VITE_API_URL` environment variable **must be explicitly set** in the GitHub Actions workflow:

```yaml
- name: Build frontend
  env:
    VITE_API_URL: /api/v1  # Required for production builds
  run: |
    cd frontend
    npm ci
    npm run build
```

**Why this matters**:
- Vite doesn't always reliably load `.env.production` in CI/CD environments
- System environment variables take precedence over `.env.*` files
- Without explicit configuration, the build may fall back to `localhost:8000`, causing CORS errors in production
- The frontend API client (`frontend/src/services/api.js`) uses fail-fast error checking to catch missing configuration early

**Production API Routing**:
- Frontend uses relative paths: `/api/v1/*`
- CloudFront routes `/api/*` requests to EC2 backend
- No CORS issues because all requests appear to come from same origin

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

**Development CORS Issues**:

Update `CORS_ORIGINS` in `backend/.env`:
```env
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

**Production CORS Issues** (Frontend calling `localhost:8000` instead of CloudFront):

**Error message**:
```
Access to fetch at 'http://localhost:8000/api/v1/...' from origin 'https://CLOUDFRONT-DOMAIN'
has been blocked by CORS policy: Permission was denied for this request to access
the 'unknown' address space.
```

**Root cause**: Frontend build is using hardcoded `localhost:8000` instead of relative paths `/api/v1`.

**Solution**:

1. **Verify GitHub Actions workflow has environment variable** (`.github/workflows/deploy.yml`):
   ```yaml
   - name: Build frontend
     env:
       VITE_API_URL: /api/v1  # Must be present
     run: |
       cd frontend
       npm ci
       npm run build
   ```

2. **Verify API client has fail-fast checking** (`frontend/src/services/api.js`):
   ```javascript
   const API_BASE_URL = import.meta.env.VITE_API_URL;

   if (!API_BASE_URL) {
     throw new Error('VITE_API_URL environment variable is not set. Check your .env file.');
   }
   ```

3. **Test locally before deploying**:
   ```bash
   cd frontend
   VITE_API_URL=/api/v1 npm run build
   # Build should succeed without errors
   ```

4. **Deploy and verify**:
   - Push changes to main branch
   - CI/CD will automatically rebuild and deploy
   - Open production URL and check browser Network tab
   - API calls should go to `/api/v1/*` (not `localhost:8000`)

## Deployment Considerations

**Local Development**:
- Backend: Uvicorn + SQLite on `localhost:8000`
- Frontend: Vite dev server on `localhost:3000`
- Frontend proxies `/api/*` to backend (configured in `vite.config.js`)

**Production (AWS)**:
- **Frontend**: S3 + CloudFront (CDN with HTTPS)
  - Static React build files served from S3
  - CloudFront handles HTTPS termination
  - CloudFront routes `/api/*` to EC2 backend
- **Backend**: EC2 t3.micro + SystemD service
  - FastAPI + Uvicorn on port 8000 (HTTP only)
  - SQLite database at `/opt/etf-portfolio/backend/portfolio.db`
  - Auto-restart on crash via systemd
  - Daily automated backups
- **API Routing**:
  - Frontend uses relative paths `/api/v1/*`
  - CloudFront routes these to EC2 backend
  - No CORS issues (same-origin from browser perspective)

**Key Production Configuration**:
- Backend `.env`: `CORS_ORIGINS=["https://YOUR_CLOUDFRONT_DOMAIN"]`
- CI/CD: `VITE_API_URL=/api/v1` set in GitHub Actions workflow
- Frontend: Fail-fast error checking if `VITE_API_URL` not set

**Future Considerations**:
- Migrate from SQLite to RDS PostgreSQL for better scalability
- Add Redis for caching and session management
- Implement API Gateway for rate limiting and authentication

## CI/CD Pipeline

### Overview

Automated deployment using GitHub Actions when PRs are merged to `main` branch.

**Workflow**: `.github/workflows/deploy.yml`

**Pipeline Flow**:
```
PR Merge → Run Tests → Build Frontend → Deploy to S3 →
Deploy to EC2 → Verify Health → Complete ✓
```

**Duration**: ~5-7 minutes total
- Tests: ~2 minutes
- Frontend build/deploy: ~1-2 minutes
- Backend deploy: ~1 minute
- CloudFront invalidation: ~1-2 minutes

### GitHub Actions Workflow

**Jobs**:
1. **test**: Runs pytest suite (254 tests, 95% coverage) on Ubuntu runner
2. **deploy**: Deploys both frontend and backend (only runs if tests pass)

**Triggers**:
- Automatic: Push to `main` branch (after PR merge)
- Manual: workflow_dispatch (Actions tab → Run workflow)

### Required GitHub Secrets

Configure in repository Settings → Secrets and variables → Actions:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key for S3/CloudFront |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `AWS_REGION` | AWS region (e.g., `us-east-1`) |
| `S3_BUCKET_NAME` | S3 bucket name for frontend |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront distribution ID (14 chars, starts with E) |
| `CLOUDFRONT_DOMAIN` | CloudFront domain (e.g., `d123abc.cloudfront.net`) |
| `EC2_HOST` | EC2 Elastic IP or public DNS |
| `EC2_USERNAME` | SSH username (`ubuntu` for Ubuntu instances) |
| `EC2_SSH_PRIVATE_KEY` | Private SSH key for EC2 (include headers) |
| `CODECOV_TOKEN` | (Optional) Codecov.io token for coverage reports |

### Manual Deployment

**Trigger deployment manually**:
1. Go to repository → **Actions** tab
2. Click **"Deploy to AWS"** workflow
3. Click **"Run workflow"** dropdown
4. Select branch (usually `main`)
5. Click **"Run workflow"** button

**Use cases**:
- Emergency deployment
- Deploy specific commit/branch
- Re-deploy after fixing configuration
- Rollback to previous version

### Monitoring Deployments

**View workflow logs**:
1. Go to **Actions** tab
2. Click on workflow run
3. Click on job name (test/deploy)
4. Expand steps to see details

**Deployment badge**:
- Added to README.md
- Shows current status (passing/failing)
- Updates automatically after each deployment

**Notifications**:
- GitHub email on workflow failure (if enabled)
- Check GitHub notifications bell

### Deployment Verification

**After successful deployment**:

```bash
# Check frontend (replace with your CloudFront domain)
curl https://YOUR_CLOUDFRONT_DOMAIN

# Check backend API
curl https://YOUR_CLOUDFRONT_DOMAIN/api/v1/health
# Expected: {"status":"healthy"}

# View full API docs
open https://YOUR_CLOUDFRONT_DOMAIN/api/v1/docs
```

### Common CI/CD Issues

**Test failures**:
```bash
# Run tests locally before pushing
cd backend
uv run pytest -v

# If tests pass locally but fail in CI:
# - Check Python version matches (3.12)
# - Verify all dependencies in pyproject.toml
# - Check for environment-specific issues
```

**Frontend build failures**:
```bash
# Test build locally
cd frontend
npm ci
npm run build

# If build succeeds locally but fails in CI:
# - Check Node.js version matches (18)
# - Verify package-lock.json is committed
# - Clear npm cache if needed
```

**EC2 SSH connection failures**:
- Verify `EC2_SSH_PRIVATE_KEY` includes full key with headers
- Check EC2 security group allows SSH from 0.0.0.0/0 (or GitHub Actions IPs)
- Ensure SSH key is added to EC2 `~/.ssh/authorized_keys`
- Test key locally: `ssh -i ~/.ssh/key ubuntu@EC2_IP`

**Backend deployment script failures**:
```bash
# SSH to EC2 manually and debug
ssh -i ~/.ssh/key ubuntu@EC2_IP

cd /opt/etf-portfolio/backend

# Test each step manually
git status                                    # Check git state
git pull origin main                          # Test git pull
/home/ubuntu/.cargo/bin/uv sync --all-extras # Test dependency install
/home/ubuntu/.cargo/bin/uv run alembic upgrade head  # Test migrations
sudo systemctl restart etf-portfolio.service  # Test service restart
curl http://localhost:8000/health             # Test health check
```

**S3 upload failures**:
- Verify `S3_BUCKET_NAME` matches actual bucket name
- Check IAM user has `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket` permissions
- Ensure AWS credentials are correct and not expired

**CloudFront invalidation failures**:
- Verify `CLOUDFRONT_DISTRIBUTION_ID` is correct (14-char ID)
- Check IAM user has `cloudfront:CreateInvalidation` permission
- Note: Invalidation takes 1-2 minutes to complete (workflow doesn't wait)

### Rollback Procedure

**Quick rollback** (if deployment broke production):

**Method 1: Revert commit and re-deploy** (Recommended):
```bash
# Find bad commit
git log --oneline

# Revert it (creates new commit)
git revert <bad-commit-sha>

# Push to main (triggers auto-deployment)
git push origin main
```

**Method 2: Manual rollback** (Faster):

**Backend**:
```bash
# SSH to EC2
ssh -i ~/.ssh/key ubuntu@EC2_IP

# Go to backend directory
cd /opt/etf-portfolio/backend

# Reset to good commit
git reset --hard <good-commit-sha>

# Rollback migration if needed
/home/ubuntu/.cargo/bin/uv run alembic downgrade -1

# Restart service
sudo systemctl restart etf-portfolio.service

# Verify
curl http://localhost:8000/health
```

**Frontend**:
```bash
# From local machine
cd frontend
git reset --hard <good-commit-sha>
npm run build

# Deploy to S3
aws s3 sync dist/ s3://BUCKET_NAME/ --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"

aws s3 cp dist/index.html s3://BUCKET_NAME/index.html \
  --cache-control "public, max-age=300, must-revalidate"

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"
```

### CI/CD Documentation

For complete CI/CD setup and troubleshooting guide, see:
- **Full guide**: `CI_CD.md` - Complete setup instructions with IAM user creation, security best practices, and detailed troubleshooting
- **Workflow file**: `.github/workflows/deploy.yml` - GitHub Actions workflow definition
- **Manual deployment**: `DEPLOYMENT.md` - Manual AWS deployment guide (CLI-based)
- **Console deployment**: `DEPLOYMENT_MANUAL.md` - AWS Console deployment guide (web UI)

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
**Test Coverage**: 95% (245 tests)
**Backend Endpoints**: 21 total (5 transaction, 1 analytics, 2 position values, 5 ISIN metadata, 3 other assets, 4 snapshots, 2 settings) - optimized from 27 endpoints
**Frontend Pages**: 7 (Investment Dashboard, Transactions, Add/Edit Transaction, ISIN Metadata, Add/Edit ISIN Metadata, Other Assets, Snapshots with Growth Tracking)
**Frontend Components**: 15 main components (Layout, Navigation, TransactionForm, TransactionList, ISINMetadataForm, ISINMetadataList, DashboardHoldingsTable, HoldingsDistributionChart, ClosedPositionsTable, PortfolioSummary, OtherAssetsTable, OtherAssetsDistributionChart, SnapshotValueChart, SnapshotsTable, SnapshotAssetTypeChart)
**Visualization**: Portfolio distribution pie charts with Chart.js (centralized color system), time-series area chart with growth tracking, inline asset distribution charts, asset name display in holdings tables
**Multi-Currency**: EUR/CZK support with backend Decimal precision for other assets
**Exchange Rate**: User-friendly input with onBlur/Enter save pattern (prevents UI blocking), optimized settings router with 66% fewer database queries
**Snapshot Management**: Exchange rate display in snapshots table ("Rate: X.XX CZK/EUR"), hover-to-delete with red X button, full datetime deletion with automatic URL encoding, confirmation dialogs with auto-refresh
**Architecture**: Backend-first calculations - all financial math performed on backend using Decimal, frontend is pure presentation layer
**Logging**: Structured JSON logging with audit trail for all operations, request tracing, and performance monitoring

---

**Development Philosophy**: Keep it simple, test thoroughly, maintain separation of concerns, use Decimal for money, all calculations on backend.
