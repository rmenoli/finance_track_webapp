# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ETF Portfolio Tracker - Full-stack web application for tracking ETF transactions with automatic cost basis calculations using the average cost method. Single-user system with no authentication.

**Tech Stack**:
- **Backend**: FastAPI, SQLAlchemy 2.0, SQLite, Alembic, Pydantic 2.x, UV package manager
- **Frontend**: React 18, Vite, React Router v6, CSS (component-scoped)

## Essential Commands

### Development Servers

**Backend** (Terminal 1):
```bash
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
# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Testing
```bash
# Run all tests
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
sqlite3 portfolio.db

# Inside sqlite3:
.tables                    # List tables
.schema transactions       # View schema
SELECT * FROM transactions; # Query data
.quit                      # Exit
```

## Architecture

### Three-Layer Architecture

1. **Routers** (`app/routers/`): API endpoints, request validation, HTTP concerns
   - `transactions.py`: CRUD operations for transactions
   - `analytics.py`: Portfolio analytics and cost basis calculations

2. **Services** (`app/services/`): Business logic, no HTTP knowledge
   - `transaction_service.py`: Transaction CRUD operations, filtering, pagination
   - `cost_basis_service.py`: Core financial calculations (average cost, realized gains)

3. **Models** (`app/models/`): Database schema via SQLAlchemy ORM
   - `transaction.py`: Transaction model with constraints and indexes

### Key Design Patterns

**Dependency Injection**: Database sessions injected via FastAPI's `Depends(get_db)`

**Schema Separation**:
- `models/`: SQLAlchemy ORM (database layer)
- `schemas/`: Pydantic models (API layer)
- Never mix these - Pydantic for validation, SQLAlchemy for persistence

**Service Layer Pattern**: All business logic in `services/`, routers are thin wrappers

### Cost Basis Calculation Logic

**Average Cost Method** (in `cost_basis_service.py`):

1. **BUY transactions**: Add to total cost and units
   - `total_cost += (price_per_unit × units) + fee`
   - `total_units += units`

2. **SELL transactions**: Remove proportional cost basis
   - `proportion = units_sold / total_units`
   - `cost_removed = total_cost × proportion`
   - `total_cost -= cost_removed`
   - `total_units -= units_sold`

3. **Realized Gain** = `(sell_price × units - fee) - (avg_cost × units)`

**Critical**: Process transactions chronologically (ORDER BY date ASC) for accurate calculations.

### Financial Precision

**Always use `Decimal`** for monetary values, never `float`. Database columns are `Numeric(10, 2)` for fees, `Numeric(10, 4)` for prices and units.

```python
# Correct
from decimal import Decimal
fee = Decimal("1.50")

# Wrong - floating point errors
fee = 1.50  # Never use float for money
```

### Database Constraints

Transaction model has SQLAlchemy CheckConstraints:
- `units > 0`
- `price_per_unit > 0`
- `fee >= 0`

These are enforced at database level, but also validate in Pydantic schemas.

### ISIN Validation

ISIN format: 12 characters (2 letters + 9 alphanumeric + 1 check digit)
- Validated by regex in `constants.py`: `ISIN_PATTERN`
- Applied in Pydantic schemas with `@field_validator`
- Always uppercase ISINs before storage/queries

### Pydantic Model Naming Convention

Avoid using `date` as both a field name and importing `date` type. Use:
```python
from datetime import date as DateType
```
This prevents Pydantic field name clashing errors.

## Configuration

Environment variables in `.env`:
- `DATABASE_URL`: SQLite path (default: `sqlite:///./portfolio.db`)
- `API_V1_PREFIX`: API route prefix (default: `/api/v1`)
- `DEBUG`: Enable debug mode and SQL logging
- `CORS_ORIGINS`: JSON array of allowed origins for frontend

Configuration loaded via Pydantic Settings in `app/config.py`.

## Frontend Architecture

### Project Structure

