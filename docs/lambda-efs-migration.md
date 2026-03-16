# Lambda + EFS Migration Plan

**Goal:** Migrate the FastAPI backend from EC2 to AWS Lambda (Docker container) with SQLite persisted on EFS, reducing monthly AWS cost from ~$13 to ~$0.

**Architecture:** Lambda container wraps FastAPI via Mangum, receiving requests forwarded by CloudFront from `/api/*`. SQLite database lives on EFS mounted at `/mnt/efs/portfolio.db`, persisting across Lambda invocations. GitHub Actions builds and pushes a Docker image to ECR, then updates the Lambda function.

**Tech Stack:** FastAPI, Mangum, Docker, AWS Lambda, ECR, EFS, CloudFront, GitHub Actions

---

## Pre-requisites: Manual AWS Console Setup

These steps must be completed BEFORE running any code changes. They are one-time infrastructure tasks.

### Step A: Create ECR Repository
1. AWS Console → ECR → **Create repository**
2. Visibility: **Private**
3. Name: `finance-tracker-backend`
4. Keep all other defaults → **Create**
5. **Note the full registry URI** (e.g., `123456789012.dkr.ecr.eu-west-1.amazonaws.com/finance-tracker-backend`)

### Step B: Create EFS File System
1. AWS Console → EFS → **Create file system**
2. Name: `finance-tracker-db`
3. VPC: use the **default VPC** (same one EC2 uses)
4. Click **Create** (use defaults — regional storage, General Purpose)
5. **Note the File System ID** (e.g., `fs-0abc1234`)

### Step C: Create Security Groups
1. AWS Console → EC2 → Security Groups → **Create security group**

**Lambda security group:**
- Name: `finance-tracker-lambda-sg`
- VPC: default VPC
- Inbound rules: none
- Outbound rules: Add rule → Type: **NFS** (port 2049), Destination: **Custom** → (will fill with EFS SG below)

**EFS security group:**
- Name: `finance-tracker-efs-sg`
- VPC: default VPC
- Inbound rules: Type: **NFS** (port 2049), Source: **Custom** → select `finance-tracker-lambda-sg`
- Outbound rules: none needed

After creating both SGs:
- Edit the Lambda SG outbound rule → set destination to `finance-tracker-efs-sg`

### Step D: Add EFS Mount Targets
1. AWS Console → EFS → select your file system → **Network** tab
2. For **each availability zone** in your region, click **Manage** → ensure mount targets exist
3. Set each mount target's security group to `finance-tracker-efs-sg`

### Step E: Create EFS Access Point
1. In your EFS file system → **Access points** tab → **Create access point**
2. Root directory path: `/portfolio`
3. POSIX user: UID `1000`, GID `1000`
4. Root directory creation permissions: Owner UID `1000`, GID `1000`, Permissions `0755`
5. **Note the Access Point ARN**

### Step E.5: Push Initial Image to ECR

> Do this before Step F. You need an image in ECR to create the Lambda function.

```bash
# Authenticate Docker to ECR (via aws-vault)
aws-vault exec YOUR_PROFILE -- aws ecr get-login-password --region YOUR_REGION | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com

# Build the image — linux/amd64 required even on Apple Silicon
# --provenance=false prevents Docker BuildKit from adding OCI attestation manifests
# that Lambda does not support
cd backend
docker build --platform linux/amd64 --provenance=false -f Dockerfile.lambda -t finance-tracker-backend .

# Tag and push
docker tag finance-tracker-backend:latest \
  YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/finance-tracker-backend:latest

aws-vault exec YOUR_PROFILE -- docker push \
  YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com/finance-tracker-backend:latest
```

Verify it arrived: AWS Console → ECR → `finance-tracker-backend` → should show one image tagged `latest`.

