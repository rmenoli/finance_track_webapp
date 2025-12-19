from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analytics, isin_metadata, position_values, transactions

# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    description="API for tracking ETF portfolio transactions with cost basis calculations",
    version="0.1.0",
    debug=settings.debug,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transactions.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)
app.include_router(isin_metadata.router, prefix=settings.api_v1_prefix)
app.include_router(position_values.router, prefix=settings.api_v1_prefix)


@app.get("/", tags=["root"])
def root():
    """Root endpoint with API information."""
    return {
        "message": "ETF Portfolio Tracker API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