```
frontend/
├── src/
│   ├── components/        # Reusable React components
│   │   ├── Layout.jsx     # Main layout wrapper with navigation
│   │   ├── Navigation.jsx # Navigation bar
│   │   ├── TransactionForm.jsx    # Add/edit transaction form
│   │   ├── TransactionList.jsx    # Transaction table
│   │   ├── HoldingsTable.jsx      # Holdings display
│   │   └── PortfolioSummary.jsx   # Dashboard summary cards
│   ├── pages/             # Page-level components
│   │   ├── Dashboard.jsx  # Portfolio overview
│   │   ├── Transactions.jsx       # Transaction management
│   │   ├── AddTransaction.jsx     # Add/edit transaction page
│   │   ├── Holdings.jsx   # Current holdings view
│   │   └── Analytics.jsx  # Cost basis and gains
│   ├── services/          # API client
│   │   └── api.js         # Fetch-based API client
│   ├── App.jsx            # Main app with routing
│   └── main.jsx           # Entry point
├── vite.config.js         # Vite configuration (proxy setup)
└── package.json           # Dependencies
```

### Component Architecture

**Pattern**: Functional components with hooks (useState, useEffect)

**No state management library**: Simple useState/useEffect for all state (adequate for single-user app)

**Routing**: React Router v6 with nested routes
- Layout component wraps all pages
- Navigation uses NavLink for active states
- Routes: /, /transactions, /transactions/add, /transactions/edit/:id, /holdings, /analytics

### API Client (`src/services/api.js`)

All backend communication goes through `api.js`. Two main objects:

**transactionsAPI**:
- `getAll(params)` - GET /transactions with filters
- `getById(id)` - GET /transactions/{id}
- `create(data)` - POST /transactions
- `update(id, data)` - PUT /transactions/{id}
- `delete(id)` - DELETE /transactions/{id}

**analyticsAPI**:
- `getPortfolioSummary()` - GET /analytics/portfolio-summary
- `getHoldings()` - GET /analytics/holdings
- `getAllCostBases()` - GET /analytics/cost-basis
- `getCostBasis(isin)` - GET /analytics/cost-basis/{isin}
- `getRealizedGains(isin?)` - GET /analytics/realized-gains

**Error Handling**: All API methods throw errors with descriptive messages. Components catch and display to users.

