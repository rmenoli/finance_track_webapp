# ETF Portfolio Tracker

A full-stack web application for tracking ETF portfolio transactions with automatic cost basis calculations using the average cost method.

**Stack**: FastAPI backend + React frontend (Vite)

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Backend Setup](#backend-setup)
- [Frontend Setup](#frontend-setup)
- [Development Workflow](#development-workflow)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

## Features

### Backend
- **Transaction Management**: RESTful API for ETF transaction CRUD operations
- **Cost Basis Tracking**: Automatic calculation using average cost method
- **Portfolio Analytics**:
  - Current holdings with average cost per unit
  - Total invested and fees paid
  - Realized gains/losses from sell transactions
  - Portfolio summary with all metrics
- **Advanced Filtering**: Filter transactions by ISIN, broker, type, date range
- **Pagination & Sorting**: Efficient data retrieval with customizable pagination
- **Data Validation**: ISIN format validation, date validation, positive value checks
- **API Documentation**: Auto-generated Swagger UI and ReDoc documentation

### Frontend
- **Dashboard**: Portfolio summary with key metrics and recent transactions
- **Transaction Management**: Add, edit, delete transactions with intuitive forms
- **Holdings View**: Current positions with cost basis details
- **Analytics**: Detailed cost basis and realized gains breakdowns
- **Filtering & Search**: Filter transactions by ISIN, broker, type, and date range
- **Responsive Design**: Clean UI that works on desktop and mobile
- **Client-Side Validation**: Immediate feedback matching backend rules

## Tech Stack

### Backend
- **Framework**: FastAPI 0.124.4
- **Database**: SQLite with SQLAlchemy 2.0.45
- **Migrations**: Alembic 1.17.2
- **Validation**: Pydantic 2.12.5
- **Package Manager**: UV (modern Python package manager)
- **Server**: Uvicorn 0.38.0

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Routing**: React Router v6
- **HTTP Client**: Fetch API
- **Styling**: CSS (component-scoped)

## Prerequisites

Before you begin, ensure you have the following installed:

### Backend
- **Python 3.11+** (Python 3.12 recommended)
- **UV** package manager (recommended) or pip
- **Git** (for cloning the repository)

### Frontend
- **Node.js 18+** (Node.js 20+ recommended)
- **npm** (comes with Node.js)

### Installing UV (Backend Package Manager)

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
node --version
npm --version
```

## Quick Start

Clone the repository and start both servers:

```bash
# Clone the repository
git clone https://github.com/rmenoli/finance_track_webapp.git
cd finance_track_webapp

# Backend: Install dependencies and run migrations
uv sync --all-extras
uv run alembic upgrade head

# Backend: Start server (Terminal 1)
uv run uvicorn app.main:app --reload

# Frontend: Install dependencies and start dev server (Terminal 2)
cd frontend
npm install
npm run dev
```

Access the application:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Backend Setup

### Step 1: Install Dependencies

**Using UV (Recommended):**
```bash
# Install all dependencies including dev dependencies
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

### Step 2: Set Up the Database

The database will be automatically created when you run migrations.

```bash
# Apply database migrations (creates tables)
uv run alembic upgrade head
```

You should see output like:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 3ff3f0eefe40, initial_transaction_table
```

### Step 3: Start the Backend Server

```bash
# Development mode with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify the backend is running:
- Health check: http://localhost:8000/health
- API documentation: http://localhost:8000/docs

## Frontend Setup

### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

### Step 2: Install Dependencies

```bash
npm install
```

### Step 3: Configure Environment (Optional)

The default configuration connects to `http://localhost:8000`. If you need to change this:

**`.env.development`** (already configured):
```
VITE_API_URL=http://localhost:8000/api/v1
```

### Step 4: Start the Frontend Dev Server

```bash
npm run dev
```

The frontend will be available at http://localhost:3000

### Frontend Scripts

```bash
npm run dev      # Start development server (port 3000)
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint (if configured)
```

## Configuration

### Backend Environment Variables

The backend uses environment variables for configuration. A `.env` file has been created with default values.

**View/Edit `.env` file:**
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

**Configuration Options:**

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./portfolio.db` |
| `API_V1_PREFIX` | API version prefix | `/api/v1` |
| `PROJECT_NAME` | Application name | `ETF Portfolio Tracker` |
| `DEBUG` | Enable debug mode | `True` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:3000", "http://localhost:8000"]` |

### Frontend Environment Variables

The frontend uses Vite environment variables:

**`frontend/.env.development`** (development):
```env
VITE_API_URL=http://localhost:8000/api/v1
```

**`frontend/.env.production`** (production):
```env
VITE_API_URL=/api/v1
```

## Development Workflow

### Running Both Servers

**Terminal 1 - Backend:**
```bash
uv run uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Frontend Development

Navigate to http://localhost:3000 to see the React application. The frontend is configured to proxy API requests to the backend at http://localhost:8000.

**Vite features:**
- Hot Module Replacement (HMR) for instant updates
- Fast build times
- Auto-proxy to backend API

### Backend Development

The backend runs with auto-reload enabled. Any changes to Python files will trigger an automatic restart.

**API Documentation available at:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing the API

### Using the Interactive Documentation

FastAPI provides interactive API documentation out of the box:

1. **Swagger UI** (recommended for testing): http://localhost:8000/docs
2. **ReDoc** (better for reading): http://localhost:8000/redoc

### Manual Testing with curl

Below are comprehensive examples for testing all endpoints.

#### 1. Health Check

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{"status":"healthy"}
```

#### 2. Create a BUY Transaction

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

**Expected Response:**
```json
{
  "id": 1,
  "date": "2025-01-15",
  "isin": "IE00B4L5Y983",
  "broker": "Interactive Brokers",
  "fee": "1.50",
  "price_per_unit": "450.2500",
  "units": "10.0000",
  "transaction_type": "BUY",
  "created_at": "2025-12-16T22:43:45.019661",
  "updated_at": "2025-12-16T22:43:45.019663"
}
```

#### 3. Create Multiple Transactions (for testing)

```bash
# Second BUY transaction (same ISIN, different price)
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-02-01",
    "isin": "IE00B4L5Y983",
    "broker": "Interactive Brokers",
    "fee": 1.50,
    "price_per_unit": 460.00,
    "units": 5.0,
    "transaction_type": "BUY"
  }'

# Different ISIN
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-02-05",
    "isin": "US0378331005",
    "broker": "Degiro",
    "fee": 2.00,
    "price_per_unit": 175.50,
    "units": 20.0,
    "transaction_type": "BUY"
  }'

# SELL transaction
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-02-10",
    "isin": "IE00B4L5Y983",
    "broker": "Interactive Brokers",
    "fee": 1.50,
    "price_per_unit": 470.00,
    "units": 3.0,
    "transaction_type": "SELL"
  }'
```

#### 4. List All Transactions

```bash
curl http://localhost:8000/api/v1/transactions
```

#### 5. List Transactions with Filters

```bash
# Filter by ISIN
curl "http://localhost:8000/api/v1/transactions?isin=IE00B4L5Y983"

# Filter by transaction type
curl "http://localhost:8000/api/v1/transactions?transaction_type=BUY"

# Filter by broker
curl "http://localhost:8000/api/v1/transactions?broker=Interactive%20Brokers"

# Filter by date range
curl "http://localhost:8000/api/v1/transactions?start_date=2025-01-01&end_date=2025-02-15"

# Multiple filters with pagination
curl "http://localhost:8000/api/v1/transactions?isin=IE00B4L5Y983&transaction_type=BUY&skip=0&limit=10"

# Sort by date ascending
curl "http://localhost:8000/api/v1/transactions?sort_by=date&sort_order=asc"
```

#### 6. Get Single Transaction

```bash
# Replace {id} with actual transaction ID
curl http://localhost:8000/api/v1/transactions/1
```

#### 7. Update Transaction

```bash
# Update specific fields only
curl -X PUT http://localhost:8000/api/v1/transactions/1 \
  -H "Content-Type: application/json" \
  -d '{
    "fee": 2.00,
    "broker": "Updated Broker Name"
  }'
```

#### 8. Delete Transaction

```bash
curl -X DELETE http://localhost:8000/api/v1/transactions/1
```

**Expected Response:** HTTP 204 No Content (empty response)

#### 9. Get Cost Basis for Specific ISIN

```bash
curl http://localhost:8000/api/v1/analytics/cost-basis/IE00B4L5Y983
```

**Expected Response:**
```json
{
  "isin": "IE00B4L5Y983",
  "total_units": "12.0000",
  "total_cost": "6955.25",
  "average_cost_per_unit": "579.6042",
  "transactions_count": 3,
  "current_market_value": null,
  "unrealized_gain_loss": null
}
```

#### 10. Get All Cost Bases

```bash
curl http://localhost:8000/api/v1/analytics/cost-basis
```

#### 11. Get Current Holdings

```bash
curl http://localhost:8000/api/v1/analytics/holdings
```

**Expected Response:**
```json
[
  {
    "isin": "IE00B4L5Y983",
    "units": "12.0000",
    "average_cost_per_unit": "579.6042",
    "total_cost": "6955.25"
  },
  {
    "isin": "US0378331005",
    "units": "20.0000",
    "average_cost_per_unit": "175.60",
    "total_cost": "3512.00"
  }
]
```

#### 12. Get Realized Gains

```bash
# All realized gains
curl http://localhost:8000/api/v1/analytics/realized-gains

# Realized gains for specific ISIN
curl "http://localhost:8000/api/v1/analytics/realized-gains?isin=IE00B4L5Y983"
```

#### 13. Get Portfolio Summary

```bash
curl http://localhost:8000/api/v1/analytics/portfolio-summary
```

**Expected Response:**
```json
{
  "total_invested": "10023.25",
  "total_fees": "6.50",
  "holdings": [
    {
      "isin": "IE00B4L5Y983",
      "units": "12.0000",
      "average_cost_per_unit": "579.6042",
      "total_cost": "6955.25"
    },
    {
      "isin": "US0378331005",
      "units": "20.0000",
      "average_cost_per_unit": "175.60",
      "total_cost": "3512.00"
    }
  ],
  "realized_gains": "108.50",
  "realized_losses": "0",
  "net_realized_gains": "108.50",
  "unique_isins": 2
}
```

### Testing with Python requests

Create a test script `test_api.py`:

```python
import requests
from datetime import date

BASE_URL = "http://localhost:8000/api/v1"

# Create a transaction
transaction_data = {
    "date": str(date.today()),
    "isin": "IE00B4L5Y983",
    "broker": "Interactive Brokers",
    "fee": 1.50,
    "price_per_unit": 450.25,
    "units": 10.0,
    "transaction_type": "BUY"
}

response = requests.post(f"{BASE_URL}/transactions", json=transaction_data)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Get all transactions
response = requests.get(f"{BASE_URL}/transactions")
print(f"\nAll transactions: {response.json()}")

# Get portfolio summary
response = requests.get(f"{BASE_URL}/analytics/portfolio-summary")
print(f"\nPortfolio summary: {response.json()}")
```

Run the script:
```bash
uv run python test_api.py
```

### Testing with Postman

1. Import the API into Postman:
   - Open Postman
   - Go to Import > Link
   - Enter: `http://localhost:8000/openapi.json`
   - Click Import

2. All endpoints will be available in Postman with examples

## API Documentation

### Interactive Documentation

Once the server is running, you can access:

1. **Swagger UI**: http://localhost:8000/docs
   - Interactive API testing interface
   - Try out endpoints directly from the browser
   - See request/response schemas

2. **ReDoc**: http://localhost:8000/redoc
   - Clean, readable API documentation
   - Better for understanding API structure

### Endpoint Reference

#### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/transactions` | Create a new transaction |
| GET | `/api/v1/transactions` | List all transactions (with filters) |
| GET | `/api/v1/transactions/{id}` | Get transaction by ID |
| PUT | `/api/v1/transactions/{id}` | Update a transaction |
| DELETE | `/api/v1/transactions/{id}` | Delete a transaction |

#### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/cost-basis` | Get cost basis for all ISINs |
| GET | `/api/v1/analytics/cost-basis/{isin}` | Get cost basis for specific ISIN |
| GET | `/api/v1/analytics/holdings` | Get current holdings |
| GET | `/api/v1/analytics/realized-gains` | Get realized gains from sells |
| GET | `/api/v1/analytics/portfolio-summary` | Get full portfolio summary |

### Transaction Model

```json
{
  "date": "2025-01-15",           // Transaction date (YYYY-MM-DD)
  "isin": "IE00B4L5Y983",        // 12-character ISIN code
  "broker": "Interactive Brokers", // Broker name
  "fee": 1.50,                    // Transaction fee (>=0)
  "price_per_unit": 450.25,      // Price per unit (>0)
  "units": 10.0,                  // Number of units (>0)
  "transaction_type": "BUY"       // BUY or SELL
}
```

### Validation Rules

- **ISIN**: Must be exactly 12 characters (2 letters + 9 alphanumeric + 1 digit)
- **Date**: Cannot be in the future
- **Units**: Must be greater than 0
- **Price per unit**: Must be greater than 0
- **Fee**: Must be greater than or equal to 0
- **Transaction type**: Must be either "BUY" or "SELL"

## Database Management

### View Database Schema

```bash
# Connect to SQLite database
sqlite3 portfolio.db

# View tables
.tables

# View transactions table structure
.schema transactions

# Query transactions
SELECT * FROM transactions;

# Exit
.quit
```

### Create New Migration

After modifying models in `app/models/`:

```bash
# Generate migration automatically
uv run alembic revision --autogenerate -m "description of changes"

# Apply migration
uv run alembic upgrade head
```

### Rollback Migration

```bash
# Rollback one migration
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade <revision_id>

# Rollback all migrations
uv run alembic downgrade base
```

### View Migration History

```bash
uv run alembic history
```

### Reset Database

```bash
# Delete the database file
rm portfolio.db

# Recreate with migrations
uv run alembic upgrade head
```

## Development Workflow

### Code Formatting and Linting

The project uses **Ruff** for linting and formatting.

```bash
# Check for linting issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

### Running Tests (when available)

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html

# Run specific test file
uv run pytest tests/test_transactions.py

# Run with verbose output
uv run pytest -v
```

### Development Server with Live Reload

```bash
# The --reload flag enables auto-reload on code changes
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Debugging

Enable debug mode in `.env`:
```env
DEBUG=True
```

This will:
- Show detailed error messages
- Enable SQL query logging
- Provide more verbose output

## Troubleshooting

### Port Already in Use

**Error:**
```
ERROR: [Errno 48] error while attempting to bind on address ('0.0.0.0', 8000): address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uv run uvicorn app.main:app --reload --port 8001
```

### Database Locked Error

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```bash
# Close all connections to the database
# Restart the application
# Or use WAL mode (already enabled in this project)
```

### Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'app'
```

**Solution:**
```bash
# Make sure you're in the project root directory
pwd

# Reinstall dependencies
uv sync --all-extras

# Or install in editable mode
pip install -e .
```

### Migration Errors

**Error:**
```
alembic.util.exc.CommandError: Target database is not up to date
```

**Solution:**
```bash
# Check current revision
uv run alembic current

# Apply pending migrations
uv run alembic upgrade head
```

### UV Not Found

**Error:**
```
command not found: uv
```

**Solution:**
```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your terminal
# Or add UV to PATH manually
```

### Frontend "Failed to fetch" Error

**Error:** Frontend shows "Failed to fetch" or "Network Error"

**Common Causes:**

1. **Backend not running on correct port**
   ```bash
   # Check if backend is running on port 8000
   curl http://localhost:8000/health

   # Should return: {"status":"healthy"}
   ```

2. **Backend running on wrong port**
   ```bash
   # Check what's running on port 8000
   lsof -i :8000

   # Kill process on wrong port
   kill -9 <PID>

   # Start backend on correct port
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Backend not accessible**
   - Make sure backend is running with `--host 0.0.0.0` (not `127.0.0.1` only)
   - Check firewall settings
   - Verify `.env` has correct CORS settings

4. **Check both servers are running:**
   ```bash
   # Backend should be on port 8000
   curl http://localhost:8000/health

   # Frontend should be on port 3000
   curl http://localhost:3000
   ```

### CORS Issues

If you're getting CORS errors:

1. Update `CORS_ORIGINS` in `.env`:
```env
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000", "http://localhost:5173"]
```

2. Restart the backend server

3. Verify CORS headers in browser DevTools (Network tab)

## Project Structure

```
finance_track_webapp/
├── alembic/                    # Database migrations
│   ├── versions/               # Migration files
│   ├── env.py                  # Alembic environment
│   └── script.py.mako         # Migration template
├── app/                        # Backend application
│   ├── __init__.py
│   ├── main.py                # FastAPI application entry point
│   ├── config.py              # Application settings
│   ├── database.py            # Database connection and session
│   ├── constants.py           # Constants and enums
│   ├── exceptions.py          # Custom exceptions
│   ├── models/                # SQLAlchemy models
│   │   ├── __init__.py
│   │   └── transaction.py     # Transaction database model
│   ├── schemas/               # Pydantic schemas (validation)
│   │   ├── __init__.py
│   │   ├── transaction.py     # Transaction request/response schemas
│   │   └── analytics.py       # Analytics response schemas
│   ├── routers/               # API route handlers
│   │   ├── __init__.py
│   │   ├── transactions.py    # Transaction CRUD endpoints
│   │   └── analytics.py       # Analytics endpoints
│   └── services/              # Business logic
│       ├── __init__.py
│       ├── transaction_service.py  # Transaction operations
│       └── cost_basis_service.py   # Cost basis calculations
├── frontend/                   # Frontend application
│   ├── public/                # Static assets
│   │   └── vite.svg
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   │   ├── Layout.jsx / .css
│   │   │   ├── Navigation.jsx / .css
│   │   │   ├── TransactionForm.jsx / .css
│   │   │   ├── TransactionList.jsx / .css
│   │   │   ├── HoldingsTable.jsx / .css
│   │   │   └── PortfolioSummary.jsx / .css
│   │   ├── pages/             # Page components
│   │   │   ├── Dashboard.jsx / .css
│   │   │   ├── Transactions.jsx / .css
│   │   │   ├── Holdings.jsx / .css
│   │   │   ├── Analytics.jsx / .css
│   │   │   └── AddTransaction.jsx / .css
│   │   ├── services/          # API client
│   │   │   └── api.js         # Fetch-based API client
│   │   ├── App.jsx            # Main app component with routing
│   │   ├── main.jsx           # Entry point
│   │   ├── App.css            # App-level styles
│   │   └── index.css          # Global styles
│   ├── .env.development       # Development environment
│   ├── .env.production        # Production environment
│   ├── package.json           # Node dependencies
│   ├── vite.config.js         # Vite configuration
│   ├── index.html             # HTML entry point
│   └── README.md              # Frontend-specific README
├── tests/                     # Backend tests
│   ├── __init__.py
│   ├── conftest.py           # Test fixtures
│   ├── test_transaction_service.py
│   ├── test_cost_basis_service.py
│   ├── test_api_transactions.py
│   ├── test_api_analytics.py
│   └── test_schemas.py
├── .env                       # Backend environment variables
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore patterns
├── alembic.ini               # Alembic configuration
├── pyproject.toml            # Python dependencies and metadata
├── CLAUDE.md                 # Claude Code development guide
├── README.md                 # This file
└── portfolio.db              # SQLite database (created at runtime)
```

## Example Workflows

### Complete Test Workflow

```bash
# 1. Start the server
uv run uvicorn app.main:app --reload

# 2. In another terminal, create transactions
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-01-15", "isin": "IE00B4L5Y983", "broker": "IB", "fee": 1.50, "price_per_unit": 450.25, "units": 10.0, "transaction_type": "BUY"}'

curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-02-01", "isin": "IE00B4L5Y983", "broker": "IB", "fee": 1.50, "price_per_unit": 460.00, "units": 5.0, "transaction_type": "BUY"}'

curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -d '{"date": "2025-02-10", "isin": "IE00B4L5Y983", "broker": "IB", "fee": 1.50, "price_per_unit": 470.00, "units": 3.0, "transaction_type": "SELL"}'

# 3. Check portfolio summary
curl http://localhost:8000/api/v1/analytics/portfolio-summary

# 4. Check cost basis
curl http://localhost:8000/api/v1/analytics/cost-basis/IE00B4L5Y983

# 5. Check realized gains
curl http://localhost:8000/api/v1/analytics/realized-gains
```

## Testing

### Backend Tests

The backend has comprehensive test coverage (96%, 86 tests):

```bash
# Run all backend tests
uv run pytest

# Run with coverage report
uv run pytest --cov=app --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_cost_basis_service.py -v
```

### Manual Testing

1. Start both servers (backend and frontend)
2. Navigate to http://localhost:3000
3. Test key workflows:
   - Create BUY transaction
   - Create SELL transaction
   - View portfolio summary on dashboard
   - Filter transactions by ISIN/broker/type
   - Edit existing transaction
   - Delete transaction
   - View holdings and cost basis
   - Check realized gains in analytics

## Next Steps

### Potential Enhancements

1. **Add Authentication**: Implement user authentication for multi-user support
2. **Deploy**: Deploy to production (Heroku, AWS, Vercel, Digital Ocean, etc.)
3. **Additional Features**:
   - Dividend tracking
   - Multi-currency support with exchange rates
   - CSV import/export functionality
   - Real-time market data integration
   - Tax reporting and capital gains summaries
   - Charts and visualizations for portfolio performance
   - Mobile-responsive improvements
   - Dark mode theme

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section above
- Review the API documentation at `/docs`

---

**Happy Tracking! 📈**
