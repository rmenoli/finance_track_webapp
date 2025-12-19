# Backend - ETF Portfolio Tracker

FastAPI backend service for tracking ETF transactions with automatic cost basis calculations using the average cost method. Part of the full-stack ETF Portfolio Tracker application.

## Table of Contents

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [API Documentation](#api-documentation)
- [Database Management](#database-management)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Architecture](#architecture)
- [Common Scenarios](#common-scenarios)
- [Troubleshooting](#troubleshooting)

## Tech Stack

- **Framework**: FastAPI 0.124.4 (high-performance, modern Python web framework)
- **Database**: SQLite with SQLAlchemy 2.0.45 (ORM)
- **Migrations**: Alembic 1.17.2 (database version control)
- **Validation**: Pydantic 2.12.5 (data validation and settings)
- **Package Manager**: UV (fast Python package manager)
- **Server**: Uvicorn 0.38.0 (ASGI server)
- **Testing**: Pytest 9.0.2 with 95% coverage (158 tests)
- **Code Quality**: Ruff 0.14.9 (linting and formatting)

## Prerequisites

- **Python 3.11+** (Python 3.12 recommended)
- **UV** package manager (recommended) or pip
- **SQLite** (comes pre-installed on most systems)
- **Git** (for version control)

### Installing UV

UV is a fast Python package manager that replaces pip, poetry, and other tools.

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```bash
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Verify installation:**
```bash
uv --version
```

## Installation

### Step 1: Navigate to Backend Directory

From the project root:
```bash
cd backend
```

### Step 2: Install Dependencies

**Using UV (Recommended):**
```bash
# Install all dependencies including dev tools
uv sync --all-extras

# Or install only production dependencies
uv sync
```

**Using pip (Alternative):**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -e .
pip install -e ".[dev]"
```

### Step 3: Set Up the Database

Run migrations to create the database and tables:

```bash
uv run alembic upgrade head
```

You should see output like:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 3ff3f0eefe40, initial_transaction_table
```

This creates `portfolio.db` in the backend directory.

## Configuration

### Environment Variables

The backend uses a `.env` file for configuration. Create or edit `.env`:

```bash
cat .env
```

**Default configuration:**
```env
DATABASE_URL=sqlite:///./portfolio.db
API_V1_PREFIX=/api/v1
PROJECT_NAME=ETF Portfolio Tracker
DEBUG=True
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./portfolio.db` |
| `API_V1_PREFIX` | API route prefix | `/api/v1` |
| `PROJECT_NAME` | Application name | `ETF Portfolio Tracker` |
| `DEBUG` | Enable debug mode and SQL logging | `True` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:3000", ...]` |

**Important Notes:**
- In production, set `DEBUG=False`
- For PostgreSQL deployment (AWS RDS), update `DATABASE_URL` to PostgreSQL connection string
- Add production frontend URL to `CORS_ORIGINS` when deploying

## Running the Server

### Development Mode

Start the server with auto-reload (restarts on code changes):

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Why `--host 0.0.0.0`?** This makes the server accessible from other machines on the network, required for the frontend to connect properly.

### Production Mode

Run with multiple workers for better performance:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Verify Server is Running

```bash
# Health check endpoint
curl http://localhost:8000/health
# Expected response: {"status":"healthy"}

# Open interactive API documentation in browser
open http://localhost:8000/docs
# Or visit: http://localhost:8000/docs manually
```

You should see:
- `INFO: Application startup complete` in the terminal
- JSON response `{"status":"healthy"}` from the health check
- Interactive Swagger UI at http://localhost:8000/docs

## API Documentation

### Interactive Documentation

FastAPI provides automatic interactive API documentation:

1. **Swagger UI**: http://localhost:8000/docs
   - Interactive API testing interface
   - Try out endpoints directly from the browser
   - See request/response schemas

2. **ReDoc**: http://localhost:8000/redoc
   - Clean, readable API documentation
   - Better for understanding API structure

### Endpoints

All endpoints are prefixed with `/api/v1`

#### Transaction Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/transactions` | Create a new transaction |
| GET | `/transactions` | List all transactions (with optional filters) |
| GET | `/transactions/{id}` | Get specific transaction by ID |
| PUT | `/transactions/{id}` | Update an existing transaction |
| DELETE | `/transactions/{id}` | Delete a transaction (hard delete) |

**Query Parameters for GET /transactions:**
- `isin`: Filter by ISIN code
- `broker`: Filter by broker name
- `transaction_type`: Filter by BUY or SELL
- `start_date`: Filter transactions from this date
- `end_date`: Filter transactions up to this date
- `skip`: Pagination offset (default: 0)
- `limit`: Number of results (default: 100)

#### Analytics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/portfolio-summary` | Complete portfolio overview including holdings, total invested, and total fees |

#### Position Value Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/position-values` | Create or update position value (UPSERT by ISIN) |
| GET | `/position-values` | List all position values |
| GET | `/position-values/{isin}` | Get position value for specific ISIN |
| DELETE | `/position-values/{isin}` | Delete position value by ISIN |

**Position Values** allow users to manually track the current market value of their positions. Values are stored per ISIN with automatic timestamp tracking. When creating/updating, the system uses UPSERT logic - one row per ISIN that updates if it exists or creates if new.

#### ISIN Metadata Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/isin-metadata` | Create new ISIN metadata (name and type) |
| POST | `/isin-metadata/upsert` | Create or update ISIN metadata (UPSERT by ISIN) |
| GET | `/isin-metadata?type={type}` | List all ISIN metadata with optional type filter |
| GET | `/isin-metadata/{isin}` | Get ISIN metadata for specific ISIN |
| PUT | `/isin-metadata/{isin}` | Update ISIN metadata (name and/or type) |
| DELETE | `/isin-metadata/{isin}` | Delete ISIN metadata by ISIN |

**ISIN Metadata** stores asset information (name and type) for each ISIN. The type field is an enum with three values: `STOCK`, `BOND`, or `REAL_ASSET`. This feature enables categorizing ISINs and displaying meaningful names instead of bare ISIN codes. The metadata is independent of transactions - you can have metadata without transactions and vice versa.

### Example Requests

#### Create a Transaction

```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-01-15",
    "isin": "IE00B4L5Y983",
    "broker": "Interactive Brokers",
    "fee": 1.50,
    "price_per_unit": 450.25,
    "units": 10.0,
    "transaction_type": "BUY"
  }'
```

#### Get Portfolio Summary

```bash
curl http://localhost:8000/api/v1/analytics/portfolio-summary
```

#### Create/Update Position Value

```bash
curl -X POST http://localhost:8000/api/v1/position-values \
  -H "Content-Type: application/json" \
  -d '{
    "isin": "IE00B4L5Y983",
    "current_value": 5000.50
  }'
```

#### Get All Position Values

```bash
curl http://localhost:8000/api/v1/position-values
```

#### Create ISIN Metadata

```bash
curl -X POST http://localhost:8000/api/v1/isin-metadata \
  -H "Content-Type: application/json" \
  -d '{
    "isin": "IE00B4L5Y983",
    "name": "iShares Core MSCI Emerging Markets ETF",
    "type": "STOCK"
  }'
```

#### List ISIN Metadata by Type

```bash
# Get all stocks
curl "http://localhost:8000/api/v1/isin-metadata?type=STOCK"

# Get all bonds
curl "http://localhost:8000/api/v1/isin-metadata?type=BOND"

# Get all real assets
curl "http://localhost:8000/api/v1/isin-metadata?type=REAL_ASSET"
```

### Validation Rules

**Transaction Validation:**
- **ISIN**: Exactly 12 characters (2 letters + 9 alphanumeric + 1 digit)
- **Date**: Cannot be in the future
- **Units**: Must be > 0
- **Price per unit**: Must be > 0
- **Fee**: Must be >= 0
- **Transaction type**: Either "BUY" or "SELL"

**ISIN Metadata Validation:**
- **ISIN**: Exactly 12 characters (2 letters + 9 alphanumeric + 1 digit), auto-uppercase
- **Name**: 1-255 characters, whitespace stripped
- **Type**: Must be one of `STOCK`, `BOND`, or `REAL_ASSET`

**Position Value Validation:**
- **ISIN**: 1-12 characters (no format validation - allows any string)
- **Current value**: Must be > 0

### Response Schemas

#### Portfolio Summary Response

The `/analytics/portfolio-summary` endpoint returns comprehensive portfolio data including calculated P/L for each holding:

```json
{
  "total_invested": "10000.00",
  "total_withdrawn": "2000.00",
  "total_fees": "25.50",
  "total_current_portfolio_invested_value": "11500.00",
  "total_profit_loss": "3474.50",
  "holdings": [
    {
      "isin": "IE00B4L5Y983",
      "total_units": "10.5000",
      "total_cost_without_fees": "5000.00",
      "total_gains_without_fees": "0.00",
      "total_fees": "12.50",
      "transactions_count": 2,
      "current_value": "5500.00",
      "absolute_pl_without_fees": "500.00",
      "percentage_pl_without_fees": "10.00",
      "absolute_pl_with_fees": "487.50",
      "percentage_pl_with_fees": "9.73"
    }
  ],
  "closed_positions": [
    {
      "isin": "US0378331005",
      "total_units": "0.0000",
      "total_cost_without_fees": "3000.00",
      "total_gains_without_fees": "3500.00",
      "total_fees": "15.00",
      "transactions_count": 4,
      "current_value": "0",
      "absolute_pl_without_fees": "500.00",
      "percentage_pl_without_fees": "16.67",
      "absolute_pl_with_fees": "485.00",
      "percentage_pl_with_fees": "16.08"
    }
  ]
}
```

**Key Fields Explained:**

**Holdings (Open Positions):**
- `current_value`: Current market value of the position (from manual entry, `null` if not set)
- `absolute_pl_without_fees`: Profit/Loss without fees in currency (`null` if no current value)
- `percentage_pl_without_fees`: Profit/Loss percentage without fees (`null` if no current value)
- `absolute_pl_with_fees`: Profit/Loss including fees in currency (`null` if no current value)
- `percentage_pl_with_fees`: Profit/Loss percentage including fees (`null` if no current value)

**Closed Positions (Fully Sold):**
- `current_value`: Always `0` for closed positions
- `absolute_pl_without_fees`: Realized profit/loss without fees
- `percentage_pl_without_fees`: Realized profit/loss percentage without fees
- `absolute_pl_with_fees`: Realized profit/loss including fees
- `percentage_pl_with_fees`: Realized profit/loss percentage including fees

**Important Notes:**
- All P/L calculations are performed on the backend using Python `Decimal` for financial precision
- For open positions, P/L is `null` if no `current_value` has been manually entered
- For closed positions, P/L represents the realized gains/losses from selling
- P/L calculations use the average cost method for cost basis

## Database Management

### View Database

Connect to the SQLite database:

```bash
sqlite3 portfolio.db

# Inside sqlite3:
.tables                    # List tables
.schema transactions       # View schema
SELECT * FROM transactions; # Query data
.quit                      # Exit
```

### Database Migrations

#### Create a New Migration

After modifying models in `app/models/`:

```bash
# Generate migration automatically
uv run alembic revision --autogenerate -m "description of changes"

# Review generated migration in alembic/versions/
# Then apply it
uv run alembic upgrade head
```

#### Rollback Migrations

```bash
# Rollback one migration
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade <revision_id>

# Rollback all migrations
uv run alembic downgrade base
```

#### View Migration History

```bash
uv run alembic history

# Check current revision
uv run alembic current
```

#### Reset Database

```bash
# Delete the database file
rm portfolio.db

# Recreate with migrations
uv run alembic upgrade head
```

## Testing

### Run All Tests

```bash
# Run all 152 tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run with coverage report (95% coverage)
uv run pytest --cov=app --cov-report=term-missing --cov-report=html
```

### Run Specific Tests

```bash
# Run specific test file
uv run pytest tests/test_transaction_service.py -v

# Run specific test class
uv run pytest tests/test_api_transactions.py::TestTransactionAPI -v

# Run specific test
uv run pytest tests/test_cost_basis_service.py::TestCostBasisService::test_calculate_cost_basis_single_buy -v
```

### Test Categories

```bash
# Service layer tests (44 tests)
uv run pytest tests/test_transaction_service.py tests/test_cost_basis_service.py tests/test_isin_metadata_service.py tests/test_position_value_service.py

# API tests (71 tests)
uv run pytest tests/test_api_transactions.py tests/test_api_analytics.py tests/test_api_isin_metadata.py tests/test_api_position_values.py

# Validation tests (39 tests)
uv run pytest tests/test_schemas.py

# ISIN metadata specific tests (45 tests)
uv run pytest tests/test_isin_metadata_service.py tests/test_api_isin_metadata.py
```

### Test Coverage

Current coverage: **95%** (152 tests)

To view detailed coverage:
```bash
uv run pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Code Quality

### Linting and Formatting

The project uses **Ruff** for fast linting and formatting:

```bash
# Check for linting issues
uv run ruff check .

# Auto-fix fixable issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Pre-commit Best Practices

Before committing:
```bash
# 1. Format code
uv run ruff format .

# 2. Fix linting issues
uv run ruff check --fix .

# 3. Run tests
uv run pytest

# 4. Commit changes
git add .
git commit -m "Your message"
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

**1. Routers** (`app/routers/`):
- API endpoints and HTTP concerns
- Request validation via Pydantic
- Response formatting
- No business logic

**2. Services** (`app/services/`):
- Business logic and calculations
- No HTTP knowledge (can be used outside FastAPI)
- Pure Python functions
- Testable in isolation

**3. Models** (`app/models/`):
- Database schema via SQLAlchemy ORM
- Database constraints and indexes
- Timestamps and relationships

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Settings (Pydantic Settings)
│   ├── database.py            # Database connection and session
│   ├── constants.py           # Constants and enums (TransactionType, ISINType)
│   ├── exceptions.py          # Custom exceptions
│   ├── models/                # SQLAlchemy models (database layer)
│   │   ├── transaction.py     # Transaction model
│   │   ├── position_value.py  # Position value model
│   │   └── isin_metadata.py   # ISIN metadata model
│   ├── schemas/               # Pydantic schemas (validation layer)
│   │   ├── transaction.py     # Transaction request/response schemas
│   │   ├── analytics.py       # Analytics response schemas
│   │   ├── position_value.py  # Position value schemas
│   │   └── isin_metadata.py   # ISIN metadata schemas
│   ├── routers/               # API route handlers (HTTP layer)
│   │   ├── transactions.py    # Transaction CRUD endpoints
│   │   ├── analytics.py       # Analytics endpoints
│   │   ├── position_values.py # Position value endpoints
│   │   └── isin_metadata.py   # ISIN metadata endpoints
│   └── services/              # Business logic (service layer)
│       ├── transaction_service.py  # Transaction operations
│       ├── cost_basis_service.py   # Cost basis calculations
│       ├── position_value_service.py  # Position value operations
│       └── isin_metadata_service.py   # ISIN metadata operations
├── alembic/                   # Database migrations
│   ├── versions/              # Migration files
│   ├── env.py                 # Alembic environment
│   └── script.py.mako         # Migration template
├── tests/                     # Test suite (95% coverage, 152 tests)
│   ├── conftest.py           # Test fixtures
│   ├── test_transaction_service.py
│   ├── test_cost_basis_service.py
│   ├── test_position_value_service.py
│   ├── test_isin_metadata_service.py
│   ├── test_api_transactions.py
│   ├── test_api_analytics.py
│   ├── test_api_position_values.py
│   ├── test_api_isin_metadata.py
│   ├── test_position_value_cleanup.py
│   └── test_schemas.py
├── .env                       # Environment variables (gitignored)
├── .env.example              # Environment template
├── alembic.ini               # Alembic configuration
├── pyproject.toml            # Dependencies and project metadata
├── uv.lock                   # Dependency lock file
└── portfolio.db              # SQLite database (gitignored)
```

### Key Design Patterns

**Dependency Injection**: Database sessions injected via FastAPI's `Depends(get_db)`

```python
@router.get("/transactions")
def list_transactions(db: Session = Depends(get_db)):
    # db session automatically provided and closed
    ...
```

**Schema Separation**:
- `models/`: SQLAlchemy ORM models (database layer)
- `schemas/`: Pydantic models (API/validation layer)
- Never mix these - Pydantic for validation, SQLAlchemy for persistence

**Service Layer Pattern**: All business logic in `services/`, routers are thin wrappers

### Cost Basis Calculation Logic

The system uses the **Average Cost Method** for calculating cost basis:

**BUY transactions**:
```
total_cost += (price_per_unit × units) + fee
total_units += units
average_cost = total_cost / total_units
```

**SELL transactions**:
```
proportion = units_sold / total_units
cost_removed = total_cost × proportion
realized_gain = (sell_price × units - fee) - cost_removed
total_cost -= cost_removed
total_units -= units_sold
```

**Critical**: Transactions must be processed chronologically (`ORDER BY date ASC`) for accurate calculations.

### Financial Precision

**Always use `Decimal`** for monetary values:

```python
from decimal import Decimal

# Correct
fee = Decimal("1.50")

# Wrong - floating point errors
fee = 1.50  # Never use float for money!
```

Database columns are `Numeric(10, 2)` for fees, `Numeric(10, 4)` for prices/units.

## Common Scenarios

### Adding a New Field to Transaction

1. Update `app/models/transaction.py` (add SQLAlchemy column)
2. Update `app/schemas/transaction.py` (add Pydantic field)
3. Generate migration: `uv run alembic revision --autogenerate -m "add_field_name"`
4. Review generated migration in `alembic/versions/`
5. Apply: `uv run alembic upgrade head`
6. Update tests as needed

### Adding a New Analytics Endpoint

1. Add calculation function in `app/services/cost_basis_service.py`
2. Add response schema in `app/schemas/analytics.py`
3. Add route in `app/routers/analytics.py`
4. Write tests
5. Document in API docs (automatic via FastAPI)

### Modifying Cost Basis Logic

All cost basis calculations are in `app/services/cost_basis_service.py`:

- `calculate_cost_basis()`: Average cost for one ISIN
- `calculate_current_holdings()`: All holdings
- `calculate_realized_gains()`: P&L from sells
- `get_portfolio_summary()`: Complete portfolio metrics

**Important**: Maintain chronological transaction processing when modifying.

### Managing ISIN Metadata

ISIN metadata provides asset names and types for ISINs:

**Add metadata for a new ISIN**:
```bash
curl -X POST http://localhost:8000/api/v1/isin-metadata \
  -H "Content-Type: application/json" \
  -d '{
    "isin": "IE00B4L5Y983",
    "name": "iShares Core MSCI Emerging Markets ETF",
    "type": "STOCK"
  }'
```

**Update existing metadata**:
```bash
curl -X PUT http://localhost:8000/api/v1/isin-metadata/IE00B4L5Y983 \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name"}'
```

**Filter by asset type**:
```bash
# Get all stocks
curl "http://localhost:8000/api/v1/isin-metadata?type=STOCK"

# Get all bonds
curl "http://localhost:8000/api/v1/isin-metadata?type=BOND"
```

**Key Points**:
- Metadata is independent of transactions (no foreign key relationship)
- ISIN is automatically normalized to uppercase
- Type must be: `STOCK`, `BOND`, or `REAL_ASSET`
- Use UPSERT endpoint for bulk imports: `POST /isin-metadata/upsert`

## Troubleshooting

### Port Already in Use

**Error**: `[Errno 48] error while attempting to bind on address ('0.0.0.0', 8000)`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uv run uvicorn app.main:app --reload --port 8001
```

### Database Locked

**Error**: `sqlite3.OperationalError: database is locked`

**Solution**:
- Close all database browser connections
- Restart the backend server
- SQLite WAL mode is already enabled to prevent this

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Make sure you're in the backend directory
cd backend

# Reinstall dependencies
uv sync --all-extras

# Or with pip
pip install -e .
```

### Migration Errors

**Error**: `alembic.util.exc.CommandError: Target database is not up to date`

**Solution**:
```bash
# Check current revision
uv run alembic current

# Apply pending migrations
uv run alembic upgrade head
```

### CORS Issues

If frontend gets CORS errors:

1. Update `CORS_ORIGINS` in `.env`:
   ```env
   CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
   ```

2. Restart the backend server

3. Verify CORS headers in browser DevTools (Network tab)

### Tests Failing

```bash
# Run tests with verbose output to see failures
uv run pytest -v

# Run specific failing test
uv run pytest tests/test_file.py::test_name -v

# Check if database is clean
rm test.db
uv run pytest
```

## Deployment Considerations

### Preparing for AWS Deployment

This backend is structured for containerized deployment:

**1. Create a Dockerfile** (in `backend/`):
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install UV
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev

# Copy application code
COPY . .

# Run migrations and start server
CMD uv run alembic upgrade head && \
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**2. Environment Variables for Production**:
```env
DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/dbname
DEBUG=False
CORS_ORIGINS=["https://your-frontend-domain.com"]
```

**3. Database Migration**:
- Local dev: SQLite (`portfolio.db`)
- Production: PostgreSQL (AWS RDS)
- Change only `DATABASE_URL`, code remains the same

**4. Security Checklist**:
- Set `DEBUG=False` in production
- Use secrets manager for sensitive env vars
- Enable HTTPS/TLS
- Set up proper CORS origins
- Use connection pooling for PostgreSQL

## Performance Tips

1. **Database Indexes**: Already optimized with indexes on `date`, `isin`, and `(date, isin)`
2. **Connection Pooling**: SQLAlchemy pool is configured automatically
3. **Query Optimization**: Use `.filter()` before `.all()` to minimize data transfer
4. **Caching**: Consider Redis for frequently accessed analytics
5. **Async**: Current implementation is sync (adequate for single-user); can migrate to async SQLAlchemy for higher concurrency

## Additional Resources

### Official Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/) - SQL toolkit and ORM
- [Alembic Documentation](https://alembic.sqlalchemy.org/) - Database migrations
- [Pydantic Documentation](https://docs.pydantic.dev/) - Data validation
- [UV Documentation](https://docs.astral.sh/uv/) - Python package manager

### Project Documentation
- **Main README**: [`../README.md`](../README.md) - Project overview and quick start
- **Frontend README**: [`../frontend/README.md`](../frontend/README.md) - Frontend documentation
- **Development Guide**: [`../CLAUDE.md`](../CLAUDE.md) - Claude Code development guidance

---

**Need Help?**
- Check the [troubleshooting section](#troubleshooting) above
- Review the main [project README](../README.md) for contribution guidelines
- Open an issue on GitHub with detailed information
