# Architecture

This document describes the production architecture of the ETF Portfolio Tracker and provides step-by-step instructions to recreate the infrastructure from scratch on a new AWS account and/or Neon account.

---

## System Overview

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────────┐
│   Browser    │────▶│   CloudFront     │────▶│   S3 Bucket       │
│              │     │   (CDN + HTTPS)  │     │   (React build)   │
└──────────────┘     └──────┬───────────┘     └───────────────────┘
                            │
                            │ /api/* requests
                            ▼
                     ┌──────────────────┐     ┌───────────────────┐
                     │   API Gateway    │────▶│   AWS Lambda      │
                     │   (HTTP API)     │     │   (FastAPI +      │
                     └──────────────────┘     │    Mangum)        │
                                              └──────┬────────────┘
                                                     │
                                                     │ DATABASE_URL
                                                     ▼
                                              ┌───────────────────┐
                                              │   Neon PostgreSQL │
                                              │   (free tier,     │
                                              │    serverless)    │
                                              └───────────────────┘
```

### Components

| Component | Service | Purpose |
|-----------|---------|---------|
| **Frontend** | S3 + CloudFront | Static React app served via CDN with HTTPS |
| **Backend** | AWS Lambda + API Gateway | FastAPI app packaged as Docker image, invoked per-request |
| **Database** | Neon PostgreSQL (free tier) | Persistent serverless PostgreSQL, scales to zero |
| **Container Registry** | Amazon ECR | Stores Docker images for the Lambda function |
| **CI/CD** | GitHub Actions | Automated testing, migrations, and deployment |

### Key Design Decisions

- **Lambda over EC2**: No idle costs, automatic scaling, no server maintenance
- **Neon over S3/SQLite**: Reliable persistent storage, no cold-start download/upload sync, real PostgreSQL features
- **NullPool in SQLAlchemy**: Lambda invocations are short-lived; connection pooling would leak connections and exhaust Neon's free-tier limit
- **Alembic at deploy time**: Migrations run in CI/CD (not Lambda cold start) for reliability and speed
- **SQLite for local dev**: Simple, no external dependencies needed for development

### Request Flow

1. Browser loads React app from CloudFront (S3 origin)
2. Frontend makes API calls to `/api/v1/*` (relative paths)
3. CloudFront routes `/api/*` to API Gateway
4. API Gateway invokes Lambda function
5. Lambda runs FastAPI via Mangum (ASGI adapter)
6. FastAPI connects to Neon PostgreSQL via `DATABASE_URL`
7. Response flows back through the same path

---

## Production Environment Variables

### Lambda Environment Variables

Set these on the Lambda function (AWS Console → Lambda → Configuration → Environment variables):

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | `postgresql://user:pass@host/neondb?sslmode=require` | Neon connection string |
| `CORS_ORIGINS` | `["https://YOUR_CLOUDFRONT_DOMAIN"]` | CloudFront domain |
| `API_V1_PREFIX` | `/v1` | API route prefix |
| `DEBUG` | `False` | Disable SQL logging in production |
| `LOG_LEVEL` | `INFO` | Structured JSON logging level |
| `LOG_FORMAT` | `json` | Log format (json for CloudWatch) |

### GitHub Secrets

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `AWS_REGION` | e.g. `us-east-1` |
| `S3_BUCKET_NAME` | Frontend S3 bucket name |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront distribution ID |
| `CLOUDFRONT_DOMAIN` | e.g. `d1234abcd.cloudfront.net` (bare domain, no `https://`) |
| `ECR_REGISTRY` | e.g. `123456789012.dkr.ecr.us-east-1.amazonaws.com` |
| `ECR_REPOSITORY` | e.g. `finance-tracker-backend` |
| `LAMBDA_FUNCTION_NAME` | e.g. `finance-tracker-backend` |
| `NEON_DATABASE_URL` | Neon PostgreSQL connection string |

---

## Recreating from Scratch

### Step 1: Neon PostgreSQL

1. Go to [neon.tech](https://neon.tech) and create an account
2. Create a new project (free tier: 1 project, 0.5 GiB storage)
3. Choose a region close to your AWS region (e.g. `us-east-1`)
4. Copy the **connection string** from the dashboard — it looks like:
   ```
   postgresql://neondb_owner:password@ep-xxx-yyy.us-east-1.aws.neon.tech/neondb?sslmode=require
   ```
5. Run Alembic to create the schema:
   ```bash
   cd backend
   DATABASE_URL="postgresql://..." uv run alembic upgrade head
   ```
6. Verify tables exist in Neon SQL Editor:
   ```sql
   SELECT tablename FROM pg_tables WHERE schemaname = 'public';
   ```

### Step 2: AWS Account Setup

**All AWS CLI commands below MUST include `--profile YOUR_PROFILE`.** Set up a profile first:

```bash
aws configure --profile etf-portfolio
# Enter: Access Key ID, Secret Access Key, Region (e.g. us-east-1), Output (json)
```

#### 2a. Create ECR Repository

```bash
aws ecr create-repository \
  --repository-name finance-tracker-backend \
  --image-scanning-configuration scanOnPush=true \
  --profile etf-portfolio
```

Note the `repositoryUri` from the output (e.g. `123456789012.dkr.ecr.us-east-1.amazonaws.com/finance-tracker-backend`).

#### 2b. Build and Push Initial Docker Image

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --profile etf-portfolio | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build the image
cd backend
docker build -f Dockerfile.lambda -t finance-tracker-backend:latest .

# Tag and push
docker tag finance-tracker-backend:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/finance-tracker-backend:latest
docker push \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/finance-tracker-backend:latest
```

#### 2c. Create Lambda Function

```bash
# Create execution role
aws iam create-role \
  --role-name finance-tracker-lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' \
  --profile etf-portfolio

# Attach basic execution policy (CloudWatch logs)
aws iam attach-role-policy \
  --role-name finance-tracker-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  --profile etf-portfolio

# Wait a few seconds for IAM propagation, then create the function
aws lambda create-function \
  --function-name finance-tracker-backend \
  --package-type Image \
  --code ImageUri=123456789012.dkr.ecr.us-east-1.amazonaws.com/finance-tracker-backend:latest \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/finance-tracker-lambda-role \
  --timeout 30 \
  --memory-size 256 \
  --environment "Variables={
    DATABASE_URL=postgresql://...,
    CORS_ORIGINS=[\"https://YOUR_CLOUDFRONT_DOMAIN\"],
    API_V1_PREFIX=/v1,
    DEBUG=False,
    LOG_LEVEL=INFO,
    LOG_FORMAT=json
  }" \
  --profile etf-portfolio
```

Note: For the `--environment` flag, it's easier to set env vars via the AWS Console (Lambda → Configuration → Environment variables) to avoid shell quoting issues.

#### 2d. Create API Gateway (HTTP API)

```bash
# Create HTTP API
aws apigatewayv2 create-api \
  --name finance-tracker-api \
  --protocol-type HTTP \
  --profile etf-portfolio

# Note the ApiId from output, then create Lambda integration
aws apigatewayv2 create-integration \
  --api-id YOUR_API_ID \
  --integration-type AWS_PROXY \
  --integration-uri arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:finance-tracker-backend \
  --payload-format-version 2.0 \
  --profile etf-portfolio

# Create catch-all route
aws apigatewayv2 create-route \
  --api-id YOUR_API_ID \
  --route-key '$default' \
  --target integrations/YOUR_INTEGRATION_ID \
  --profile etf-portfolio

# Create default stage with auto-deploy
aws apigatewayv2 create-stage \
  --api-id YOUR_API_ID \
  --stage-name '$default' \
  --auto-deploy \
  --profile etf-portfolio

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name finance-tracker-backend \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:YOUR_ACCOUNT_ID:YOUR_API_ID/*" \
  --profile etf-portfolio
```

Note the API endpoint URL from `create-api` output (e.g. `https://abc123.execute-api.us-east-1.amazonaws.com`).

#### 2e. Create S3 Bucket for Frontend

```bash
aws s3 mb s3://etf-portfolio-frontend-YOUR_UNIQUE_SUFFIX \
  --profile etf-portfolio

# Block public access (CloudFront will serve, not S3 directly)
aws s3api put-public-access-block \
  --bucket etf-portfolio-frontend-YOUR_UNIQUE_SUFFIX \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true \
  --profile etf-portfolio
```

#### 2f. Create CloudFront Distribution

This is easiest via the AWS Console:

1. Go to **CloudFront** → **Create distribution**
2. **Origin 1 (S3)**:
   - Origin domain: select your S3 bucket
   - Origin access: **Origin Access Control (OAC)** → create new
3. **Origin 2 (API Gateway)**:
   - Origin domain: `abc123.execute-api.us-east-1.amazonaws.com` (your API Gateway URL, no `https://`)
   - Protocol: HTTPS only
4. **Default behavior** (S3):
   - Viewer protocol: Redirect HTTP to HTTPS
   - Cache policy: CachingOptimized
5. **Additional behavior** for `/api/*`:
   - Origin: select API Gateway origin
   - Cache policy: CachingDisabled
   - Origin request policy: AllViewerExceptHostHeader
6. **Default root object**: `index.html`
7. **Error pages**: Create custom error response for 403 → `/index.html` with 200 (for React Router)

After creation:
- Note the **Distribution ID** (e.g. `E1A2B3C4D5E6F7`)
- Note the **Domain name** (e.g. `d1234abcd.cloudfront.net`)
- Update the S3 bucket policy to allow CloudFront OAC access (CloudFront will prompt you)

#### 2g. Create IAM User for CI/CD

```bash
aws iam create-user \
  --user-name github-actions-etf-portfolio \
  --profile etf-portfolio

aws iam create-access-key \
  --user-name github-actions-etf-portfolio \
  --profile etf-portfolio
# SAVE the AccessKeyId and SecretAccessKey — shown only once
```

Attach this inline policy (replace placeholders):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3Deploy",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::YOUR_BUCKET_NAME",
        "arn:aws:s3:::YOUR_BUCKET_NAME/*"
      ]
    },
    {
      "Sid": "CloudFront",
      "Effect": "Allow",
      "Action": ["cloudfront:CreateInvalidation", "cloudfront:GetInvalidation"],
      "Resource": "arn:aws:cloudfront::YOUR_ACCOUNT_ID:distribution/*"
    },
    {
      "Sid": "ECR",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Lambda",
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration"
      ],
      "Resource": "arn:aws:lambda:*:YOUR_ACCOUNT_ID:function:finance-tracker-backend"
    }
  ]
}
```

```bash
aws iam put-user-policy \
  --user-name github-actions-etf-portfolio \
  --policy-name GitHubActionsDeployPolicy \
  --policy-document file://policy.json \
  --profile etf-portfolio
```

### Step 3: Configure GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** and add all secrets listed in the [GitHub Secrets](#github-secrets) table above.

### Step 4: Deploy

```bash
# Build frontend and push everything
git push origin main
```

The CI/CD pipeline will:
1. Run tests
2. Run Alembic migrations against Neon (already done, but idempotent)
3. Build frontend → deploy to S3 → invalidate CloudFront
4. Build Docker image → push to ECR → update Lambda
5. Health check

### Step 5: Verify

```bash
# Health check
curl https://YOUR_CLOUDFRONT_DOMAIN/api/v1/health
# Expected: {"status":"healthy"}

# Frontend
open https://YOUR_CLOUDFRONT_DOMAIN
```

---

## Cost Breakdown (Free / Minimal Tier)

| Service | Cost | Notes |
|---------|------|-------|
| **Neon PostgreSQL** | Free | 0.5 GiB storage, 1 project, scales to zero |
| **AWS Lambda** | ~Free | 1M free requests/month, 400K GB-seconds/month |
| **API Gateway** | ~Free | 1M free HTTP API calls/month |
| **ECR** | ~$0.10/month | 500MB free storage, pay for excess |
| **S3** | ~$0.03/month | Static files, minimal storage |
| **CloudFront** | ~$0-1/month | 1TB free transfer, 10M free requests |
| **Total** | ~$0-2/month | Single-user app with minimal traffic |

---

## Local Development

Local development uses SQLite and does not require AWS or Neon:

```bash
# Backend
cd backend
# .env already has DATABASE_URL=sqlite:///./portfolio.db
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm run dev
```

To test against Neon locally:
```bash
DATABASE_URL="postgresql://..." uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
