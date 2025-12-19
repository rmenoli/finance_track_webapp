# ETF Portfolio Tracker

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

**User Experience**
- ✅ Clean, responsive React UI
- ✅ Interactive API documentation (Swagger UI)
- ✅ Fast development with hot reload
- ✅ Comprehensive test coverage (95%)

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, SQLAlchemy 2.0, SQLite, Alembic, Pydantic |
| **Frontend** | React 18, Vite, React Router v6, CSS |
| **Testing** | Pytest (152 tests, 95% coverage) |
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
│   ├── tests/                        # Backend tests (152 tests, 95% coverage)
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

95% coverage across 152 tests:

```bash
cd backend

# Run all tests
uv run pytest -v

# Run with coverage report
uv run pytest --cov=app --cov-report=html

# Run specific test categories
uv run pytest tests/test_api_transactions.py      # API tests
uv run pytest tests/test_cost_basis_service.py    # Business logic tests
uv run pytest tests/test_schemas.py               # Validation tests
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

### Current Setup (Local Development)

- **Backend**: Uvicorn server on port 8000
- **Database**: SQLite (`backend/portfolio.db`)
- **Frontend**: Vite dev server on port 3000

### AWS Deployment (Future)

The project structure is ready for containerized deployment:

**Backend (ECS/Lambda/EC2):**
- Containerize `backend/` directory
- Replace SQLite with RDS PostgreSQL
- Set environment variables for production
- Deploy with Dockerfile

**Frontend (S3 + CloudFront / ECS):**
- Build static assets: `npm run build`
- Deploy to S3 with CloudFront
- Or containerize and deploy alongside backend

**📖 Detailed deployment guide:** See [`backend/README.md`](backend/README.md#deployment-considerations)

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

#### Analytics Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/portfolio-summary` | Complete portfolio overview (includes holdings, total invested, total fees) |

#### Position Value Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/position-values` | Create or update position value (UPSERT) |
| GET | `/position-values` | List all position values |
| GET | `/position-values/{isin}` | Get position value by ISIN |
| DELETE | `/position-values/{isin}` | Delete position value |

#### ISIN Metadata Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/isin-metadata` | Create ISIN metadata (name, type) |
| POST | `/isin-metadata/upsert` | Create or update ISIN metadata |
| GET | `/isin-metadata?type={type}` | List all ISIN metadata (with optional type filter) |
| GET | `/isin-metadata/{isin}` | Get ISIN metadata by ISIN |
| PUT | `/isin-metadata/{isin}` | Update ISIN metadata |
| DELETE | `/isin-metadata/{isin}` | Delete ISIN metadata |

**Full interactive API documentation:** http://localhost:8000/docs (Swagger UI)

---

## Common Issues

### "Failed to fetch" Error

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
**Test Coverage**: 95% (152 tests)
**Frontend Pages**: 4 pages (Investment Dashboard, Transactions, Add/Edit Transaction, ISIN Metadata Management)
**Backend Endpoints**: 16 endpoints (5 transaction, 1 analytics, 4 position values, 6 ISIN metadata)

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
