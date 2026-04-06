# Security & Cost Control Plan

## Context

The ETF Portfolio Tracker is internet-facing (CloudFront -> API Gateway -> Lambda -> Neon PostgreSQL) with **zero security controls**: no auth, no rate limiting, no Lambda concurrency limits, no API Gateway throttling, no budget alarm. An attacker or bot could invoke Lambda thousands of times, triggering unbounded costs. The budget target is $5/month.

## Actual Architecture

CloudFront -> Lambda Function URL (no API Gateway). The Lambda Function URL has `AuthType: NONE`, meaning it's publicly accessible even without CloudFront.

## Priority Levels

| Priority | Items | Type | Effort |
|----------|-------|------|--------|
| **P0** | Lambda concurrency + Budget alert | AWS CLI only | 5 min |
| **P1** | API key middleware + Budget killer Lambda | Code + AWS CLI | 30 min |

---

## P0: Prevent Cost Explosion (AWS CLI only, no code changes)

### P0.1: Set Lambda reserved concurrency to 5

Caps max parallel executions. Single most important control.

```bash
aws lambda put-function-concurrency \
  --function-name finance-tracker-backend \
  --reserved-concurrent-executions 5 \
  --profile etf-portfolio
```

### ~~P0.2: Set API Gateway throttling~~ — N/A (no API Gateway)

Architecture uses Lambda Function URL directly, not API Gateway. Throttling is handled by Lambda concurrency (P0.1) and API key middleware (P1.1).

### P0.2: Create AWS Budget with $5 threshold + email alert

Alerts at 80% ($4) and 100% ($5).

```bash
aws budgets create-budget \
  --account-id YOUR_ACCOUNT_ID \
  --budget '{
    "BudgetName": "finance-tracker-monthly",
    "BudgetLimit": {"Amount": "5", "Unit": "USD"},
    "TimeUnit": "MONTHLY",
    "BudgetType": "COST"
  }' \
  --notifications-with-subscribers '[
    {
      "Notification": {
        "NotificationType": "ACTUAL",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 80,
        "ThresholdType": "PERCENTAGE"
      },
      "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "YOUR_EMAIL"}]
    },
    {
      "Notification": {
        "NotificationType": "ACTUAL",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 100,
        "ThresholdType": "PERCENTAGE"
      },
      "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "YOUR_EMAIL"}]
    }
  ]' \
  --profile etf-portfolio
```

---

## P1: Prevent Abuse (Code Changes)

### P1.1: Add API Key Middleware

A simple `X-API-Key` header check. Not enterprise auth, but blocks bots/scanners.

**Files to modify:**

#### 1. `backend/app/config.py` - add `api_key` setting

Add after `cors_origins` (line 14):

```python
api_key: str = ""  # Empty = no auth (local dev)
```

#### 2. `backend/app/main.py` - add middleware after CORS block (line 173)

Insert between the `add_middleware(CORSMiddleware, ...)` call (line 167-173) and `# Include routers` (line 175).

Note: `root_path="/api"` (line 53) means internal routes don't include `/api`. Health endpoints are at `/health` and `/v1/health` (lines 197-198).

```python
@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    """Reject requests without a valid API key (when API_KEY is configured)."""
    if not settings.api_key:
        return await call_next(request)
    if request.url.path in ("/health", "/v1/health", "/"):
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    if request.headers.get("X-API-Key") != settings.api_key:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid or missing API key"},
        )
    return await call_next(request)
```

All needed imports (`Request`, `status`, `JSONResponse`) are already present in `main.py` (lines 7-9).

#### 3. `frontend/src/services/api.js` - add API key header

Add after `API_BASE_URL` check (line 6), create a centralized fetch wrapper:

```javascript
const API_KEY = import.meta.env.VITE_API_KEY || '';

function apiFetch(url, options = {}) {
  const headers = { ...options.headers };
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }
  return fetch(url, { ...options, headers });
}
```

Then replace every `fetch(` call in the file with `apiFetch(` (~25 occurrences across all API methods).

#### 4. `frontend/.env.development` - add empty key

Append: `VITE_API_KEY=`

#### 5. `frontend/.env.production` - add empty key placeholder

