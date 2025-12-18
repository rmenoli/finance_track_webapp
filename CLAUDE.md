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

### Testing
```bash
cd backend

# Run all tests (108 tests, 96% coverage)
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
│   │   ├── constants.py       # Constants and enums
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── models/            # SQLAlchemy models (database layer)
│   │   │   └── transaction.py
│   │   ├── schemas/           # Pydantic schemas (validation layer)
│   │   │   ├── transaction.py
│   │   │   └── analytics.py
│   │   ├── routers/           # API route handlers (HTTP layer)
│   │   │   ├── transactions.py
│   │   │   └── analytics.py
│   │   └── services/          # Business logic (service layer)
│   │       ├── transaction_service.py
│   │       └── cost_basis_service.py
│   ├── alembic/               # Database migrations
│   │   ├── versions/          # Migration files
│   │   ├── env.py             # Alembic environment
│   │   └── script.py.mako     # Migration template
│   ├── tests/                 # Test suite (96% coverage, 108 tests)
│   │   ├── conftest.py       # Test fixtures
│   │   ├── test_transaction_service.py
│   │   ├── test_cost_basis_service.py
│   │   ├── test_api_transactions.py
│   │   ├── test_api_analytics.py
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
│   │   │   ├── DashboardHoldingsTable.jsx  # Holdings table for dashboard
│   │   │   └── PortfolioSummary.jsx   # Dashboard summary cards
│   │   ├── pages/             # Page-level components
│   │   │   ├── InvestmentDashboard.jsx  # Portfolio overview page
│   │   │   ├── Transactions.jsx         # Transaction management
│   │   │   └── AddTransaction.jsx       # Add/edit transaction page
│   │   ├── services/          # API client
│   │   │   └── api.js         # Fetch-based API client
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

## API Structure

All routes prefixed with `/api/v1`:

**Transactions**:
- `POST /transactions` - Create
- `GET /transactions` - List with filters (isin, broker, type, date range)
- `GET /transactions/{id}` - Get one
- `PUT /transactions/{id}` - Update
- `DELETE /transactions/{id}` - Delete

**Analytics**:
- `GET /analytics/portfolio-summary` - Complete portfolio overview (includes holdings, total invested, total fees)

**Position Values**:
- `POST /position-values` - Create or update (UPSERT by ISIN)
- `GET /position-values` - List all position values
- `GET /position-values/{isin}` - Get by ISIN
- `DELETE /position-values/{isin}` - Delete by ISIN

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
1. **Investment Dashboard** (`/`) - Portfolio summary, holdings table, key metrics
2. **Transactions** (`/transactions`) - Full transaction list with filters and CRUD operations
3. **Add/Edit Transaction** (`/transactions/add`, `/transactions/edit/:id`) - Transaction form

**Key Components**:
- **Layout**: Main wrapper with navigation for all pages
- **Navigation**: Navigation bar with route links
- **TransactionForm**: Reusable form for creating/editing transactions
- **TransactionList**: Table view with filters and actions
- **DashboardHoldingsTable**: Detailed holdings display for dashboard
- **PortfolioSummary**: Summary cards showing portfolio metrics

**Routing**: React Router v6 with nested routes
- Layout component wraps all pages
- Routes: `/`, `/transactions`, `/transactions/add`, `/transactions/edit/:id`

**API Client** (`frontend/src/services/api.js`):
- `transactionsAPI`: CRUD operations for transactions
- `analyticsAPI`: Portfolio analytics (summary with holdings, total invested, total fees)
- `positionValuesAPI`: Manual position value tracking (UPSERT, list, get, delete)

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

ISIN format validation in `backend/app/constants.py`: `ISIN_PATTERN`

## Configuration

**Backend Environment Variables** (`.env` in `backend/`):
```env
DATABASE_URL=sqlite:///./portfolio.db
API_V1_PREFIX=/api/v1
PROJECT_NAME=ETF Portfolio Tracker
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

**Frontend Environment Variables**:
- `.env.development`: `VITE_API_URL=http://localhost:8000/api/v1`
- `.env.production`: `VITE_API_URL=/api/v1`

## Testing

**Test Suite**: 92 tests, 96% coverage

**Test Structure**:
- `tests/conftest.py`: Fixtures for database and test client
- `tests/test_transaction_service.py`: Service layer (14 tests)
- `tests/test_cost_basis_service.py`: Cost basis calculations (11 tests)
- `tests/test_position_value_service.py`: Position value service (9 tests)
- `tests/test_api_transactions.py`: Transaction API (20 tests)
- `tests/test_api_analytics.py`: Analytics API (2 tests)
- `tests/test_api_position_values.py`: Position values API (9 tests)
- `tests/test_schemas.py`: Pydantic validation (27 tests)

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
**Test Coverage**: 96% (92 backend tests)
**Backend Endpoints**: 10 total (5 transaction, 1 analytics, 4 position values)
**Frontend Pages**: 3 (Investment Dashboard, Transactions, Add/Edit Transaction)
**Frontend Components**: 6 main components (Layout, Navigation, TransactionForm, TransactionList, DashboardHoldingsTable, PortfolioSummary)

---

**Development Philosophy**: Keep it simple, test thoroughly, maintain separation of concerns, use Decimal for money.