### Step F: Create Lambda Function
1. AWS Console → Lambda → **Create function**
2. Choose: **Container image**
3. Function name: `finance-tracker-backend`
4. Container image URI: the ECR URI from Step E.5 (e.g. `123456789012.dkr.ecr.eu-west-1.amazonaws.com/finance-tracker-backend:latest`)
5. Architecture: `x86_64`
6. Click **Create function**

**After creation, configure in this exact order:**

**1. IAM Role (must be first — required before VPC can be assigned)**
- Configuration → Permissions → click the role name → **Add permissions → Attach policies**
- Attach: `AWSLambdaVPCAccessExecutionRole`
- Attach: `AmazonElasticFileSystemClientReadWriteAccess`
- Also add this inline policy for ECR image pull (Actions → Create inline policy):
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage", "ecr:BatchCheckLayerAvailability"],
    "Resource": "arn:aws:ecr:REGION:ACCOUNT_ID:repository/finance-tracker-backend"
  }, {
    "Effect": "Allow",
    "Action": "ecr:GetAuthorizationToken",
    "Resource": "*"
  }]
}
```

**2. General configuration**
- Configuration → General configuration: Memory `512 MB`, Timeout `30 sec`

**3. Environment variables**
- Configuration → Environment variables → Add:
  - `DATABASE_URL` = `sqlite:////mnt/efs/portfolio.db`
  - `CORS_ORIGINS` = `["https://YOUR_CLOUDFRONT_DOMAIN"]` (replace with actual domain)
  - `LOG_LEVEL` = `INFO`
  - `LOG_FORMAT` = `json`

**4. VPC (requires IAM role from step 1)**
- Configuration → VPC → Edit → select default VPC, select all subnets, security group: `finance-tracker-lambda-sg`

**5. File systems (requires VPC from step 4)**
- Configuration → File systems → Add → select your EFS, access point from Step E, local mount path: `/mnt/efs`

### Step F.5: Smoke Test Lambda via Console

> Do this after completing all Step F configuration (VPC, EFS, env vars). Verifies the container, Mangum, FastAPI, and EFS mount all work before exposing a public URL.

1. Lambda → `finance-tracker-backend` → **Test** tab
2. Click **Create new event**, name it `health-check`, paste this payload:
```json
{
  "version": "2.0",
  "routeKey": "GET /api/v1/health",
  "rawPath": "/api/v1/health",
  "rawQueryString": "",
  "headers": {"content-type": "application/json"},
  "requestContext": {"http": {"method": "GET", "path": "/api/v1/health", "sourceIp": "127.0.0.1"}},
  "isBase64Encoded": false
}
```
3. Click **Test**

Expected result:
```json
{
  "statusCode": 200,
  "body": "{\"status\":\"healthy\"}"
}
```

Check the **Log output** below the response for Alembic migration lines — confirms EFS is mounted and writable:
```
INFO  [alembic.runtime.migration] Running upgrade ...
```

**If it times out:** EFS or VPC is misconfigured — check Configuration → VPC and Configuration → File systems.

**If it returns 500:** check the log output for the Python traceback.

**Only proceed to Step G once this returns 200.**

### Step G: Enable Lambda Function URL
1. Lambda → your function → **Configuration → Function URL** → **Create function URL**
2. Auth type: **NONE**
3. **Note the Function URL** (e.g., `https://abcdef.lambda-url.eu-west-1.on.aws/`)

### Step H: Update Lambda IAM Role
1. Lambda → your function → **Configuration → Permissions** → click the role name
2. **Attach policies**:
   - `AWSLambdaVPCAccessExecutionRole`
   - `AmazonElasticFileSystemClientReadWriteAccess`
3. For ECR image pull, add inline policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage", "ecr:BatchCheckLayerAvailability"],
    "Resource": "arn:aws:ecr:REGION:ACCOUNT_ID:repository/finance-tracker-backend"
  }, {
    "Effect": "Allow",
    "Action": "ecr:GetAuthorizationToken",
    "Resource": "*"
  }]
}
```

### Step I: Update GitHub Actions IAM User
The existing GitHub Actions IAM user needs additional permissions. In AWS Console → IAM → Users → find the CI/CD user → Add inline policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunctionConfiguration",
        "lambda:WaitForFunctionActive"
      ],
      "Resource": "arn:aws:lambda:REGION:ACCOUNT_ID:function:finance-tracker-backend"
    }
  ]
}
```