Append: `VITE_API_KEY=`

(Real value injected via GitHub secret at build time.)

#### 6. `.github/workflows/deploy.yml` - pass API key to frontend build (line 102-107)

Add `VITE_API_KEY` to the existing build step env:

```yaml
      - name: Build frontend
        env:
          VITE_API_URL: /api/v1
          VITE_API_KEY: ${{ secrets.API_KEY }}
```

#### 7. AWS + GitHub setup (manual, one-time)

```bash
# Generate a random key
API_KEY=$(openssl rand -hex 32)
echo "API_KEY: $API_KEY"

# Add to Lambda env vars via AWS Console:
#   Lambda -> Configuration -> Environment variables -> Add API_KEY

# Add to GitHub Secrets:
#   Repository -> Settings -> Secrets -> New: API_KEY = same value
```

#### 8. Backend tests - add API key middleware tests

Add tests in `backend/tests/test_api_key_middleware.py`:
- Request without key when `api_key=""` (empty) -> 200 (no auth)
- Request without key when `api_key` is set -> 401
- Request with correct key -> 200
- Request with wrong key -> 401
- Health endpoints bypass key check -> 200
- OPTIONS requests bypass key check -> 200

### P1.2: Budget Killer Lambda (optional safety net)

Auto-disables the main Lambda when budget is exceeded.

#### 1. Create `backend/budget_killer/handler.py`

```python
"""Triggered by SNS when AWS Budget exceeds threshold.
Sets main Lambda concurrency to 0 to prevent further costs.
"""

import json
import logging
import os

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAIN_FUNCTION_NAME = os.environ["MAIN_FUNCTION_NAME"]


def handler(event, context):
    logger.info("Budget alarm triggered: %s", json.dumps(event))
    client = boto3.client("lambda")
    client.put_function_concurrency(
        FunctionName=MAIN_FUNCTION_NAME,
        ReservedConcurrentExecutions=0,
    )
    logger.info("Disabled %s - concurrency set to 0", MAIN_FUNCTION_NAME)
    return {"statusCode": 200, "body": "Function disabled"}
```

#### 2. AWS setup (manual commands, all with `--profile etf-portfolio`)

1. Create SNS topic `finance-tracker-budget-alarm`
2. Create IAM role with `lambda:PutFunctionConcurrency` permission
3. Package and create the budget killer Lambda (simple zip deploy, not Docker)
4. Subscribe Lambda to SNS topic
5. Create a second AWS Budget that notifies the SNS topic at 100% threshold

Recovery after budget resets:
```bash
aws lambda put-function-concurrency \
  --function-name finance-tracker-backend \
  --reserved-concurrent-executions 5 \
  --profile etf-portfolio
```

---

## Implementation Order

| Step | What | Downtime |
|------|------|----------|
| 1 | P0.1: Lambda concurrency (once quota approved) | None |
| 2 | P0.2: AWS Budget alert | None |
| 3 | P1.1: API key middleware (backend + frontend + deploy config + tests) | Requires deploy |
| 4 | P1.2: Budget killer Lambda + SNS + wiring | None |

Steps 1, 2, and 4 are pure infrastructure (no code deployment). Step 3 is a single commit (backend + frontend must deploy together so the key matches).

---

## Verification

1. **Lambda concurrency**: `aws lambda get-function-concurrency --function-name finance-tracker-backend --profile etf-portfolio` -> `ReservedConcurrentExecutions: 5`
2. **Budget**: `aws budgets describe-budgets --account-id YOUR_ACCOUNT_ID --profile etf-portfolio`
4. **API key**: `curl -s https://YOUR_DOMAIN/api/v1/transactions` -> 401. Then `curl -s -H "X-API-Key: YOUR_KEY" https://YOUR_DOMAIN/api/v1/transactions` -> 200
5. **Health endpoint stays open**: `curl -s https://YOUR_DOMAIN/api/v1/health` -> 200 (no key needed)
6. **Frontend works**: Open the app in browser - should load and fetch data normally
7. **Tests pass**: `cd backend && uv run pytest -v`
8. **Budget killer** (optional): Test by manually publishing to SNS topic, verify main Lambda concurrency goes to 0
