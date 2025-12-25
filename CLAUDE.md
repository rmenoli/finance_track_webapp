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

**IMPORTANT**: Backend MUST run on port 8000 with `--host 0.0.0.0` for frontend to connect.

**Health check**: `curl http://localhost:8000/health` (should return `{"status":"healthy"}`)

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

```bash
cd backend

# Default INFO level (structured JSON)
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Debug level
LOG_LEVEL=DEBUG uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Human-readable text format
LOG_FORMAT=text uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Logs include: HTTP requests, audit trail, exceptions, performance metrics (>100ms).

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
│   │   ├── models/            # SQLAlchemy models (database layer)
│   │   ├── schemas/           # Pydantic schemas (validation layer)
│   │   ├── routers/           # API route handlers (HTTP layer)
│   │   └── services/          # Business logic (service layer)
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Test suite (95% coverage, 254 tests)
│   └── README.md             # 📖 Comprehensive backend documentation
│
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── components/        # Reusable React components (15 components)
│   │   ├── pages/             # Page-level components (7 pages)
│   │   ├── constants/         # Application constants
│   │   ├── services/          # API client (api.js)
│   │   └── utils/             # Utility functions
│   └── README.md             # 📖 Frontend documentation
│
├── CLAUDE.md                  # This file (development guidance)
└── README.md                  # High-level overview
```

**Note**: See `backend/README.md` and `frontend/README.md` for detailed file-by-file documentation.

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

**All P/L calculated on backend** using `Decimal` (in `backend/app/services/cost_basis_service.py`).

**Open positions**:
```python
absolute_pl = current_value - total_cost_with_fees
percentage_pl = (absolute_pl / total_cost_with_fees * 100)
```

**Closed positions**:
```python
absolute_pl = total_gains - total_cost_with_fees
percentage_pl = (absolute_pl / total_cost_with_fees * 100)
```

Frontend displays pre-calculated values from API responses.

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

Uses Pydantic's `@computed_field` for calculated values in API responses (not stored in DB).

**Transaction responses**: `total_without_fees`, `total_with_fees`
**Holdings responses**: `net_buy_in_cost`, `net_buy_in_cost_per_unit`, `current_price_per_unit`

**Benefits**: Single source of truth, no DB migrations needed, all calculations use `Decimal` precision

## API Structure

All routes prefixed with `/api/v1`. Interactive docs: http://localhost:8000/docs

**Transactions**: `POST`, `GET`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`, `POST /degiro-import-csv-transactions`

**Analytics**: `GET /portfolio-summary` (holdings, total invested, total fees)

**Position Values**: `POST` (UPSERT by ISIN), `GET`

**ISIN Metadata**: `POST`, `GET ?type={type}`, `GET /{isin}`, `PUT /{isin}`, `DELETE /{isin}`

**Other Assets**: `POST` (UPSERT), `GET ?include_investments={bool}`, `DELETE /{type}?asset_detail={detail}`

**Asset Snapshots**: `POST`, `GET`, `GET /summary` (growth tracking), `DELETE /{snapshot_date}`, `POST /import-csv`

**Note**: Transaction and holdings responses include computed fields. See schemas for details.

## Common Development Scenarios

### Adding a New Field to Transaction

1. Update model: `backend/app/models/transaction.py`
2. Update schema: `backend/app/schemas/transaction.py`
3. Generate migration: `uv run alembic revision --autogenerate -m "add_field"`
4. Apply migration: `uv run alembic upgrade head`
5. Update tests

### Adding a New Analytics Endpoint

1. Add calculation in `backend/app/services/cost_basis_service.py`
2. Add response schema in `backend/app/schemas/analytics.py`
3. Add route in `backend/app/routers/analytics.py`
4. Write tests

### Modifying Cost Basis Logic

All cost basis calculations in `backend/app/services/cost_basis_service.py`:
- `calculate_cost_basis()`: Average cost for one ISIN
- `calculate_current_holdings()`: All holdings
- `get_portfolio_summary()`: Aggregates total invested, total fees, holdings

**Critical**: Maintain chronological processing (`ORDER BY date ASC`).

**See `backend/README.md` for**: Position value tracking, snapshot management, detailed workflow examples.

## Frontend Architecture

**Pattern**: Functional components with hooks (useState, useEffect). No state management library.

**Pages** (7 total):
1. Investment Dashboard (`/`) - Portfolio overview
2. Transactions (`/transactions`) - Transaction list with CRUD
3. ISIN Metadata (`/isin-metadata`) - Asset metadata management
4. Other Assets (`/other-assets`) - Multi-currency non-ETF holdings
5. Snapshots (`/snapshots`) - Historical portfolio states with growth tracking

**Key Features**:
- Interactive Chart.js visualizations (pie charts, time-series)
- Centralized color system (`frontend/src/constants/chartColors.js`)
- API client with CRUD + analytics (`frontend/src/services/api.js`)
- React Router v6 with nested routes

**Styling**: Component-scoped CSS + global utilities in `index.css`

**See `frontend/README.md` for**: Component details, API client usage, chart configuration.

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

**Common cause**: Backend not running or wrong host/port.

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check process on port 8000
lsof -i :8000

# Start backend correctly
cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Port Conflicts

```bash
lsof -i :8000        # Find process
kill -9 <PID>        # Kill process
```

### Database Issues

```bash
cd backend
uv run alembic current        # Check migration status
uv run alembic upgrade head   # Apply migrations
```

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

**Automated deployment** using GitHub Actions when code is pushed to `main` branch.

**Workflow**: `.github/workflows/deploy.yml`

**Pipeline Flow**:
```
PR Merge → Run Tests → Build Frontend → Deploy to S3 → Deploy to EC2 → Complete ✓
```

**Duration**: ~5-7 minutes total

### Manual Deployment

**Trigger manually from GitHub**:
1. Go to repository → **Actions** tab
2. Click **"Deploy to AWS"** workflow
3. Click **"Run workflow"** → Select `main` branch → **"Run workflow"**

**Use cases**: Emergency deployment, rollback to specific commit, re-deploy after config fix

### Deployment Verification

```bash
# Check frontend
curl https://YOUR_CLOUDFRONT_DOMAIN

