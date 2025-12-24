# CI/CD Pipeline Documentation

This document explains the automated deployment pipeline for the ETF Portfolio Tracker application using GitHub Actions.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
- [GitHub Secrets Configuration](#github-secrets-configuration)
- [IAM User Setup](#iam-user-setup)
- [Workflow Triggers](#workflow-triggers)
- [Manual Deployment](#manual-deployment)
- [Monitoring Deployments](#monitoring-deployments)
- [Troubleshooting](#troubleshooting)
- [Rollback Procedure](#rollback-procedure)
- [Security Best Practices](#security-best-practices)

---

## Overview

The CI/CD pipeline automatically deploys the application to AWS when code is merged to the main branch. It includes:

- **Automated Testing**: Runs 254 backend tests (95% coverage) before deployment
- **Frontend Deployment**: Builds React app and uploads to S3 with CloudFront invalidation
- **Backend Deployment**: SSH to EC2, pull latest code, run migrations, restart service
- **Health Verification**: Confirms backend is healthy after deployment

**Pipeline Flow:**
```
PR Merged to main
    ↓
Run Backend Tests (pytest)
    ↓ (if tests pass)
Build Frontend (npm run build)
    ↓
Deploy Frontend to S3
    ↓
Invalidate CloudFront Cache
    ↓
Deploy Backend to EC2 (SSH)
    ↓
Verify Health Check
    ↓
Deployment Complete ✓
```

**Deployment Time:** ~5-7 minutes
- Tests: ~2 minutes
- Frontend build/deploy: ~1-2 minutes
- Backend deploy: ~1 minute
- CloudFront invalidation: ~1-2 minutes

---

## Architecture

**GitHub Actions Workflow** (`.github/workflows/deploy.yml`):
- **Job 1: test** - Runs pytest suite on Ubuntu runner
- **Job 2: deploy** - Deploys both frontend and backend (depends on test success)

**AWS Resources:**
- **S3 Bucket**: Hosts React build files (frontend)
- **CloudFront**: CDN for global distribution with HTTPS
- **EC2 Instance**: Runs FastAPI backend on Ubuntu 24.04
- **IAM User**: Dedicated CI/CD user with minimal permissions

---

## Setup Instructions

### Prerequisites

1. **AWS Infrastructure Deployed**: Follow `DEPLOYMENT.md` to set up:
   - S3 bucket for frontend
   - EC2 instance for backend (with application running)
   - CloudFront distribution
   - Elastic IP for EC2 (recommended)

2. **Application in GitHub**: Code repository hosted on GitHub

3. **Local Testing**: Ensure tests pass locally:
   ```bash
   cd backend
   uv run pytest
   ```

### Step-by-Step Setup

#### 1. Create IAM User for CI/CD

See [IAM User Setup](#iam-user-setup) section below for detailed instructions.

#### 2. Create SSH Key for EC2 (CI/CD Dedicated)

**On your local machine:**

```bash
# Generate new SSH key for CI/CD (don't reuse personal key)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/ci_cd_deploy_key -N ""

# This creates two files:
# - ci_cd_deploy_key (private key - will be GitHub secret)
# - ci_cd_deploy_key.pub (public key - add to EC2)
```

**Add public key to EC2:**

```bash
# SSH to your EC2 instance
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@YOUR_EC2_IP

# Add CI/CD public key to authorized_keys
nano ~/.ssh/authorized_keys

# Paste the contents of ci_cd_deploy_key.pub on a new line
# Save and exit (Ctrl+X, Y, Enter)

# Verify permissions
chmod 600 ~/.ssh/authorized_keys
```

**Test CI/CD key works:**

```bash
# From local machine
ssh -i ~/.ssh/ci_cd_deploy_key ubuntu@YOUR_EC2_IP

# Should connect successfully
```

#### 3. Configure GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add the following 9 secrets (see [GitHub Secrets Configuration](#github-secrets-configuration) for details):

| Secret Name | Value |
|------------|-------|
| `AWS_ACCESS_KEY_ID` | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `AWS_REGION` | AWS region (e.g., `us-east-1`) |
| `S3_BUCKET_NAME` | S3 bucket name |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront distribution ID |
| `CLOUDFRONT_DOMAIN` | CloudFront domain (e.g., `d123abc.cloudfront.net`) |
| `EC2_HOST` | EC2 Elastic IP or public DNS |
| `EC2_USERNAME` | EC2 username (usually `ubuntu`) |
| `EC2_SSH_PRIVATE_KEY` | Contents of `ci_cd_deploy_key` private key file |
| `CODECOV_TOKEN` | (Optional) Codecov token for coverage reports |

#### 4. Enable GitHub Actions

In your repository:
1. Go to **Actions** tab
2. If prompted, click **"I understand my workflows, go ahead and enable them"**
3. You should see the **"Deploy to AWS"** workflow listed

#### 5. Test First Deployment

**Option A: Merge a PR to main**
```bash
# Create a test branch
git checkout -b test-ci-cd

# Make a small change (e.g., update README)
echo "CI/CD enabled" >> README.md

# Commit and push
git add README.md
git commit -m "Test CI/CD pipeline"
git push origin test-ci-cd

# Create PR on GitHub and merge it
# Workflow will trigger automatically
```

**Option B: Manual trigger**
1. Go to **Actions** tab
2. Click **"Deploy to AWS"** workflow
3. Click **"Run workflow"** button
4. Select branch **"main"**
5. Click **"Run workflow"**

#### 6. Verify Deployment

**Check workflow logs:**
1. Go to **Actions** tab → Click on the running workflow
2. Watch logs in real-time
3. Look for green checkmarks on all steps

**Verify application:**
```bash
# Check frontend
curl https://YOUR_CLOUDFRONT_DOMAIN

# Check backend API
curl https://YOUR_CLOUDFRONT_DOMAIN/api/v1/health
# Expected: {"status":"healthy"}
```

---

## GitHub Secrets Configuration

### Required Secrets

#### AWS Credentials

**AWS_ACCESS_KEY_ID**
- IAM user access key ID
- Format: `AKIA...` (20 characters)
- Get from: IAM user creation or AWS CLI (`aws configure list`)

**AWS_SECRET_ACCESS_KEY**
- IAM user secret access key
- Format: Long alphanumeric string (40 characters)
- Get from: IAM user creation (only shown once!)
- **Important**: Keep secure, never commit to code

**AWS_REGION**
- AWS region where resources are deployed
- Examples: `us-east-1`, `eu-west-1`, `ap-southeast-1`
- Must match region of S3 bucket and EC2 instance

#### S3 and CloudFront

**S3_BUCKET_NAME**
- S3 bucket name for frontend
- Example: `etf-portfolio-frontend-1234567890`
- Get from: AWS Console → S3 → Your bucket name

**CLOUDFRONT_DISTRIBUTION_ID**
- CloudFront distribution ID (NOT domain name)
- Format: `E1A2B3C4D5E6F7` (14 characters)
- Get from: AWS Console → CloudFront → Distributions → ID column

**CLOUDFRONT_DOMAIN**
- CloudFront domain name (optional, for verification message)
- Format: `d1a2b3c4d5e6f7.cloudfront.net`
- Get from: AWS Console → CloudFront → Distributions → Domain name column

#### EC2 Access

**EC2_HOST**
- EC2 instance Elastic IP or Public DNS
- **Recommended**: Use Elastic IP (doesn't change)
- Examples:
  - Elastic IP: `54.123.45.67`
  - Public DNS: `ec2-54-123-45-67.compute-1.amazonaws.com`
- Get from: AWS Console → EC2 → Instances → Public IPv4 address

**EC2_USERNAME**
- SSH username for EC2 instance
- For Ubuntu: `ubuntu`
- For Amazon Linux: `ec2-user`

**EC2_SSH_PRIVATE_KEY**
- Contents of private SSH key file (CI/CD dedicated key)
- **Format**: Include full key including headers
  ```
  -----BEGIN RSA PRIVATE KEY-----
  [key contents]
  -----END RSA PRIVATE KEY-----
  ```
- Get from: `cat ~/.ssh/ci_cd_deploy_key` (after generating in Step 2)
- **Important**: Use a dedicated key for CI/CD, not your personal key

#### Optional Secrets

**CODECOV_TOKEN** (optional)
- Token for uploading coverage reports to Codecov.io
- Sign up at https://codecov.io and link your repository
- Get from: Codecov → Repository Settings → Token

### How to Add Secrets

1. Go to GitHub repository
2. Click **Settings** tab
3. In left sidebar: **Secrets and variables** → **Actions**
4. Click **"New repository secret"** button
5. **Name**: Enter secret name exactly (e.g., `AWS_ACCESS_KEY_ID`)
6. **Secret**: Paste the value
7. Click **"Add secret"**
8. Repeat for all secrets

**Verification:**
- After adding all secrets, they should appear in the list
- You cannot view secret values after creation (security feature)
- You can update secrets by clicking on them and choosing "Update"

---

## IAM User Setup

Create a dedicated IAM user with minimal required permissions for CI/CD.

### Step 1: Create IAM User

1. Log in to AWS Console
2. Navigate to **IAM** service
3. Click **Users** → **Create user**
4. **User name**: `github-actions-etf-portfolio`
5. **AWS access type**: Select **"Access key - Programmatic access"**
6. Click **Next**

### Step 2: Attach Permissions

**Option A: Create Custom Policy (Recommended - Least Privilege)**

1. Click **"Attach policies directly"**
2. Click **"Create policy"**
3. Click **JSON** tab
4. Paste this policy (replace `YOUR_BUCKET_NAME` and `YOUR_ACCOUNT_ID`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3FrontendDeploy",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR_BUCKET_NAME",
        "arn:aws:s3:::YOUR_BUCKET_NAME/*"
      ]
    },
    {
      "Sid": "CloudFrontInvalidation",
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation"
      ],
      "Resource": "arn:aws:cloudfront::YOUR_ACCOUNT_ID:distribution/*"
    }
  ]
}
```

5. Click **Next: Tags** (optional)
6. Click **Next: Review**
7. **Name**: `GitHubActionsDeployPolicy`
8. Click **Create policy**
9. Go back to user creation, refresh policies, and select `GitHubActionsDeployPolicy`

**Option B: Use AWS Managed Policies (Simpler, Less Secure)**

Attach these managed policies:
- `AmazonS3FullAccess` (or `AmazonS3ReadOnlyAccess` + custom S3 write policy)
- `CloudFrontFullAccess` (or create custom policy for invalidations only)

### Step 3: Review and Create

1. Click **Next**
2. Review user details and permissions
3. Click **Create user**

### Step 4: Save Credentials

**CRITICAL: Save these immediately - secret key is only shown once!**

1. **Access key ID**: Copy this (e.g., `AKIAIOSFODNN7EXAMPLE`)
2. **Secret access key**: Click **"Show"** and copy (e.g., `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`)
3. **Save both** to GitHub secrets:
   - `AWS_ACCESS_KEY_ID` = Access key ID
   - `AWS_SECRET_ACCESS_KEY` = Secret access key

**Store securely** (password manager or GitHub secrets only)

### Step 5: Enable MFA (Recommended)

1. Go to IAM → Users → `github-actions-etf-portfolio`
2. **Security credentials** tab
3. **Multi-factor authentication (MFA)** → **Assign MFA device**
4. Follow setup wizard

**Note**: MFA is for console access; programmatic access (GitHub Actions) uses access keys.

### IAM Policy Explanation

**S3 Permissions:**
- `s3:PutObject` - Upload files to S3
- `s3:GetObject` - Read files (verification)
- `s3:DeleteObject` - Remove old files during sync
- `s3:ListBucket` - List bucket contents for sync

**CloudFront Permissions:**
- `cloudfront:CreateInvalidation` - Clear CDN cache after deployment
- `cloudfront:GetInvalidation` - Check invalidation status

---

## Workflow Triggers

### Automatic Trigger: PR Merge to Main

**Trigger condition:** Push to `main` branch
- Happens when PR is merged
- Also triggers on direct push to `main` (if allowed)

**Workflow steps:**
1. Detect push to main
2. Run tests (pytest suite)
3. If tests pass → deploy
4. If tests fail → stop (no deployment)

### Manual Trigger: workflow_dispatch

**When to use:**
- Emergency deployment
- Rollback to specific commit
- Test deployment without PR
- Re-deploy after fixing GitHub Actions configuration

**How to manually trigger:**

1. Go to GitHub repository → **Actions** tab
2. Click **"Deploy to AWS"** workflow (left sidebar)
3. Click **"Run workflow"** dropdown button (top right)
4. Select branch (usually **main**)
5. Click **"Run workflow"** button
6. Watch workflow progress in real-time

---

## Manual Deployment

### Triggering Deployment

See [Workflow Triggers](#workflow-triggers) section above.

### Deploying Specific Commit

1. Go to **Actions** → **Deploy to AWS**
2. Click **"Run workflow"**
3. Change branch to commit SHA or branch name
4. Click **"Run workflow"**

**Alternative: Revert and deploy**
```bash
# Revert to specific commit
git revert <bad-commit-sha>
git push origin main

# Or reset to previous state (requires force push)
git reset --hard <good-commit-sha>
git push --force origin main  # Use with caution!
```

### Deploying Only Frontend or Backend

Currently, the workflow deploys both together. To deploy individually:

**Frontend only:**
1. SSH to EC2 and stop backend service temporarily
2. Run workflow (frontend deploys, backend deploy fails but doesn't break frontend)
3. Restart backend service

**Backend only:**
1. Comment out frontend steps in `.github/workflows/deploy.yml`
2. Commit and push to main
3. Deployment runs backend only
4. Restore workflow file after deployment

**Better approach:** Create separate workflows:
- `.github/workflows/deploy-frontend.yml`
- `.github/workflows/deploy-backend.yml`

---

## Monitoring Deployments

### Real-Time Monitoring

**GitHub Actions UI:**
1. Go to **Actions** tab
2. Click on running workflow
3. Watch logs in real-time
4. Green checkmarks ✓ = success
5. Red X = failure

**View specific job:**
- Click on job name (e.g., "Run Tests" or "Deploy Application")
- Expand steps to see detailed logs
- Download logs for offline review

### Notifications

**GitHub default notifications:**
- Email on workflow failure (if enabled in settings)
- GitHub notifications bell icon

**Optional: Slack/Discord notifications**

Add to `.github/workflows/deploy.yml` after deploy job:

```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
    fields: repo,message,commit,author,action,eventName,ref,workflow
```

Add `SLACK_WEBHOOK` secret with webhook URL.

### Deployment History

**View past deployments:**
1. Go to **Actions** tab
2. See list of all workflow runs
3. Filter by:
   - Event (push, workflow_dispatch)
   - Status (success, failure, cancelled)
   - Branch
   - Actor (who triggered)

**Deployment artifacts:**
- Test coverage reports (if Codecov enabled)
- Workflow logs (available for 90 days)

---

## Troubleshooting

### Test Failures

**Symptom:** Workflow stops at "Run Tests" job with red X

**Diagnosis:**
1. Click on "Run Tests" job
2. Expand "Run backend tests with coverage"
3. Read pytest output

**Common causes:**
- New code broke existing tests
- Missing environment variables in tests
- Database migration not applied in test environment

**Solution:**
```bash
# Run tests locally first
cd backend
uv run pytest -v

# Fix failing tests
# Commit fixes and push
```

### Frontend Build Failures

**Symptom:** "Build frontend" step fails

**Diagnosis:**
1. Check error message in logs
2. Common errors:
   - `npm ci` fails → `package-lock.json` out of sync
   - Build errors → TypeScript/ESLint issues
   - Memory errors → Large bundle size

**Solution:**
```bash
# Test build locally
cd frontend
npm ci
npm run build

# If successful locally but fails in CI:
# - Check Node.js version matches (18.x)
# - Clear npm cache in workflow (add npm cache clean step)
```

### S3 Upload Failures

**Symptom:** "Deploy frontend to S3" step fails

**Common errors:**

**Error: "AccessDenied"**
- **Cause**: IAM user lacks S3 permissions
- **Solution**: Verify IAM policy includes `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket`

**Error: "NoSuchBucket"**
- **Cause**: Bucket name incorrect or bucket doesn't exist
- **Solution**: Verify `S3_BUCKET_NAME` secret matches actual bucket name

**Error: "InvalidAccessKeyId"**
- **Cause**: AWS credentials incorrect or expired
- **Solution**: Regenerate IAM user access keys and update secrets

### CloudFront Invalidation Failures

**Symptom:** "Invalidate CloudFront cache" step fails

**Common errors:**

**Error: "NoSuchDistribution"**
- **Cause**: Distribution ID incorrect
- **Solution**: Verify `CLOUDFRONT_DISTRIBUTION_ID` secret (14-character ID starting with E)

**Error: "AccessDenied"**
- **Cause**: IAM user lacks CloudFront invalidation permission
- **Solution**: Add `cloudfront:CreateInvalidation` to IAM policy

**Note:** Invalidation takes 1-2 minutes to complete. Workflow doesn't wait for completion, it just initiates it.

### EC2 SSH Connection Failures

**Symptom:** "Deploy backend to EC2" step fails with connection error

**Common errors:**

**Error: "Permission denied (publickey)"**
- **Cause**: SSH key incorrect or not authorized on EC2
- **Solution**:
  1. Verify `EC2_SSH_PRIVATE_KEY` secret contains full key including headers
  2. Check key is added to EC2 `~/.ssh/authorized_keys`
  3. Test key locally: `ssh -i ~/.ssh/ci_cd_deploy_key ubuntu@EC2_IP`

**Error: "Connection timed out"**
- **Cause**: EC2 security group blocks SSH from GitHub Actions IPs
- **Solution**: GitHub Actions uses dynamic IPs; must allow SSH from `0.0.0.0/0` or use Systems Manager Session Manager

**Error: "Host key verification failed"**
- **Cause**: EC2 host not in known_hosts
- **Solution**: Workflow includes `ssh-keyscan` step; verify it runs before SSH

**Security Note:** Opening SSH to `0.0.0.0/0` is risky. Consider:
- Restricting to GitHub Actions IP ranges (changes frequently)
- Using AWS Systems Manager Session Manager (no SSH needed)
- Using a bastion host

### Backend Deployment Failures

**Symptom:** SSH connects but deployment script fails

**Common errors:**

**Error: "git pull failed"**
- **Cause**: Git conflicts or EC2 can't reach GitHub
- **Solution**: SSH to EC2 manually and run `git status`, resolve conflicts

**Error: "uv sync failed"**
- **Cause**: Dependency installation error
- **Solution**: Check `pyproject.toml` syntax, verify internet access on EC2

**Error: "alembic upgrade failed"**
- **Cause**: Database migration error
- **Solution**: SSH to EC2, check database file exists and permissions are correct

**Error: "systemctl restart failed"**
- **Cause**: Service not found or permission issue
- **Solution**: Verify systemd service file exists at `/etc/systemd/system/etf-portfolio.service`

**Error: "Health check failed (curl -f returned error)"**
- **Cause**: Backend didn't start properly or is unhealthy
- **Solution**:
  1. SSH to EC2
  2. Check service status: `sudo systemctl status etf-portfolio.service`
  3. Check logs: `sudo journalctl -u etf-portfolio.service -n 50`
  4. Test health: `curl http://localhost:8000/health`

### GitHub Secrets Issues

**Symptom:** Workflow fails with "secret not found" or empty values

**Solution:**
1. Verify secret name matches exactly (case-sensitive)
2. Verify secret exists in repository settings (not organization settings)
3. Check secret value is not empty
4. Re-create secret if needed

**Note:** You cannot view secret values after creation. If unsure, delete and re-create.

---

## Rollback Procedure

### When to Rollback

- Deployment succeeded but application is broken
- New feature causes production issues
- Database migration failed

### Rollback Methods

#### Method 1: Revert Commit and Re-deploy (Recommended)

```bash
# Find the bad commit
git log --oneline

# Revert the bad commit (creates new commit)
git revert <bad-commit-sha>

# Push to main (triggers auto-deployment)
git push origin main
```

**Pros:**
- Safe (preserves history)
- Automatic deployment via CI/CD
- Easy to track what was reverted

**Cons:**
- Takes 5-7 minutes (full deployment)

#### Method 2: Manual Rollback (Faster)

**Backend rollback (SSH to EC2):**

```bash
# SSH to EC2
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@EC2_IP

# Navigate to backend
cd /opt/etf-portfolio/backend

# Reset to previous commit
git log --oneline  # Find good commit
git reset --hard <good-commit-sha>

# Rollback migration if needed
uv run alembic downgrade -1

# Restart service
sudo systemctl restart etf-portfolio.service

# Verify health
curl http://localhost:8000/health
```

**Frontend rollback:**

```bash
# On local machine
cd frontend

# Reset to previous commit
git reset --hard <good-commit-sha>

# Build frontend
npm run build

# Deploy to S3
aws s3 sync dist/ s3://BUCKET_NAME/ \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"

aws s3 cp dist/index.html s3://BUCKET_NAME/index.html \
  --cache-control "public, max-age=300, must-revalidate"

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"
```

**Pros:**
- Faster (immediate rollback)
- More control

**Cons:**
- Manual steps (error-prone)
- Doesn't update git history
- Remember to push correct version to main later

#### Method 3: Database Restore (If Migration Failed)

If database migration broke production:

```bash
# SSH to EC2
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@EC2_IP

# Stop backend service
sudo systemctl stop etf-portfolio.service

# Restore from backup
cd /opt/etf-portfolio/backend
cp portfolio.db portfolio.db.broken
gunzip -c /opt/etf-portfolio/backups/portfolio_YYYYMMDD_HHMMSS.db.gz > portfolio.db

# Restart service
sudo systemctl start etf-portfolio.service

# Verify health
curl http://localhost:8000/health
```

---

## Security Best Practices

### 1. Secrets Management

**Do:**
- ✅ Use GitHub Secrets for all sensitive data
- ✅ Create dedicated CI/CD IAM user (not personal credentials)
- ✅ Use dedicated SSH key for CI/CD (not personal key)
- ✅ Rotate credentials every 90 days
- ✅ Enable MFA on IAM user console access
- ✅ Review IAM permissions regularly (least privilege)

**Don't:**
- ❌ Never commit secrets to code (check with `git log -S "SECRET"`)
- ❌ Never echo secrets in workflow logs
- ❌ Don't reuse personal AWS credentials for CI/CD
- ❌ Don't grant more permissions than needed (avoid `*` policies)
- ❌ Don't use root AWS account credentials

### 2. SSH Key Security

**Best practices:**
- Generate dedicated key for CI/CD (separate from personal)
- Use strong key: RSA 4096-bit or Ed25519
- Store private key only in GitHub Secrets
- Never commit private key to repository
- Rotate SSH keys every 6-12 months
- Remove old keys from EC2 `authorized_keys`

**Alternative: AWS Systems Manager**

Instead of SSH, use AWS Systems Manager Session Manager:
- No open SSH port needed
- Audit logs for all sessions
- IAM-based access control

### 3. IAM Permissions

**Least privilege principle:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::BUCKET_NAME/*"
    },
    {
      "Effect": "Allow",
      "Action": "cloudfront:CreateInvalidation",
      "Resource": "arn:aws:cloudfront::ACCOUNT_ID:distribution/DISTRIBUTION_ID"
    }
  ]
}
```

**Avoid:**
```json
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
```

### 4. Branch Protection

**Enable on main branch:**
1. Go to **Settings** → **Branches**
2. Add rule for `main` branch
3. Enable:
   - ☑ Require pull request before merging
   - ☑ Require status checks to pass (select "Run Tests")
   - ☑ Require branches to be up to date
   - ☑ Do not allow bypassing the above settings

**Result:** Can't merge to main without passing tests.

### 5. Monitoring and Auditing

**Enable:**
- CloudWatch Logs for backend application
- S3 bucket access logging
- CloudFront access logs
- AWS CloudTrail for API activity
- GitHub audit log (organization level)

**Review regularly:**
- Failed deployment attempts
- AWS IAM user activity
- Unusual S3/CloudFront traffic

### 6. Secrets Rotation

**Schedule:**
- AWS access keys: Every 90 days
- SSH keys: Every 6-12 months
- Review all secrets: Quarterly

**How to rotate:**
1. Create new credentials (IAM access key, SSH key)
2. Update GitHub Secrets
3. Test deployment with new credentials
4. Delete old credentials
5. Document rotation in security log

---

## Additional Resources

- **GitHub Actions Documentation**: https://docs.github.com/en/actions
- **AWS CLI Documentation**: https://docs.aws.amazon.com/cli/
- **IAM Best Practices**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- **Backend Testing**: `backend/README.md`
- **Manual Deployment**: `DEPLOYMENT.md`

---

**CI/CD Pipeline Version:** 1.0
**Last Updated:** December 2025
**Maintained By:** ETF Portfolio Tracker Team