### Step J: Add GitHub Secrets
In your GitHub repository → Settings → Secrets and variables → Actions → **New repository secret**:

| Secret Name | Value |
|---|---|
| `ECR_REGISTRY` | `123456789012.dkr.ecr.eu-west-1.amazonaws.com` |
| `ECR_REPOSITORY` | `finance-tracker-backend` |
| `LAMBDA_FUNCTION_NAME` | `finance-tracker-backend` |

---

## Code Implementation Tasks

> **Status as of 2026-03-15:** Tasks 1-4 are **COMPLETE** (code changes already applied on branch `migration_to_lambda`). Tasks 5-7 are manual AWS operations still pending.

### Known issues fixed during implementation

| Issue | Root cause | Fix applied |
|---|---|---|
| `pip install` fails with hash error | `uv export` includes local package as `file:///var/task` | Added `--no-emit-project` to `uv export` |
| Mangum raises `KeyError: 'sourceIp'` | Mangum requires `requestContext.http.sourceIp` in every event | Always include `"sourceIp": "127.0.0.1"` in test payloads |
| All routes return 404 via Mangum | `root_path="/api"` causes Starlette to strip `/api` from paths; routes were registered with prefix `/api/v1` so after stripping became `/v1/...` with no match | Changed `api_v1_prefix` from `/api/v1` to `/v1` in `config.py` |
| Health route 404 | Same root_path stripping issue | Registered health at `/v1/health` — matches after Starlette strips `/api` from incoming `/api/v1/health` |

---

### Task 1: Add Mangum Dependency ✅ DONE

**Files:**
- Modify: `backend/pyproject.toml`

**Step 1: Add mangum dependency**
```bash
cd backend
uv add mangum
```

**Step 2: Verify it was added**
```bash
grep mangum pyproject.toml
```
Expected: `mangum>=0.19.0` (or similar) in dependencies

---

### Task 2: Create Lambda Handler ✅ DONE

**Files:**
- Create: `backend/lambda_handler.py`

`backend/lambda_handler.py`:
```python
"""AWS Lambda entry point for the FastAPI application.

Mangum adapts the ASGI FastAPI app to the Lambda event/context interface.
Alembic migrations are run on every cold start (idempotent — safe to re-run).
"""

import logging
import os

from alembic import command
from alembic.config import Config
from mangum import Mangum

from app.main import app

logger = logging.getLogger(__name__)

_BASE_DIR = os.path.dirname(__file__)


def _run_migrations() -> None:
    """Apply any pending Alembic migrations."""
    alembic_cfg = Config(os.path.join(_BASE_DIR, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(_BASE_DIR, "alembic"))
    command.upgrade(alembic_cfg, "head")
    logger.info("Alembic migrations applied")


# Run migrations on cold start (module-level, runs once per container)
_run_migrations()

# Mangum wraps the FastAPI ASGI app for Lambda
handler = Mangum(app, lifespan="off")
```

---

### Checkpoint 0: Confirm Existing Tests Still Pass

> **Do this after Tasks 1-2, before building Docker.**
> Adding Mangum and the handler file should not break anything, but importing `app.main` at module level inside `lambda_handler.py` can surface hidden import errors or circular dependencies that the test suite would catch.

```bash
cd backend
uv run pytest -q
```
Expected: all tests pass (same count as before). If anything fails, fix it before proceeding — the Docker build will have the same problem.

---

### Task 3: Create Lambda Dockerfile ✅ DONE

**Files:**
- Create: `backend/Dockerfile.lambda`