# Check backend API
curl https://YOUR_CLOUDFRONT_DOMAIN/api/v1/health
# Expected: {"status":"healthy"}
```

### Quick Rollback

**Revert commit and re-deploy**:
```bash
git revert <bad-commit-sha>
git push origin main  # Triggers auto-deployment
```

### Full Documentation

**See `CI_CD.md` for**:
- Complete setup with IAM user creation
- GitHub secrets configuration
- Detailed troubleshooting (test failures, SSH issues, CORS)
- Manual rollback procedures
- Security best practices

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
**Test Coverage**: 95% (277 tests)
**Backend Endpoints**: 23 total (6 transaction, 1 analytics, 2 position values, 5 ISIN metadata, 3 other assets, 5 snapshots, 2 settings) - includes CSV import for transactions and snapshots
**Frontend Pages**: 7 (Investment Dashboard, Transactions, Add/Edit Transaction, ISIN Metadata, Add/Edit ISIN Metadata, Other Assets, Snapshots with Growth Tracking)
**Frontend Components**: 15 main components (Layout, Navigation, TransactionForm, TransactionList, ISINMetadataForm, ISINMetadataList, DashboardHoldingsTable, HoldingsDistributionChart, ClosedPositionsTable, PortfolioSummary, OtherAssetsTable, OtherAssetsDistributionChart, SnapshotValueChart, SnapshotsTable, SnapshotAssetTypeChart)
**Visualization**: Portfolio distribution pie charts with Chart.js (centralized color system), time-series area chart with growth tracking, inline asset distribution charts, asset name display in holdings tables
**Multi-Currency**: EUR/CZK support with backend Decimal precision for other assets
**Exchange Rate**: User-friendly input with onBlur/Enter save pattern (prevents UI blocking), optimized settings router with 66% fewer database queries
**Snapshot Management**: Exchange rate display in snapshots table ("Rate: X.XX CZK/EUR"), hover-to-delete with red X button, full datetime deletion with automatic URL encoding, confirmation dialogs with auto-refresh
**CSV Import**: Bulk import for transactions (DEGIRO) and snapshots with detailed error reporting, color-coded results, and row-by-row validation. Frontend has import buttons with file validation and auto-refresh after successful imports.
**Architecture**: Backend-first calculations - all financial math performed on backend using Decimal, frontend is pure presentation layer
**Logging**: Structured JSON logging with audit trail for all operations, request tracing, and performance monitoring

---

**Development Philosophy**: Keep it simple, test thoroughly, maintain separation of concerns, use Decimal for money, all calculations on backend.
