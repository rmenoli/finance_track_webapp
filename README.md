# ETF Portfolio Tracker

![Deploy Status](https://github.com/rmenoli/finance_track_webapp/workflows/Deploy%20to%20AWS/badge.svg)

A full-stack web application for tracking ETF portfolio transactions with automatic cost basis calculations using the average cost method.

**Single-user system** | **No authentication required** | **Local-first with cloud-ready architecture**

---

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [CI/CD Pipeline](#cicd-pipeline)
- [Documentation](#documentation)

---

## Overview

### Features

**Portfolio Management**
- ✅ Track BUY/SELL transactions across multiple brokers
- ✅ Automatic cost basis calculation (average cost method)
- ✅ Real-time portfolio analytics and holdings
- ✅ ISIN validation and date range filtering
- ✅ Persistent position value tracking with manual entry
- ✅ ISIN metadata management (asset names and types)
- ✅ Asset names displayed in holdings tables
- ✅ Portfolio distribution pie chart with interactive visualization
- ✅ Other assets tracking (crypto, cash accounts, CD, pension funds)
- ✅ Multi-currency support with backend Decimal precision (EUR/CZK)
- ✅ Other assets distribution visualization with pie chart
- ✅ User-friendly exchange rate input with onBlur/Enter save pattern
- ✅ **Historical snapshots** - Capture point-in-time portfolio state with preserved exchange rates
- ✅ **Portfolio growth tracking** - Automatic calculation of absolute and percentage changes from baseline
- ✅ **Time-series visualization** - Area chart displaying portfolio value over time with growth indicators
- ✅ **Snapshot management** - Exchange rate display in snapshots table with hover-to-delete functionality
- ✅ **Bulk CSV import** - Import DEGIRO transactions from CSV with detailed error reporting
- ✅ **Snapshot CSV import** - Bulk import historical snapshot data from CSV files

**User Experience**
- ✅ Clean, responsive React UI
- ✅ Interactive API documentation (Swagger UI)
- ✅ Fast development with hot reload
- ✅ Comprehensive test coverage (95%, 277 tests)

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, SQLAlchemy 2.0, Neon PostgreSQL (prod) / SQLite (dev), Alembic, Pydantic |
| **Frontend** | React 18, Vite, React Router v6, CSS, Chart.js |
| **Testing** | Pytest (245 tests, 95% coverage) |
| **Tools** | UV (Python), npm (Node.js), Ruff (linting) |

---

## Quick Start

### Prerequisites

- **Python 3.11+** (3.12 recommended)
- **Node.js 18+** (20+ recommended)
- **UV** (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Installation

```bash
# Clone the repository
git clone https://github.com/rmenoli/finance_track_webapp.git
cd finance_track_webapp

# Backend setup
cd backend
uv sync --all-extras
uv run alembic upgrade head

# Frontend setup (in a new terminal)
cd frontend
npm install
```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Access the application:**
- 🌐 Frontend: http://localhost:3000
- 🔌 Backend API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs

---

## Project Structure

```
finance_track_webapp/
├── backend/                           # FastAPI backend
│   ├── app/                          # Application code
│   │   ├── routers/                  # API endpoints
│   │   ├── services/                 # Business logic
│   │   ├── models/                   # Database models
│   │   └── schemas/                  # Pydantic schemas
│   ├── alembic/                      # Database migrations
│   │   └── versions/                 # Migration files
│   ├── tests/                        # Backend tests (245 tests, 95% coverage)
│   ├── pyproject.toml                # Python dependencies
│   ├── uv.lock                       # Dependency lock file
│   ├── alembic.ini                   # Alembic configuration
│   ├── portfolio.db                  # SQLite database (gitignored)
│   └── README.md                     # 📖 Backend documentation
│
├── frontend/                          # React frontend
│   ├── src/
│   │   ├── components/               # React components
│   │   ├── pages/                    # Page components
│   │   └── services/                 # API client
│   ├── package.json                  # Node dependencies
│   ├── vite.config.js                # Vite configuration
│   ├── .env.development              # Development environment
│   ├── .env.production               # Production environment
│   └── README.md                     # 📖 Frontend documentation
│
├── CLAUDE.md                         # Development guide for Claude Code
└── README.md                         # This file (high-level overview)
```

---

## Development

### Backend Development

All backend commands run from the `backend/` directory:

```bash
cd backend

# Start dev server with auto-reload
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
uv run pytest -v

# Code formatting
uv run ruff format .
uv run ruff check --fix .

# Database migrations
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

**📖 Full backend documentation:** [`backend/README.md`](backend/README.md)

### Frontend Development

All frontend commands run from the `frontend/` directory:

```bash
cd frontend

# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

**📖 Full frontend documentation:** [`frontend/README.md`](frontend/README.md)

### Code Quality

**Backend:**
```bash
cd backend
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run pytest --cov=app   # Test with coverage
```

**Frontend:**
```bash
cd frontend
npm run lint               # ESLint (if configured)
npm run build              # Verify build works
```

---

## Testing

### Backend Tests

95% coverage across 245 tests:

```bash
cd backend

# Run all tests
uv run pytest -v

# Run with coverage report
uv run pytest --cov=app --cov-report=html

# Run specific test categories
uv run pytest tests/test_api_transactions.py          # API tests
uv run pytest tests/test_cost_basis_service.py        # Business logic tests
uv run pytest tests/test_api_snapshots.py              # Snapshot API tests (7 tests with growth tracking)
uv run pytest tests/test_asset_snapshot_service.py    # Snapshot service tests (19 tests)
uv run pytest tests/test_schemas.py                   # Validation tests
```

### Manual Testing

1. Start both backend and frontend servers
2. Navigate to http://localhost:3000
3. Test key workflows:
   - Create BUY transaction
   - View portfolio summary
   - Create SELL transaction
   - Check realized gains
   - Filter transactions by ISIN/broker/date

---

## Deployment

### Local Development

- **Backend**: Uvicorn server on port 8000
- **Database**: SQLite (`backend/portfolio.db`)
- **Frontend**: Vite dev server on port 3000
- **API Proxy**: Vite proxies `/api/*` to backend (no CORS issues)

### Production (AWS)

**Current production setup:**

**Infrastructure:**
- **Frontend**: S3 + CloudFront (CDN with HTTPS)
  - Static React build files served from S3
  - CloudFront handles HTTPS termination
  - CloudFront routes `/api/*` to Lambda backend
- **Backend**: AWS Lambda + Mangum (ASGI adapter)
  - FastAPI packaged as Docker image (ECR)
  - Neon PostgreSQL (free tier, serverless) as persistent database
  - Alembic migrations run at CI/CD deploy time
- **Database**: Neon PostgreSQL (free tier)
  - 0.5 GiB storage, serverless compute (scales to zero)
  - Connection via `DATABASE_URL` env var on Lambda

**Key Configuration:**
- Frontend uses relative paths `/api/v1/*`
- CloudFront routes these to Lambda backend
- No CORS issues (same-origin from browser perspective)
- CI/CD sets `VITE_API_URL=/api/v1` during build
- CI/CD runs `alembic upgrade head` against Neon before deploying Lambda

---

## CI/CD Pipeline

### Automated Deployment

The project includes a GitHub Actions workflow that automatically deploys to AWS when PRs are merged to the main branch.

**Pipeline Flow:**
```
PR Merged → Run Tests → Run Alembic Migrations (Neon) →
Build Frontend → Deploy to S3 → Deploy Lambda (ECR) →
Verify Health → Complete ✓
```

**Features:**
- ✅ Automatic deployment on PR merge to `main`
- ✅ Backend tests run before deployment (303 tests, 95% coverage)
- ✅ Alembic migrations run against Neon PostgreSQL
- ✅ Frontend builds and deploys to S3 with CloudFront invalidation
- ✅ Backend Docker image built and pushed to ECR, Lambda updated
- ✅ Health check verification after deployment
- ✅ Manual deployment trigger available

### Setup Instructions

**Prerequisites:**
1. AWS infrastructure deployed (S3, EC2, CloudFront) - see [`DEPLOYMENT.md`](DEPLOYMENT.md)
2. IAM user created with S3 and CloudFront permissions
3. SSH key for EC2 access (dedicated for CI/CD)

**GitHub Secrets Required:**

| Secret Name | Description |
|------------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `AWS_REGION` | AWS region (e.g., `us-east-1`) |
| `S3_BUCKET_NAME` | S3 bucket name for frontend |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront distribution ID |
| `CLOUDFRONT_DOMAIN` | CloudFront domain for health check |
| `ECR_REGISTRY` | ECR registry URL |
| `ECR_REPOSITORY` | ECR repository name |
| `LAMBDA_FUNCTION_NAME` | Lambda function name |
| `NEON_DATABASE_URL` | Neon PostgreSQL connection string |
| `CODECOV_TOKEN` | (Optional) Codecov token |

**Setup Steps:**
1. Create IAM user with S3/CloudFront/ECR/Lambda permissions
2. Create Neon PostgreSQL project (free tier) and copy connection string
3. Add all secrets to GitHub repository (Settings → Secrets and variables → Actions)
4. Set `DATABASE_URL` env var on Lambda (Neon connection string)
5. Merge a PR to `main` or manually trigger workflow

**Manual Deployment:**
1. Go to **Actions** tab in GitHub
2. Select **"Deploy to AWS"** workflow
3. Click **"Run workflow"** → Select branch → **"Run workflow"**

### Monitoring

**View Deployments:**
- Go to repository **Actions** tab
- Click on a workflow run to see logs
- Green checkmarks = success, Red X = failure

**Deployment Badge:**
- Shows current deployment status (success/failure)
- Located at top of README
- Updates automatically after each deployment

**📖 Complete CI/CD documentation:** [`CI_CD.md`](CI_CD.md)
- Setup instructions with screenshots
- IAM user creation guide
- Troubleshooting common issues
- Security best practices
- Rollback procedures

---

## Documentation

### Quick Links

- **Backend API Docs**: http://localhost:8000/docs (Swagger UI)
- **Backend README**: [`backend/README.md`](backend/README.md) - Full backend documentation
- **Frontend README**: [`frontend/README.md`](frontend/README.md) - Full frontend documentation
- **Development Guide**: [`CLAUDE.md`](CLAUDE.md) - Guide for Claude Code development

### API Overview

All endpoints are prefixed with `/api/v1`

#### Transaction Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/transactions` | Create new transaction |
| GET | `/transactions` | List all transactions (with filters) |
| GET | `/transactions/{id}` | Get specific transaction |
| PUT | `/transactions/{id}` | Update transaction |
| DELETE | `/transactions/{id}` | Delete transaction |
| POST | `/transactions/degiro-import-csv-transactions` | **Bulk import DEGIRO transactions from CSV** - Returns detailed success/failure report with row-by-row errors |

#### Analytics Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/portfolio-summary` | Complete portfolio overview (includes holdings, total invested, total fees) |

#### Position Value Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/position-values` | Create or update position value (UPSERT) |
| GET | `/position-values` | List all position values |

#### ISIN Metadata Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/isin-metadata` | Create ISIN metadata (name, type) |
| GET | `/isin-metadata?type={type}` | List all ISIN metadata (with optional type filter) |
| GET | `/isin-metadata/{isin}` | Get ISIN metadata by ISIN |
| PUT | `/isin-metadata/{isin}` | Update ISIN metadata |
| DELETE | `/isin-metadata/{isin}` | Delete ISIN metadata |

#### Other Assets Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/other-assets` | Create or update other asset (UPSERT) |
| GET | `/other-assets?include_investments={bool}` | List all other assets (optionally include synthetic investments row) |
| DELETE | `/other-assets/{type}?asset_detail={detail}` | Delete other asset |

#### Settings Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/settings/exchange-rate` | Get current exchange rate (EUR/CZK) |
| POST | `/settings/exchange-rate` | Update exchange rate (UPSERT) |

#### Asset Snapshot Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/snapshots` | Create snapshot of current asset state (investments + other assets) |
| GET | `/snapshots` | List all snapshots (with optional date range and asset type filters) |
| GET | `/snapshots/summary` | Get aggregated summary with growth tracking (absolute and % changes from oldest) and average monthly increment |
| DELETE | `/snapshots/{snapshot_date}` | Delete snapshots by full datetime (requires ISO 8601 format with time component) |
| POST | `/snapshots/import-csv` | **Bulk import historical snapshots from CSV** - Accepts CSV with columns: snapshot_date, asset_type, asset_detail, currency, value, exchange_rate, value_eur |

**Note**: Snapshots capture point-in-time portfolio state with preserved exchange rates. The summary endpoint includes automatic calculation of portfolio growth from the oldest snapshot in the filtered dataset, including `avg_monthly_increment` (normalized 30-day growth rate in EUR). CSV import allows bulk importing of historical snapshot data with detailed error reporting per row.

**Frontend Features**:
- Exchange rate display in snapshots table (format: "Rate: 25.50 CZK/EUR")
- Hover-to-delete functionality with red X button on each row
- Confirmation dialog before deletion
- Automatic list refresh after successful deletion
- CSV import button for bulk importing historical snapshot data
- Detailed import results with success/failure counts and per-row error reporting

**CSV Import Features** (Transactions & Snapshots):
- File picker accepts .csv files only
- Shows "Importing..." state during upload
- Displays color-coded results (green = success, yellow = partial, red = error)
- Lists specific errors with row numbers and validation details
- Auto-refreshes list after successful imports
- Dismissible results card

**Full interactive API documentation:** http://localhost:8000/docs (Swagger UI)

---

## Common Issues

### "Failed to fetch" Error (Development)

**Symptom**: Frontend shows network errors when connecting to backend.

**Solution**:
```bash
# 1. Verify backend is running on correct port
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# 2. Check backend is using --host 0.0.0.0
# Correct:
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production CORS Error

**Symptom**: Production frontend shows CORS errors like:
```
Access to fetch at 'http://localhost:8000/api/v1/...' from origin 'https://CLOUDFRONT-DOMAIN'
has been blocked by CORS policy: Permission was denied for this request to access
the 'unknown' address space.
```

**Root Cause**: Frontend build is using hardcoded `localhost:8000` instead of relative paths `/api/v1`.

**Solution**:

1. **Verify GitHub Actions workflow** (`.github/workflows/deploy.yml`):
   ```yaml
   - name: Build frontend
     env:
       VITE_API_URL: /api/v1  # Must be present
     run: |
       cd frontend
       npm ci
       npm run build
   ```

2. **Verify API client** (`frontend/src/services/api.js`):
   ```javascript
   const API_BASE_URL = import.meta.env.VITE_API_URL;

   if (!API_BASE_URL) {
     throw new Error('VITE_API_URL environment variable is not set.');
   }
   ```

3. **Deploy and verify**:
   - Push changes to main branch (triggers CI/CD)
   - Check browser Network tab after deployment
   - API calls should go to `/api/v1/*` (not `localhost:8000`)

**📖 Detailed fix guide:** See [`CLAUDE.md`](CLAUDE.md#troubleshooting)

### Port Already in Use

```bash
# Find and kill process on port 8000
lsof -i :8000
kill -9 <PID>

# Or use a different port
cd backend
uv run uvicorn app.main:app --reload --port 8001
```

### Database Issues

```bash
# Reset database (destructive - deletes all data)
cd backend
rm portfolio.db
uv run alembic upgrade head
```

**📖 Full troubleshooting guide:** See [`backend/README.md`](backend/README.md#troubleshooting)

---

## Architecture Highlights

### Three-Layer Backend Architecture

```
┌─────────────┐
│   Routers   │  ← API endpoints (FastAPI routes)
└─────────────┘
      ↓
┌─────────────┐
│  Services   │  ← Business logic (cost basis calculations)
└─────────────┘
      ↓
┌─────────────┐
│   Models    │  ← Data layer (SQLAlchemy ORM)
└─────────────┘
```

**Key principles:**
- **Separation of concerns**: Each layer has a single responsibility
- **Testability**: Business logic isolated in services (96% test coverage)
- **Maintainability**: Clear boundaries between HTTP, logic, and data layers

### Cost Basis Calculation

Uses the **Average Cost Method**:

```python
# BUY: Add to total cost and units
total_cost += (price_per_unit × units) + fee
average_cost = total_cost / total_units

# SELL: Remove proportional cost basis
proportion = units_sold / total_units
cost_removed = total_cost × proportion
realized_gain = (sell_price × units - fee) - cost_removed
```

**Critical**: Transactions processed chronologically for accuracy.

**📖 Detailed architecture documentation:** See [`backend/README.md`](backend/README.md#architecture)

---

## Project Status

**Current Version**: Development
**Test Coverage**: 95% (277 tests)
**Frontend Pages**: 7 pages (Investment Dashboard, Transactions, Add/Edit Transaction, ISIN Metadata Management, Add/Edit ISIN Metadata, Other Assets, Snapshots with Growth Tracking)
**Backend Endpoints**: 23 endpoints (6 transaction, 1 analytics, 2 position values, 5 ISIN metadata, 3 other assets, 2 settings, 5 snapshots) - includes CSV import for transactions and snapshots

---

## Contributing

### Development Workflow

1. Create a feature branch from `main`
2. Make changes with appropriate tests
3. Run linting and formatting tools
4. Ensure all tests pass
5. Commit with descriptive messages
6. Create pull request with clear description

### Code Quality Standards

- **Backend**: 90%+ test coverage required, Ruff-compliant code
- **Frontend**: Component-scoped CSS, functional components with hooks
- **Git**: Descriptive commit messages, atomic commits
- **Documentation**: Update relevant README files for significant changes

### Testing Standards

**Backend Testing**:
```bash
cd backend
uv run pytest --cov=app --cov-report=term-missing
# Minimum 90% coverage required
```

**Frontend Testing**:
- Manual testing on major browsers
- Verify responsive design (mobile/tablet/desktop)
- Test all user workflows end-to-end

---

## License

This project is licensed under the MIT License.

---

## Support

For issues and questions:
- Create an issue on GitHub with detailed description
- Check the troubleshooting sections:
  - [Backend troubleshooting](backend/README.md#troubleshooting)
  - [Frontend troubleshooting](frontend/README.md#troubleshooting)
  - [Common issues](#common-issues) (above)
- Review interactive API documentation at http://localhost:8000/docs
- Consult [CLAUDE.md](CLAUDE.md) for development guidance

---

**Happy Tracking! 📈**