`backend/Dockerfile.lambda`:
```dockerfile
FROM public.ecr.aws/lambda/python:3.12

# Copy UV binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR ${LAMBDA_TASK_ROOT}

# Install dependencies via uv export → pip install
# This installs packages into the Lambda task root (Lambda's expected location)
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --no-editable --no-emit-project -o requirements.txt && \
    pip install -r requirements.txt --no-cache-dir
# NOTE: --no-emit-project is required. Without it, uv includes the local package
# as file:///var/task in requirements.txt and pip fails with a hash verification error.

# Copy application code
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY app/ ./app/
COPY lambda_handler.py ./

CMD ["lambda_handler.handler"]
```

---

### Checkpoint A: Test Docker Container Locally

> **Do this before pushing to ECR or touching any AWS infrastructure.**
> The Lambda base image includes a local emulator that mimics the Lambda runtime — you can send real HTTP-style events and verify responses without any AWS account.

**Step 1: Build the image**
```bash
cd backend
docker build --platform linux/amd64 --provenance=false -f Dockerfile.lambda -t finance-tracker-lambda-test .
```
Expected: build completes with no errors.

> `--platform linux/amd64` is required on Apple Silicon — Lambda only supports x86_64 images.
> `--provenance=false` is required — Docker BuildKit adds OCI attestation manifests by default that Lambda rejects.
> Cross-platform builds on Apple Silicon can also produce files without world-read permissions, causing `PermissionError` at Lambda startup. The `RUN chmod -R 755 ${LAMBDA_TASK_ROOT}` in the Dockerfile fixes this.

**Step 2: Run the container with a local SQLite database**
```bash
docker run --rm -p 9000:8080 \
  -e DATABASE_URL="sqlite:////tmp/test.db" \
  -e CORS_ORIGINS='["http://localhost:3000"]' \
  -e LOG_LEVEL=INFO \
  -e LOG_FORMAT=json \
  finance-tracker-lambda-test
```

The container starts the Lambda emulator on port 9000. Leave it running and open a second terminal for the checks below.

**Step 3: Health check**

Use Postman (recommended — avoids zsh multiline quoting issues):
- Method: `POST`
- URL: `http://localhost:9000/2015-03-31/functions/function/invocations`
- Header: `Content-Type: application/json`
- Body:
```json
{
  "version": "2.0",
  "routeKey": "GET /api/v1/health",
  "rawPath": "/api/v1/health",
  "rawQueryString": "",
  "headers": {"content-type": "application/json"},
  "requestContext": {"http": {"method": "GET", "path": "/api/v1/health", "sourceIp": "127.0.0.1"}},
  "isBase64Encoded": false
}
```
Expected: `statusCode: 200`, body `{"status":"healthy"}`.

> **Routing note:** the app has `root_path="/api"` and `api_v1_prefix="/v1"`. Starlette's `get_route_path()` strips `scope["root_path"]` ("/api") from the incoming path before matching. So all routes must be registered WITHOUT the `/api` prefix — e.g. `/v1/health`, `/v1/transactions`. The health endpoint is registered as `@app.get("/v1/health")` (accessible externally as `/api/v1/health`). All external URLs remain `/api/v1/...` — the frontend is unaffected.

> **`sourceIp` is required** in every Postman/curl event payload. Mangum reads it from `requestContext.http.sourceIp` and raises a `KeyError` if it's missing.

**Step 4: Create a test transaction (verifies DB write)**

```json
{
  "version": "2.0",
  "routeKey": "POST /api/v1/transactions",
  "rawPath": "/api/v1/transactions",
  "rawQueryString": "",
  "headers": {"content-type": "application/json"},
  "requestContext": {"http": {"method": "POST", "path": "/api/v1/transactions", "sourceIp": "127.0.0.1"}},
  "body": "{\"isin\": \"IE00B4L5Y983\", \"date\": \"2024-01-15\", \"transaction_type\": \"BUY\", \"units\": \"10\", \"price_per_unit\": \"85.50\", \"fee\": \"1.00\", \"broker\": \"Test\"}",
  "isBase64Encoded": false
}
```
Expected: `statusCode: 201`, body contains the created transaction with an `id`.