**Base URL**: Configured via `VITE_API_URL` environment variable (defaults to http://localhost:8000/api/v1)

### Key Components

**TransactionForm.jsx**:
- Handles both create and edit modes
- Client-side validation matching backend rules:
  - ISIN: 12 characters (2 letters + 9 alphanumeric + 1 digit)
  - Date: Cannot be in future
  - Units: Must be > 0
  - Price per unit: Must be > 0
  - Fee: Must be >= 0
- Displays validation errors inline
- Navigates back to transactions list on success

**TransactionList.jsx**:
- Displays transactions in table format
- Edit/delete buttons per row
- Shows total cost per transaction
- Color-coded BUY/SELL badges

**PortfolioSummary.jsx**:
- Grid of summary cards (responsive)
- Color-coded positive (green) and negative (red) values
- Shows: total invested, fees, realized gains, unique ISINs, current holdings value

**HoldingsTable.jsx**:
- Current positions grouped by ISIN
- Shows units, average cost, total cost
- Footer row with totals

### Styling Approach

**Component-scoped CSS**: Each component has its own CSS file (e.g., `Layout.css`, `Dashboard.css`)

**Global styles** (`index.css`):
- Utility classes: `.btn`, `.btn-primary`, `.btn-secondary`
- Input styles: `.input`, `.input-error`
- Table styles: `.table`, `.table-container`
- Badges: `.badge`, `.badge-buy`, `.badge-sell`
- Loading/error states: `.loading`, `.error`

**Responsive**: Uses CSS Grid and flexbox with mobile breakpoints

**No CSS framework**: Clean, functional styles without external dependencies

### Vite Configuration

**Proxy setup** (`vite.config.js`):
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

This proxies `/api/*` requests from frontend (port 3000) to backend (port 8000) during development, avoiding CORS issues.

**Environment variables**:
- `VITE_API_URL` - Backend API base URL
- Access in code with `import.meta.env.VITE_API_URL`

### Common Frontend Development Scenarios

**Adding a New Page**:
1. Create page component in `src/pages/MyPage.jsx`
2. Create corresponding CSS file `src/pages/MyPage.css`
3. Add route in `src/App.jsx` within the Layout Route
4. Add navigation link in `src/components/Navigation.jsx`

**Adding a New Component**:
1. Create component in `src/components/MyComponent.jsx`
2. Create CSS file `src/components/MyComponent.css`
3. Import and use in pages or other components
4. Follow existing patterns (functional components, useState/useEffect)

**Modifying API Client**:
1. Edit `src/services/api.js`
2. Add new methods following existing patterns
3. Always include error handling (try/catch, throw descriptive errors)
4. Update components to use new API methods

**Styling Guidelines**:
- Prefer component-scoped CSS over inline styles
- Use global utility classes from `index.css` when applicable
- Follow existing color scheme (blues, greens, reds)
- Maintain responsive design patterns
- Test on mobile (viewport < 768px)

**Form Validation**:
- Always validate on client side before API call
- Match backend validation rules exactly
- Display errors inline near the invalid field
- Use `.input-error` class for invalid inputs
- Show success feedback after successful operations

**Loading States**:
- Show loading indicator during API calls (`<p>Loading...</p>`)
- Disable buttons during submission to prevent double-clicks
- Handle errors gracefully with user-friendly messages

### Frontend Environment Variables

**`.env.development`** (active during `npm run dev`):
```env
VITE_API_URL=http://localhost:8000/api/v1
```

**`.env.production`** (active during `npm run build`):
```env
VITE_API_URL=/api/v1
```

Production assumes frontend and backend are served from same origin.

## API Structure

All routes prefixed with `/api/v1`:

**Transactions**:
- `POST /transactions` - Create
- `GET /transactions` - List with filters (isin, broker, type, date range)
- `GET /transactions/{id}` - Get one
- `PUT /transactions/{id}` - Update
- `DELETE /transactions/{id}` - Delete

**Analytics**:
- `GET /analytics/cost-basis` - All holdings
- `GET /analytics/cost-basis/{isin}` - Specific ISIN
- `GET /analytics/holdings` - Current positions
- `GET /analytics/realized-gains` - P&L from sells
- `GET /analytics/portfolio-summary` - Complete overview

Interactive docs: http://localhost:8000/docs (Swagger UI)

## Common Development Scenarios

### Adding a New Field to Transaction

1. Update `app/models/transaction.py` (SQLAlchemy model)
2. Update `app/schemas/transaction.py` (Pydantic schemas)
3. Generate migration: `uv run alembic revision --autogenerate -m "add_field_name"`
4. Review generated migration in `alembic/versions/`
5. Apply: `uv run alembic upgrade head`

### Adding a New Analytics Endpoint

1. Add calculation function in `app/services/cost_basis_service.py`
2. Add response schema in `app/schemas/analytics.py`
3. Add route in `app/routers/analytics.py`
4. Use existing patterns (dependency injection, error handling)

### Modifying Cost Basis Logic

All cost basis calculations are in `cost_basis_service.py`. Key functions:
- `calculate_cost_basis()`: Average cost for one ISIN
- `calculate_current_holdings()`: All holdings
- `calculate_realized_gains()`: P&L from sells
- `get_portfolio_summary()`: Aggregates all metrics

When modifying, maintain chronological transaction processing (ORDER BY date).

## Test Suite

**Coverage**: 96% (86 tests)

### Test Structure

- `tests/conftest.py`: Fixtures for database and test client
- `tests/test_transaction_service.py`: Transaction service CRUD operations (14 tests)
- `tests/test_cost_basis_service.py`: Cost basis calculation logic (15 tests)
- `tests/test_api_transactions.py`: Transaction API endpoints (20 tests)
- `tests/test_api_analytics.py`: Analytics API endpoints (14 tests)
- `tests/test_schemas.py`: Pydantic validation (23 tests)

### Key Test Patterns

**Database Isolation**: Each test gets a fresh database via `db_session` fixture

**API Testing**: Uses FastAPI TestClient with dependency override for database

**Financial Calculations**: Extensive tests for cost basis edge cases:
- Single/multiple buys
- Partial/full sells
- Average cost calculations
- Realized gains (profit and loss)
- Portfolio summaries

**Validation Testing**: Tests all Pydantic validators:
- ISIN format validation
- Date validation (no future dates)
- Positive value constraints
- Fee non-negative constraint

### Running Specific Test Categories

```bash
# Service layer tests
uv run pytest tests/test_transaction_service.py tests/test_cost_basis_service.py

# API tests
uv run pytest tests/test_api_transactions.py tests/test_api_analytics.py

# Validation tests
uv run pytest tests/test_schemas.py
```

## Testing the API Manually

Quick manual test:
```bash
# Start server
uv run uvicorn app.main:app --reload

# In another terminal:
# Create BUY transaction
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-01-15", "isin": "IE00B4L5Y983", "broker": "IB", "fee": 1.50, "price_per_unit": 450.25, "units": 10.0, "transaction_type": "BUY"}'

# Check portfolio
curl http://localhost:8000/api/v1/analytics/portfolio-summary
```

## Important Constraints

1. **No Authentication**: Single-user system, no user model or auth
2. **SQLite Only**: Not designed for high concurrency (but WAL mode enabled)
3. **Synchronous**: Using sync SQLAlchemy, not async (adequate for single user)
4. **Date Validation**: Transaction dates cannot be in the future
5. **No Soft Deletes**: Transactions are hard-deleted (use with caution)

## Troubleshooting

### Frontend "Failed to fetch" Error

**Symptoms**: Frontend shows "Failed to fetch", "Network Error", or API calls fail

**Diagnostic Steps**:

1. **Verify backend is running on port 8000**:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy"}
   ```

2. **Check if wrong process is on port 8000**:
   ```bash
   lsof -i :8000
   # Should show uvicorn process, not something else
   ```

3. **Check backend is accessible**:
   ```bash
   # Backend must use 0.0.0.0 (not 127.0.0.1 only)
   ps aux | grep uvicorn | grep 8000
   # Should see: --host 0.0.0.0 --port 8000
   ```

4. **Verify CORS configuration**:
   ```bash
   cat .env | grep CORS_ORIGINS
   # Should include: http://localhost:3000
   ```

**Common Solutions**:

```bash
# Kill wrong process on port 8000
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Start backend correctly
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Verify it's working
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/transactions
```

**Frontend Configuration Check**:
```bash
# Verify frontend API URL
cat frontend/.env.development
# Should be: VITE_API_URL=http://localhost:8000/api/v1

# Check Vite proxy config
cat frontend/vite.config.js
# Should proxy /api to http://localhost:8000
```

### Port Conflicts

**Backend port 8000 in use**:
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>
```

**Frontend port 3000 in use**:
```bash
# Use different port
cd frontend
npm run dev -- --port 3001

# Update backend CORS to include new port
# Edit .env: CORS_ORIGINS=["http://localhost:3001", ...]
```

### Database Issues

**Database locked**:
- Close all DB browser connections
- Restart backend (SQLite WAL mode should prevent this)

**Migration issues**:
```bash
# Check current version
uv run alembic current

# Apply migrations
uv run alembic upgrade head

# Reset database (destructive)
rm portfolio.db
uv run alembic upgrade head
```

## Migration Notes

When importing models in `alembic/env.py`, use `# noqa: F401` to silence unused import warnings. This is required for autogenerate to detect models.

```python
from app.models.transaction import Transaction  # noqa: F401
```

## Database Schema

Single table: `transactions`
- Primary key: `id` (auto-increment)
- Indexes: `date`, `isin`, composite `(date, isin)`
- Timestamps: `created_at`, `updated_at` (auto-managed)
- Enum: `transaction_type` (BUY or SELL)

SQLite database file: `portfolio.db` (gitignored)