**Step 5: Read back transactions (verifies DB read)**

```json
{
  "version": "2.0",
  "routeKey": "GET /api/v1/transactions",
  "rawPath": "/api/v1/transactions",
  "rawQueryString": "",
  "headers": {"content-type": "application/json"},
  "requestContext": {"http": {"method": "GET", "path": "/api/v1/transactions", "sourceIp": "127.0.0.1"}},
  "isBase64Encoded": false
}
```
Expected: `statusCode: 200`, array contains the transaction created in Step 4.

> **Testing the frontend against Docker:** the Lambda emulator only accepts Lambda-formatted events, not plain HTTP. To test the frontend against the Docker image, override the CMD: `docker run ... finance-tracker-lambda-test uvicorn app.main:app --host 0.0.0.0 --port 8000`. However, testing the frontend against `uv run uvicorn` directly is equivalent since the application code is identical.

**Step 6: Stop the container**
```bash
# Ctrl+C in the first terminal, or:
docker stop $(docker ps -q --filter ancestor=finance-tracker-lambda-test)
```

> **If any step fails**, do not proceed to ECR/Lambda. Check the container logs in the first terminal for the full error traceback.

---

### Task 4: Update GitHub Actions CI/CD Workflow ✅ DONE

**Files:**
- Modify: `.github/workflows/deploy.yml`

The new `deploy` job replaces the EC2 SSH deployment. The `test` job and frontend deploy remain unchanged. Key changes:
- Log in to ECR
- Build and push Docker image tagged with `github.sha` and `latest`
- Update Lambda function code with new image URI
- Wait for Lambda update to complete
- Health check via CloudFront domain

---

### Checkpoint B: Verify First CI/CD Run Succeeded

> **Do this after merging `migration_to_lambda` to `main` and before touching any data.**
> The pipeline builds the image, pushes to ECR, and updates Lambda. If any of these silently failed, the Lambda is running stale or broken code and the data migration would be pointless.

**Step 1: Check the GitHub Actions run**
- GitHub → repository → **Actions** tab → find the latest "Deploy to AWS" run
- All jobs (test, deploy) must show a green checkmark
- If any job failed, read the logs and fix before continuing

**Step 2: Confirm the image is in ECR**
```bash
aws-vault exec YOUR_PROFILE -- aws ecr describe-images \
  --repository-name finance-tracker-backend \
  --query 'sort_by(imageDetails, &imagePushedAt)[-1].{digest:imageDigest,pushed:imagePushedAt,tags:imageTags}' \
  --output table
```
Expected: a row with the latest push timestamp and tag matching the most recent git SHA.

**Step 3: Confirm Lambda is using the new image**
```bash
aws-vault exec YOUR_PROFILE -- aws lambda get-function-configuration \
  --function-name finance-tracker-backend \
  --query '{ImageUri:Code.ImageUri,LastModified:LastModified,State:State}' \
  --output table
```
Expected: `State` is `Active` and `ImageUri` contains the git SHA from Step 2.

> **Do not proceed to data migration if Lambda state is not `Active` or the SHA doesn't match.**

---

### Task 5: Migrate Existing Data to EFS

> One-time manual operation to move the SQLite database from EC2 to EFS.

**Step 1: Update EC2 security group to allow NFS outbound**
- AWS Console → EC2 security group → Outbound → Add NFS (port 2049) to `finance-tracker-efs-sg`

**Step 2: Mount EFS on EC2**
```bash
ssh -i your-key.pem ec2-user@YOUR_EC2_IP

sudo mkdir -p /mnt/efs
sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2,noresvport \
  fs-YOURFSID.efs.REGION.amazonaws.com:/ /mnt/efs
sudo mkdir -p /mnt/efs/portfolio
sudo chmod 755 /mnt/efs/portfolio
```

**Step 3: Copy the SQLite database**
```bash
sudo cp /opt/etf-portfolio/backend/portfolio.db /mnt/efs/portfolio/portfolio.db
sudo chown 1000:1000 /mnt/efs/portfolio/portfolio.db
ls -la /mnt/efs/portfolio/
```

**Step 4: Verify database integrity**
```bash
sqlite3 /mnt/efs/portfolio/portfolio.db "SELECT COUNT(*) FROM transactions;"
```
Expected: your transaction count (not an error)

**Step 5: Unmount EFS from EC2**
```bash
sudo umount /mnt/efs
```

---

### Checkpoint B: Test Lambda Function Directly (Before CloudFront Cutover)

> **Do this after Task 5 (data migrated to EFS) and before Task 6 (CloudFront cutover).**
> At this point the Lambda is live on AWS with EFS mounted and your real data. EC2 is still serving the frontend — this checkpoint lets you verify the Lambda end-to-end without any user-visible impact.
>
> These are plain HTTP requests to the Lambda Function URL — no Lambda event wrapping needed. Use Postman with method + URL only (no special body format).

**Step 1: Health check**

- Method: `GET`
- URL: `https://YOUR_LAMBDA_FUNCTION_URL/api/v1/health`
- No body, no extra headers

Expected: `{"status": "healthy"}`

If you get a timeout, check:
- Lambda → Configuration → VPC is configured
- Lambda → Configuration → File systems shows the EFS mount
- CloudWatch → Log groups → `/aws/lambda/finance-tracker-backend` for error details

**Step 2: Verify real data is accessible (reads from EFS)**

Request 1 — list transactions:
- Method: `GET`
- URL: `https://YOUR_LAMBDA_FUNCTION_URL/api/v1/transactions`

Request 2 — portfolio summary:
- Method: `GET`
- URL: `https://YOUR_LAMBDA_FUNCTION_URL/api/v1/portfolio-summary`

Expected: your actual transactions and holdings, not an empty array or error.

**Step 3: Test a write operation (verify EFS is writable)**

Create a dummy transaction:
- Method: `POST`
- URL: `https://YOUR_LAMBDA_FUNCTION_URL/api/v1/transactions`
- Header: `Content-Type: application/json`
- Body:
```json
{
  "isin": "IE00B4L5Y983",
  "date": "2024-01-15",
  "transaction_type": "BUY",
  "units": "1",
  "price_per_unit": "1.00",
  "fee": "0.00",
  "broker": "Test"
}
```
Note the `id` in the response.

Delete it immediately:
- Method: `DELETE`
- URL: `https://YOUR_LAMBDA_FUNCTION_URL/api/v1/transactions/YOUR_ID`

Expected: `204 No Content`. This confirms Lambda can write to and delete from EFS.

**Step 4: Check cold start time**

Send the health check request twice back-to-back in Postman and observe the response time shown at the bottom of the response panel:
- First request: cold start, expect ~3-8s
- Second request: warm container, expect ~100-500ms

If cold start exceeds 30s, increase Lambda timeout: Configuration → General configuration → Timeout.

**Step 5: Check CloudWatch logs for errors**
- AWS Console → CloudWatch → Log groups → `/aws/lambda/finance-tracker-backend`
- Look for any ERROR or CRITICAL log lines from the migration run or the requests above
- Migration log line to confirm: `"Alembic migrations applied"`

> **Only proceed to Task 6 if all checks above pass.**

---

### Task 6: Update CloudFront to Point to Lambda

> Cutover step. Do this after Checkpoint B passes — EC2 is still live until Step 2 below.

**Step 1: Verify Lambda works via Function URL**

In Postman:
- Method: `GET`
- URL: `https://YOUR_LAMBDA_FUNCTION_URL/api/v1/health`

Expected: `{"status": "healthy"}`

**Step 2: Update CloudFront origin**
- CloudFront → your distribution → **Origins** tab
- Edit the EC2 origin (used by `/api/*` behavior)
- Change Origin domain to your Lambda Function URL (remove `https://` prefix)
- Protocol: HTTPS only

**Step 3: Update CloudFront behavior**
- CloudFront → **Behaviors** tab → edit the `/api/*` behavior
- Allowed HTTP methods: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
- Cache policy: **CachingDisabled**
- Origin request policy: **AllViewerExceptHostHeader**

**Step 4: Invalidate CloudFront cache**
```bash
aws-vault exec YOUR_PROFILE -- aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/api/*"
```

**Step 5: End-to-end verification**

In Postman:
- `GET https://YOUR_CLOUDFRONT_DOMAIN/api/v1/health` → `{"status": "healthy"}`
- `GET https://YOUR_CLOUDFRONT_DOMAIN/api/v1/transactions` → JSON array

---

### Checkpoint C: Full Frontend Smoke Test (Before Stopping EC2)

> **Do this after the CloudFront cutover and before stopping EC2.**
> curl tests pass at the HTTP level but don't catch frontend routing issues, CORS mismatches, or broken API paths in the React app. EC2 is still running here — if anything is wrong you can revert the CloudFront origin in ~2 minutes.

**Step 1: Open the app in a browser**
- Go to `https://YOUR_CLOUDFRONT_DOMAIN`
- The Investment Dashboard should load with your portfolio data visible (not a loading spinner or blank page)

**Step 2: Check the browser console for errors**
- Open DevTools → Console tab
- There should be no red errors. In particular, watch for:
  - `CORS` errors (means CloudFront origin request policy is misconfigured)
  - `Failed to fetch` (means the `/api/*` routing is broken)
  - `404` on API calls (means the path prefix is wrong)

**Step 3: Navigate through all pages**
- Transactions page — list loads
- ISIN Metadata page — list loads
- Other Assets page — list loads
- Snapshots page — list loads

**Step 4: Test one write from the UI**
- Add a test transaction via the form and save it
- Confirm it appears in the list
- Delete it immediately

**Step 5: Rollback procedure (if anything is wrong)**
- CloudFront → Origins → edit the Lambda origin → change domain back to EC2's IP/DNS
- Invalidate: `aws-vault exec YOUR_PROFILE -- aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/api/*"`
- EC2 is still running so traffic flips back instantly

> **Only stop EC2 (Task 7) after the app works end-to-end in the browser with no console errors.**

---

### Task 7: Decommission EC2

> Only after 24-48 hours of stable Lambda operation.

1. **Stop EC2** (reversible): AWS Console → EC2 → Instance State → **Stop**
2. Monitor Lambda for 1-2 days
3. **Terminate EC2** (permanent): AWS Console → EC2 → Instance State → **Terminate**

---

## Verification

Full end-to-end test after deployment:

In Postman:

| Method | URL | Expected |
|---|---|---|
| GET | `https://YOUR_CLOUDFRONT_DOMAIN/api/v1/health` | `{"status":"healthy"}` |
| GET | `https://YOUR_CLOUDFRONT_DOMAIN/api/v1/transactions` | JSON array of your transactions |
| GET | `https://YOUR_CLOUDFRONT_DOMAIN/api/v1/portfolio-summary` | JSON with holdings data |

Check Lambda logs: AWS Console → CloudWatch → Log groups → `/aws/lambda/finance-tracker-backend`

---

## Expected Cost After Migration

| Service | Monthly Cost |
|---|---|
| Lambda (few hundred requests) | $0.00 (free tier) |
| EFS (< 100MB SQLite) | ~$0.01 |
| S3 + CloudFront | ~$0.01 |
| ECR (1 image) | $0.00 (free tier: 500MB/month) |
| **Total** | **~$0.02/month** |
