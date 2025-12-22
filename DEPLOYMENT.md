# AWS Deployment Guide: ETF Portfolio Tracker

This guide provides step-by-step instructions for deploying the ETF Portfolio Tracker application to AWS with a cost-optimized architecture using S3 + CloudFront for the frontend and a small EC2 instance for the backend.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Cost Estimates](#cost-estimates)
- [Prerequisites](#prerequisites)
- [Phase 1: AWS Infrastructure Setup](#phase-1-aws-infrastructure-setup)
- [Phase 2: Backend Deployment (EC2)](#phase-2-backend-deployment-ec2)
- [Phase 3: Frontend Deployment (S3)](#phase-3-frontend-deployment-s3)
- [Phase 4: CloudFront Configuration](#phase-4-cloudfront-configuration)
- [Phase 5: Security Hardening](#phase-5-security-hardening)
- [Phase 6: Database Backup Strategy](#phase-6-database-backup-strategy)
- [Phase 7: Monitoring & Maintenance](#phase-7-monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Deployment Checklists](#deployment-checklists)

---

## Architecture Overview

```
┌──────────┐
│   User   │
└────┬─────┘
     │ HTTPS
     ▼
┌─────────────────────┐
│ CloudFront (CDN)    │
│ AWS-managed HTTPS   │
└──────┬──────────────┘
       │
       ├──► /* (Default) ─────► S3 Bucket (Static Files)
       │                        ├─ index.html
       │                        ├─ assets/
       │                        └─ (React build output)
       │
       └──► /api/* ────────────► EC2 t3.micro (HTTP:8000)
                                  ├─ FastAPI + Uvicorn
                                  ├─ Python 3.12
                                  └─ SQLite Database
```

**Key Design Decisions:**
- **CloudFront** handles HTTPS termination with AWS-managed certificates (free)
- **EC2** runs HTTP only (no SSL overhead, CloudFront handles encryption)
- **SQLite** on EC2 for cost optimization (no RDS fees)
- **Systemd** manages the Python process (auto-restart on failure)
- **Single-user** application (no horizontal scaling needed)

---

## Cost Estimates

### Monthly Cost Breakdown

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **EC2 t3.micro** | 730 hours × $0.0104/hr | $7.50 |
| **EBS gp3 Storage** | 20 GB × $0.08/GB | $1.60 |
| **CloudFront** | 50 GB free tier, then $0.085/GB | $1-5 |
| **S3 Storage** | ~20 GB × $0.023/GB | $0.50 |
| **Data Transfer** | Variable (first 1 GB free) | $0-2 |
| **CloudWatch Logs** | Optional (5 GB free tier) | $0-1 |
| **Total** | | **$10-15/month** |

**Cost Optimization Tips:**
- Use **t4g.micro** (ARM-based) instead of t3.micro for 20% savings (~$6/month vs $7.50)
- CloudFront has 50 GB/month free data transfer (first year, 10 GB after)
- First 1,000 CloudFront invalidations per month are free
- S3 storage is minimal for static frontend assets
- No RDS costs (using SQLite)

---

## Prerequisites

### AWS Account Setup
1. **AWS Account** with administrative access
2. **AWS CLI** installed and configured
   ```bash
   # Install AWS CLI (macOS)
   brew install awscli

   # Or download from: https://aws.amazon.com/cli/

   # Configure AWS CLI
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region (e.g., us-east-1), Output format (json)
   ```

3. **Verify AWS CLI configuration:**
   ```bash
   aws sts get-caller-identity
   ```

### Local Development Environment
- **Node.js** 18+ and npm (for frontend build)
- **Git** (for code deployment)
- **SSH client** (for EC2 access)

### Repository Access
- Application code available locally at:
  - Backend: `backend/`
  - Frontend: `frontend/`

---

## Phase 1: AWS Infrastructure Setup

### Step 1.1: Create S3 Bucket for Frontend

```bash
# Set variables (replace with your preferences)
BUCKET_NAME="etf-portfolio-frontend-$(date +%s)"
AWS_REGION="us-east-1"  # Choose your preferred region

# Create S3 bucket
aws s3 mb s3://$BUCKET_NAME --region $AWS_REGION

# Disable public access (CloudFront will access via OAI)
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Enable versioning (recommended for rollback capability)
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Save bucket name for later steps
echo "S3_BUCKET=$BUCKET_NAME" >> deployment-vars.txt
```

---

### Step 1.2: Launch EC2 Instance

#### Create Key Pair for SSH Access

```bash
# Create key pair
aws ec2 create-key-pair \
  --key-name etf-portfolio-backend-key \
  --query 'KeyMaterial' \
  --output text > ~/.ssh/etf-portfolio-backend-key.pem

# Set proper permissions
chmod 400 ~/.ssh/etf-portfolio-backend-key.pem
```

#### Create Security Group

```bash
# Create security group
SG_ID=$(aws ec2 create-security-group \
  --group-name etf-portfolio-backend-sg \
  --description "Security group for ETF Portfolio backend" \
  --query 'GroupId' \
  --output text)

echo "Created security group: $SG_ID"
echo "SECURITY_GROUP_ID=$SG_ID" >> deployment-vars.txt

# Allow SSH from your IP (replace YOUR_IP with your public IP)
# Get your IP: curl -s https://checkip.amazonaws.com
YOUR_IP=$(curl -s https://checkip.amazonaws.com)

aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 22 \
  --cidr $YOUR_IP/32

# Allow HTTP port 8000 from anywhere (temporary - will restrict to CloudFront later)
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0
```

#### Launch EC2 Instance

```bash
# Find Ubuntu 24.04 LTS AMI for your region
AMI_ID=$(aws ec2 describe-images \
  --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*" \
            "Name=state,Values=available" \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text)

echo "Using AMI: $AMI_ID"

# Launch t3.micro instance (or t4g.micro for ARM-based, 20% cheaper)
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.micro \
  --key-name etf-portfolio-backend-key \
  --security-group-ids $SG_ID \
  --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=20,VolumeType=gp3}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=etf-portfolio-backend}]' \
  --query 'Instances[0].InstanceId' \
  --output text)

echo "Launched instance: $INSTANCE_ID"
echo "INSTANCE_ID=$INSTANCE_ID" >> deployment-vars.txt

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $INSTANCE_ID
echo "Instance is now running"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' \
  --output text)

echo "Instance Public IP: $PUBLIC_IP"
echo "PUBLIC_IP=$PUBLIC_IP" >> deployment-vars.txt
```

#### Allocate Elastic IP (Optional but Recommended)

```bash
# Allocate Elastic IP
EIP_ALLOC=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)

# Associate with instance
aws ec2 associate-address \
  --instance-id $INSTANCE_ID \
  --allocation-id $EIP_ALLOC

# Get new Elastic IP
PUBLIC_IP=$(aws ec2 describe-addresses \
  --allocation-ids $EIP_ALLOC \
  --query 'Addresses[0].PublicIp' \
  --output text)

echo "Elastic IP: $PUBLIC_IP"
echo "PUBLIC_IP=$PUBLIC_IP" >> deployment-vars.txt
```

---

### Step 1.3: Create CloudFront Origin Access Identity (OAI)

```bash
# Create OAI for S3 access
OAI_ID=$(aws cloudfront create-cloud-front-origin-access-identity \
  --cloud-front-origin-access-identity-config \
    CallerReference=$(date +%s),Comment="OAI for ETF Portfolio S3" \
  --query 'CloudFrontOriginAccessIdentity.Id' \
  --output text)

echo "Created OAI: $OAI_ID"
echo "OAI_ID=$OAI_ID" >> deployment-vars.txt

# Get OAI canonical user for S3 bucket policy
OAI_CANONICAL_USER=$(aws cloudfront get-cloud-front-origin-access-identity \
  --id $OAI_ID \
  --query 'CloudFrontOriginAccessIdentity.S3CanonicalUserId' \
  --output text)

echo "OAI_CANONICAL_USER=$OAI_CANONICAL_USER" >> deployment-vars.txt
```

---

## Phase 2: Backend Deployment (EC2)

### Step 2.1: Connect to EC2 Instance

```bash
# SSH into the instance (replace PUBLIC_IP with your instance IP)
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@$PUBLIC_IP
```

From this point, commands run on the **EC2 instance** unless specified otherwise.

---

### Step 2.2: Update System and Install Dependencies

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# Verify Python 3.12 (Ubuntu 24.04 includes it)
python3 --version  # Should show Python 3.12.x

# Install build dependencies
sudo apt install -y build-essential libssl-dev libffi-dev git curl python3-pip

# Install sqlite3 CLI (for database management)
sudo apt install -y sqlite3
```

---

### Step 2.3: Install UV Package Manager

```bash
# Install UV (official Rust-based Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add UV to PATH
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
uv --version
```

---

### Step 2.4: Deploy Application Code

#### Option A: Git Clone (Recommended for Production)

```bash
# Create application directory
sudo mkdir -p /opt/etf-portfolio
sudo chown ubuntu:ubuntu /opt/etf-portfolio
cd /opt/etf-portfolio

# Clone repository (replace with your repository URL)
git clone https://github.com/YOUR_USERNAME/finance_track_webapp.git .

# Or if using a specific branch
git clone -b main https://github.com/YOUR_USERNAME/finance_track_webapp.git .
```

#### Option B: rsync from Local Machine

On your **local machine**, run:

```bash
# From project root directory
rsync -avz --exclude='node_modules' \
           --exclude='.venv' \
           --exclude='__pycache__' \
           --exclude='*.pyc' \
           --exclude='.git' \
           --exclude='portfolio.db' \
           backend/ ubuntu@$PUBLIC_IP:/opt/etf-portfolio/backend/

# Verify upload
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@$PUBLIC_IP "ls -la /opt/etf-portfolio/backend"
```

---

### Step 2.5: Configure Backend Environment

Back on **EC2 instance**:

```bash
cd /opt/etf-portfolio/backend

# Create production .env file
cat > .env << 'EOF'
DATABASE_URL=sqlite:////opt/etf-portfolio/backend/portfolio.db
API_V1_PREFIX=/api/v1
PROJECT_NAME=ETF Portfolio Tracker
DEBUG=False
CORS_ORIGINS=["https://CLOUDFRONT_DOMAIN_PLACEHOLDER"]

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF

# Note: We'll update CORS_ORIGINS with the actual CloudFront domain later
```

**Important Configuration Notes:**
- `DATABASE_URL`: Use absolute path for SQLite database
- `DEBUG=False`: Disables debug mode in production
- `CORS_ORIGINS`: Will be updated after CloudFront distribution is created
- `LOG_LEVEL=INFO`: Production logging level
- `LOG_FORMAT=json`: Structured logging for CloudWatch

---

### Step 2.6: Install Dependencies and Setup Database

```bash
cd /opt/etf-portfolio/backend

# Install all dependencies (including dev tools)
uv sync --all-extras

# Verify UV virtual environment created
ls -la .venv/

# Run database migrations
uv run alembic upgrade head

# Verify database file created
ls -lh portfolio.db

# Set proper permissions
chmod 644 portfolio.db
```

---

### Step 2.7: Create Systemd Service for Auto-Start

```bash
# Create systemd service file
sudo tee /etc/systemd/system/etf-portfolio.service > /dev/null << 'EOF'
[Unit]
Description=ETF Portfolio Tracker Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/etf-portfolio/backend
Environment="PATH=/home/ubuntu/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/ubuntu/.cargo/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=etf-portfolio

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/etf-portfolio/backend

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable etf-portfolio.service

# Start the service
sudo systemctl start etf-portfolio.service

# Check service status
sudo systemctl status etf-portfolio.service
```

**Expected Output:**
```
● etf-portfolio.service - ETF Portfolio Tracker Backend API
     Loaded: loaded (/etc/systemd/system/etf-portfolio.service; enabled)
     Active: active (running) since ...
```

---

### Step 2.8: Verify Backend Health

```bash
# Test health endpoint locally
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Test API endpoint
curl http://localhost:8000/api/v1/analytics/portfolio-summary
# Expected: JSON response with portfolio data

# View logs
sudo journalctl -u etf-portfolio.service -f

# Press Ctrl+C to stop following logs
```

**Test from your local machine:**
```bash
# Replace PUBLIC_IP with your EC2 public IP
curl http://PUBLIC_IP:8000/health
```

---

## Phase 3: Frontend Deployment (S3)

These steps run on your **local machine**.

### Step 3.1: Build Frontend for Production

```bash
# Navigate to frontend directory
cd frontend

# Verify production environment file
cat .env.production
# Should contain: VITE_API_URL=/api/v1

# Install dependencies (if not already installed)
npm install

# Build for production
npm run build

# Verify build output
ls -lh dist/
# Should see: index.html, assets/ directory, etc.
```

**Build Output Structure:**
```
dist/
├── index.html
├── assets/
│   ├── index-abc123.js       # Hashed JS bundle
│   ├── index-def456.css      # Hashed CSS bundle
│   └── logo-ghi789.png       # Other assets
└── vite.svg                  # Favicon
```

---

### Step 3.2: Upload to S3 with Cache Headers

```bash
# Load variables from Phase 1
source deployment-vars.txt

# Upload all files except index.html with long cache (1 year)
aws s3 sync dist/ s3://$BUCKET_NAME/ \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"

# Upload index.html separately with short cache (5 minutes)
aws s3 cp dist/index.html s3://$BUCKET_NAME/index.html \
  --cache-control "public, max-age=300, must-revalidate"

# Verify upload
aws s3 ls s3://$BUCKET_NAME/ --recursive
```

**Caching Strategy Explanation:**
- **Static assets** (JS/CSS with hashed names): 1-year cache for maximum performance
- **index.html**: 5-minute cache to allow quick updates
- `--delete` flag removes old files from S3 (clean deployment)

---

### Step 3.3: Configure S3 Bucket Policy for CloudFront OAI

```bash
# Create bucket policy JSON
cat > s3-bucket-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CloudFrontOAIAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::cloudfront:user/CloudFront Origin Access Identity $OAI_ID"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::$BUCKET_NAME/*"
    }
  ]
}
EOF

# Apply bucket policy
aws s3api put-bucket-policy \
  --bucket $BUCKET_NAME \
  --policy file://s3-bucket-policy.json

echo "S3 bucket policy applied successfully"
```

---

## Phase 4: CloudFront Configuration

### Step 4.1: Create CloudFront Distribution

**Note:** CloudFront distribution creation is complex. We'll use a JSON configuration file.

#### Create CloudFront Configuration File

```bash
# Load variables
source deployment-vars.txt

# Get EC2 public DNS name (required for CloudFront origin)
EC2_DNS=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicDnsName' \
  --output text)

echo "EC2 DNS: $EC2_DNS"

# Create CloudFront distribution config
cat > cloudfront-distribution-config.json << EOF
{
  "CallerReference": "etf-portfolio-$(date +%s)",
  "Comment": "ETF Portfolio Tracker - S3 Frontend + EC2 Backend",
  "Enabled": true,
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 2,
    "Items": [
      {
        "Id": "S3-Frontend",
        "DomainName": "$BUCKET_NAME.s3.amazonaws.com",
        "S3OriginConfig": {
          "OriginAccessIdentity": "origin-access-identity/cloudfront/$OAI_ID"
        }
      },
      {
        "Id": "EC2-Backend",
        "DomainName": "$EC2_DNS",
        "CustomOriginConfig": {
          "HTTPPort": 8000,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "http-only",
          "OriginSSLProtocols": {
            "Quantity": 1,
            "Items": ["TLSv1.2"]
          },
          "OriginReadTimeout": 30,
          "OriginKeepaliveTimeout": 5
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "S3-Frontend",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "Compress": true,
    "ForwardedValues": {
      "QueryString": false,
      "Cookies": {
        "Forward": "none"
      }
    },
    "MinTTL": 0,
    "DefaultTTL": 86400,
    "MaxTTL": 31536000
  },
  "CacheBehaviors": {
    "Quantity": 1,
    "Items": [
      {
        "PathPattern": "/api/*",
        "TargetOriginId": "EC2-Backend",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
          "Quantity": 7,
          "Items": ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"],
          "CachedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"]
          }
        },
        "Compress": false,
        "ForwardedValues": {
          "QueryString": true,
          "Cookies": {
            "Forward": "all"
          },
          "Headers": {
            "Quantity": 4,
            "Items": ["Authorization", "Content-Type", "Accept", "Origin"]
          }
        },
        "MinTTL": 0,
        "DefaultTTL": 0,
        "MaxTTL": 0
      }
    ]
  },
  "CustomErrorResponses": {
    "Quantity": 2,
    "Items": [
      {
        "ErrorCode": 404,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      },
      {
        "ErrorCode": 403,
        "ResponsePagePath": "/index.html",
        "ResponseCode": "200",
        "ErrorCachingMinTTL": 300
      }
    ]
  },
  "ViewerCertificate": {
    "CloudFrontDefaultCertificate": true,
    "MinimumProtocolVersion": "TLSv1.2_2021"
  }
}
EOF
```

#### Create CloudFront Distribution

```bash
# Create distribution
DISTRIBUTION_ID=$(aws cloudfront create-distribution \
  --distribution-config file://cloudfront-distribution-config.json \
  --query 'Distribution.Id' \
  --output text)

echo "Created CloudFront distribution: $DISTRIBUTION_ID"
echo "DISTRIBUTION_ID=$DISTRIBUTION_ID" >> deployment-vars.txt

# Get CloudFront domain name
CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
  --id $DISTRIBUTION_ID \
  --query 'Distribution.DomainName' \
  --output text)

echo "CloudFront domain: $CLOUDFRONT_DOMAIN"
echo "CLOUDFRONT_DOMAIN=$CLOUDFRONT_DOMAIN" >> deployment-vars.txt

echo "----------------------------------------------"
echo "CloudFront distribution is being deployed..."
echo "This can take 15-30 minutes."
echo "----------------------------------------------"
echo "Your application will be available at:"
echo "https://$CLOUDFRONT_DOMAIN"
echo "----------------------------------------------"
```

#### Wait for Distribution Deployment

```bash
# Wait for distribution to be deployed (takes 15-30 minutes)
aws cloudfront wait distribution-deployed --id $DISTRIBUTION_ID

echo "CloudFront distribution deployed successfully!"
```

---

### Step 4.2: Update Backend CORS Configuration

Now that we have the CloudFront domain, update the backend `.env` file.

**On EC2 instance:**

```bash
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@$PUBLIC_IP

cd /opt/etf-portfolio/backend

# Update CORS_ORIGINS with CloudFront domain
# Replace CLOUDFRONT_DOMAIN_PLACEHOLDER with your actual CloudFront domain
sed -i 's|CLOUDFRONT_DOMAIN_PLACEHOLDER|YOUR_CLOUDFRONT_DOMAIN|g' .env

# Example: If your CloudFront domain is d1234567890abc.cloudfront.net
# CORS_ORIGINS=["https://d1234567890abc.cloudfront.net"]

# Restart backend service
sudo systemctl restart etf-portfolio.service

# Verify service restarted successfully
sudo systemctl status etf-portfolio.service

# Check logs for CORS configuration
sudo journalctl -u etf-portfolio.service -n 20
```

---

## Phase 5: Security Hardening

### Step 5.1: Restrict EC2 Security Group to CloudFront Only

**On your local machine:**

```bash
# Load variables
source deployment-vars.txt

# Remove open port 8000 rule
aws ec2 revoke-security-group-ingress \
  --group-id $SG_ID \
  --protocol tcp \
  --port 8000 \
  --cidr 0.0.0.0/0

# Get CloudFront managed prefix list ID
PREFIX_LIST_ID=$(aws ec2 describe-managed-prefix-lists \
  --filters Name=prefix-list-name,Values="com.amazonaws.global.cloudfront.origin-facing" \
  --query 'PrefixLists[0].PrefixListId' \
  --output text)

echo "CloudFront Prefix List: $PREFIX_LIST_ID"

# Allow port 8000 from CloudFront prefix list only
aws ec2 authorize-security-group-ingress \
  --group-id $SG_ID \
  --ip-permissions IpProtocol=tcp,FromPort=8000,ToPort=8000,PrefixListIds="[{PrefixListId=$PREFIX_LIST_ID}]"

echo "Security group restricted to CloudFront only"
```

**Verification:**

```bash
# This should timeout or refuse connection (backend not directly accessible)
curl http://$PUBLIC_IP:8000/health

# This should work (access via CloudFront)
curl https://$CLOUDFRONT_DOMAIN/api/v1/health
```

---

### Step 5.2: Verify Security Configuration

**Backend Security Checklist:**
- [ ] `DEBUG=False` in `.env`
- [ ] `CORS_ORIGINS` includes CloudFront domain (HTTPS)
- [ ] EC2 security group allows port 8000 only from CloudFront
- [ ] SSH port 22 restricted to your IP only

**Frontend Security Checklist:**
- [ ] S3 bucket blocks all public access
- [ ] S3 bucket policy allows only CloudFront OAI
- [ ] CloudFront uses HTTPS (redirect-to-https enabled)

---

## Phase 6: Database Backup Strategy

### Step 6.1: Create Automated Backup Script

**On EC2 instance:**

```bash
# Create backup directory
sudo mkdir -p /opt/etf-portfolio/backups

# Create backup script
sudo tee /opt/etf-portfolio/backup-db.sh > /dev/null << 'EOF'
#!/bin/bash

# Configuration
BACKUP_DIR="/opt/etf-portfolio/backups"
DB_PATH="/opt/etf-portfolio/backend/portfolio.db"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Create SQLite backup using .backup command (consistent, hot backup)
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/portfolio_$DATE.db'"

# Compress backup
gzip $BACKUP_DIR/portfolio_$DATE.db

# Log success
echo "$(date): Backup completed - portfolio_$DATE.db.gz"

# Delete backups older than RETENTION_DAYS
find $BACKUP_DIR -name "portfolio_*.db.gz" -mtime +$RETENTION_DAYS -delete

# Log cleanup
echo "$(date): Old backups cleaned up (retention: $RETENTION_DAYS days)"
EOF

# Make script executable
sudo chmod +x /opt/etf-portfolio/backup-db.sh

# Set proper ownership
sudo chown ubuntu:ubuntu /opt/etf-portfolio/backup-db.sh
sudo chown ubuntu:ubuntu /opt/etf-portfolio/backups

# Test backup script
/opt/etf-portfolio/backup-db.sh

# Verify backup created
ls -lh /opt/etf-portfolio/backups/
```

---

### Step 6.2: Schedule Daily Backups with Cron

```bash
# Open crontab editor
crontab -e

# Add line to run backup daily at 2 AM UTC
# (Paste this line in the crontab editor)
0 2 * * * /opt/etf-portfolio/backup-db.sh >> /var/log/db-backup.log 2>&1

# Save and exit (Ctrl+X, then Y, then Enter in nano)

# Verify cron job added
crontab -l
```

---

### Step 6.3: Optional: Upload Backups to S3

**Create S3 backup bucket:**

```bash
# On local machine
BACKUP_BUCKET="etf-portfolio-backups-$(date +%s)"

aws s3 mb s3://$BACKUP_BUCKET

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $BACKUP_BUCKET \
  --versioning-configuration Status=Enabled

# Create lifecycle policy to delete backups older than 30 days
cat > s3-lifecycle.json << EOF
{
  "Rules": [
    {
      "Id": "DeleteOldBackups",
      "Status": "Enabled",
      "Expiration": {
        "Days": 30
      },
      "Filter": {
        "Prefix": ""
      }
    }
  ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket $BACKUP_BUCKET \
  --lifecycle-configuration file://s3-lifecycle.json

echo "Backup bucket created: $BACKUP_BUCKET"
```

**Update backup script to upload to S3:**

On EC2 instance, edit `/opt/etf-portfolio/backup-db.sh` and add before the cleanup section:

```bash
# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/portfolio_$DATE.db.gz s3://YOUR_BACKUP_BUCKET/ --only-show-errors
```

---

### Step 6.4: Restore from Backup

**To restore a backup:**

```bash
# On EC2 instance
cd /opt/etf-portfolio/backend

# Stop the service
sudo systemctl stop etf-portfolio.service

# Backup current database (just in case)
cp portfolio.db portfolio.db.before-restore

# Restore from compressed backup
gunzip -c /opt/etf-portfolio/backups/portfolio_20250122_020000.db.gz > portfolio.db

# Restart service
sudo systemctl start etf-portfolio.service

# Verify restoration
curl http://localhost:8000/api/v1/analytics/portfolio-summary
```

---

## Phase 7: Monitoring & Maintenance

### Step 7.1: Set Up Billing Alerts

**On local machine:**

```bash
# Create SNS topic for billing alerts
TOPIC_ARN=$(aws sns create-topic \
  --name etf-portfolio-billing-alerts \
  --query 'TopicArn' \
  --output text)

echo "SNS Topic ARN: $TOPIC_ARN"

# Subscribe your email to the topic
aws sns subscribe \
  --topic-arn $TOPIC_ARN \
  --protocol email \
  --notification-endpoint your-email@example.com

echo "Check your email and confirm the subscription!"

# Create billing alarm (alert if monthly bill exceeds $20)
aws cloudwatch put-metric-alarm \
  --alarm-name etf-portfolio-billing-alert \
  --alarm-description "Alert if monthly bill exceeds $20" \
  --metric-name EstimatedCharges \
  --namespace AWS/Billing \
  --statistic Maximum \
  --period 21600 \
  --threshold 20 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions $TOPIC_ARN \
  --dimensions Name=Currency,Value=USD

echo "Billing alarm created (threshold: $20/month)"
```

---

### Step 7.2: Create Health Check Script

**On EC2 instance:**

```bash
# Create health check script
sudo tee /opt/etf-portfolio/health-check.sh > /dev/null << 'EOF'
#!/bin/bash

HEALTH_URL="http://localhost:8000/health"
RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

if [ "$RESPONSE_CODE" -eq 200 ]; then
  echo "[$TIMESTAMP] Health check PASSED (HTTP $RESPONSE_CODE)"
  exit 0
else
  echo "[$TIMESTAMP] Health check FAILED (HTTP $RESPONSE_CODE)"

  # Attempt automatic recovery
  echo "[$TIMESTAMP] Attempting service restart..."
  sudo systemctl restart etf-portfolio.service
  sleep 5

  # Re-check after restart
  RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)
  if [ "$RESPONSE_CODE" -eq 200 ]; then
    echo "[$TIMESTAMP] Service restart SUCCESSFUL"
    exit 0
  else
    echo "[$TIMESTAMP] Service restart FAILED - manual intervention required"
    exit 1
  fi
fi
EOF

sudo chmod +x /opt/etf-portfolio/health-check.sh
sudo chown ubuntu:ubuntu /opt/etf-portfolio/health-check.sh

# Test health check
/opt/etf-portfolio/health-check.sh

# Schedule health check every 5 minutes
crontab -e

# Add line:
*/5 * * * * /opt/etf-portfolio/health-check.sh >> /var/log/health-check.log 2>&1
```

---

### Step 7.3: Application Update Procedures

#### Update Backend

**On EC2 instance:**

```bash
# SSH into EC2
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@$PUBLIC_IP

# Navigate to application directory
cd /opt/etf-portfolio/backend

# Pull latest code
git pull origin main

# Install new dependencies (if any)
uv sync --all-extras

# Run database migrations (if any)
uv run alembic upgrade head

# Restart service
sudo systemctl restart etf-portfolio.service

# Verify service status
sudo systemctl status etf-portfolio.service

# Check logs for errors
sudo journalctl -u etf-portfolio.service -n 50

# Test health endpoint
curl http://localhost:8000/health
```

#### Update Frontend

**On local machine:**

```bash
# Navigate to frontend directory
cd frontend

# Pull latest code
git pull origin main

# Install new dependencies (if any)
npm install

# Build for production
npm run build

# Load deployment variables
source deployment-vars.txt

# Upload to S3 with cache headers
aws s3 sync dist/ s3://$BUCKET_NAME/ \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"

aws s3 cp dist/index.html s3://$BUCKET_NAME/index.html \
  --cache-control "public, max-age=300, must-revalidate"

# Invalidate CloudFront cache for immediate update
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

# Check invalidation status
aws cloudfront list-invalidations \
  --distribution-id $DISTRIBUTION_ID

echo "Frontend updated successfully!"
```

---

### Step 7.4: Optional: CloudWatch Logs Setup

**On EC2 instance:**

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Create CloudWatch config
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/config.json > /dev/null << 'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/syslog",
            "log_group_name": "/aws/ec2/etf-portfolio/syslog",
            "log_stream_name": "{instance_id}"
          }
        ]
      },
      "journal": {
        "unit_name": "etf-portfolio.service",
        "log_group_name": "/aws/ec2/etf-portfolio/application",
        "log_stream_name": "{instance_id}"
      }
    }
  }
}
EOF

# Start CloudWatch agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json
```

**View logs in CloudWatch (local machine):**

```bash
# Tail application logs
aws logs tail /aws/ec2/etf-portfolio/application --follow
```

---

## Troubleshooting

### Backend Issues

#### Service Not Starting

```bash
# Check service status
sudo systemctl status etf-portfolio.service

# View detailed logs (last 100 lines)
sudo journalctl -u etf-portfolio.service -n 100 --no-pager

# Check if port 8000 is in use
sudo lsof -i :8000

# Test manual start for debugging
cd /opt/etf-portfolio/backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Check environment variables
cat /opt/etf-portfolio/backend/.env
```

#### Database Issues

```bash
# Check database file exists
ls -lh /opt/etf-portfolio/backend/portfolio.db

# Check database integrity
sqlite3 /opt/etf-portfolio/backend/portfolio.db "PRAGMA integrity_check;"

# View current migration version
cd /opt/etf-portfolio/backend
uv run alembic current

# Force migration to latest
uv run alembic upgrade head

# Check WAL mode (should return "wal")
sqlite3 /opt/etf-portfolio/backend/portfolio.db "PRAGMA journal_mode;"
```

#### CORS Errors

```bash
# Verify CORS_ORIGINS in .env
cat /opt/etf-portfolio/backend/.env | grep CORS_ORIGINS

# Should be: CORS_ORIGINS=["https://d1234567890abc.cloudfront.net"]

# Update if incorrect
nano /opt/etf-portfolio/backend/.env

# Restart service after change
sudo systemctl restart etf-portfolio.service

# Verify in logs that CORS is configured correctly
sudo journalctl -u etf-portfolio.service -n 20 | grep -i cors
```

---

### Frontend Issues

#### 404 Errors on React Router Paths

**Problem:** Refreshing on routes like `/transactions` returns 404.

**Solution:** Verify CloudFront custom error responses.

```bash
# Check CloudFront error pages configuration
aws cloudfront get-distribution-config \
  --id $DISTRIBUTION_ID \
  --query 'DistributionConfig.CustomErrorResponses'

# Should show 404 → /index.html with 200 response code
```

If missing, update CloudFront distribution to add custom error responses for 404 and 403.

#### API Requests Failing

```bash
# Test backend via CloudFront
curl https://$CLOUDFRONT_DOMAIN/api/v1/health

# Check CloudFront behavior for /api/* pattern
aws cloudfront get-distribution-config \
  --id $DISTRIBUTION_ID \
  --query 'DistributionConfig.CacheBehaviors.Items[?PathPattern==`/api/*`]'

# Verify EC2 security group allows CloudFront
aws ec2 describe-security-groups --group-ids $SG_ID
```

#### Stale Cache After Update

```bash
# Invalidate entire distribution
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

# Or invalidate specific files
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/index.html" "/assets/*"

# Check invalidation status
aws cloudfront list-invalidations --distribution-id $DISTRIBUTION_ID
```

---

### Performance Issues

#### High CPU on EC2

```bash
# Check CPU usage
top

# View Uvicorn worker processes
ps aux | grep uvicorn

# Consider reducing workers in systemd service
sudo nano /etc/systemd/system/etf-portfolio.service
# Change: --workers 4  →  --workers 2

sudo systemctl daemon-reload
sudo systemctl restart etf-portfolio.service
```

#### Database Lock Issues (SQLite)

```bash
# Check for long-running transactions
sqlite3 /opt/etf-portfolio/backend/portfolio.db ".timeout 5000"

# Verify WAL mode is enabled (should return "wal")
sqlite3 /opt/etf-portfolio/backend/portfolio.db "PRAGMA journal_mode;"

# Enable WAL if not set
sqlite3 /opt/etf-portfolio/backend/portfolio.db "PRAGMA journal_mode=WAL;"
```

---

## Deployment Checklists

### Pre-Deployment Checklist

Infrastructure:
- [ ] AWS CLI installed and configured
- [ ] S3 bucket created with versioning enabled
- [ ] EC2 instance launched (t3.micro, Ubuntu 24.04)
- [ ] Security group configured (SSH + port 8000)
- [ ] Elastic IP allocated and associated (optional)
- [ ] CloudFront OAI created

Backend:
- [ ] Python 3.12 and UV installed on EC2
- [ ] Application code deployed to `/opt/etf-portfolio`
- [ ] Production `.env` file created
- [ ] Dependencies installed (`uv sync --all-extras`)
- [ ] Database migrations applied (`uv run alembic upgrade head`)
- [ ] Systemd service created and enabled
- [ ] Service running and health check passing

Frontend:
- [ ] Node.js and npm installed locally
- [ ] Frontend built with production env (`npm run build`)
- [ ] Build output verified (`dist/` directory exists)

CloudFront:
- [ ] CloudFront distribution created with dual origins
- [ ] S3 bucket policy allows CloudFront OAI access
- [ ] Distribution deployed (status: Deployed)
- [ ] CloudFront domain obtained

---

### Post-Deployment Verification Checklist

Application Access:
- [ ] Access CloudFront URL in browser (HTTPS)
- [ ] Frontend loads correctly (no console errors)
- [ ] Navigation works (Dashboard, Transactions, ISIN Metadata, etc.)
- [ ] API requests work (create transaction, view analytics)
- [ ] No CORS errors in browser console

Backend:
- [ ] Health endpoint accessible: `https://[CLOUDFRONT_DOMAIN]/api/v1/health`
- [ ] Backend logs show no errors: `sudo journalctl -u etf-portfolio.service`
- [ ] Database file exists and has data
- [ ] Systemd service enabled for auto-start

Security:
- [ ] Backend CORS_ORIGINS includes CloudFront domain
- [ ] EC2 security group restricted to CloudFront prefix list only
- [ ] Direct EC2 access blocked (test: `curl http://PUBLIC_IP:8000/health` should timeout)
- [ ] S3 bucket blocks public access
- [ ] DEBUG=False in backend `.env`

Reliability:
- [ ] Service auto-starts after EC2 reboot
- [ ] Database backups scheduled (cron job)
- [ ] Health check script configured
- [ ] Billing alerts configured

---

### Security Hardening Checklist

Backend:
- [ ] `DEBUG=False` in production `.env`
- [ ] `CORS_ORIGINS` set to CloudFront domain only (HTTPS)
- [ ] `LOG_LEVEL=INFO` (not DEBUG)
- [ ] Database file has proper permissions (644)
- [ ] Application directory owned by `ubuntu` user
- [ ] Systemd service has security hardening enabled

EC2 Instance:
- [ ] Security group allows SSH only from your IP
- [ ] Security group allows port 8000 only from CloudFront prefix list
- [ ] System packages updated regularly
- [ ] SSH uses key-based authentication (no password)
- [ ] Elastic IP used (prevents IP changes)

CloudFront & S3:
- [ ] CloudFront enforces HTTPS (`redirect-to-https`)
- [ ] S3 bucket has all public access blocked
- [ ] S3 bucket policy allows only CloudFront OAI
- [ ] CloudFront uses TLS 1.2 minimum

Monitoring:
- [ ] Billing alerts configured
- [ ] Health check script with auto-restart
- [ ] CloudWatch logs enabled (optional)
- [ ] Database backups automated and tested

---

## Summary

You have successfully deployed the ETF Portfolio Tracker application to AWS with a cost-optimized architecture!

**Your Application URLs:**
- **Frontend:** `https://[YOUR_CLOUDFRONT_DOMAIN]`
- **Backend API:** `https://[YOUR_CLOUDFRONT_DOMAIN]/api/v1`
- **API Docs:** `https://[YOUR_CLOUDFRONT_DOMAIN]/api/v1/docs`
- **Health Check:** `https://[YOUR_CLOUDFRONT_DOMAIN]/api/v1/health`

**Architecture Summary:**
- **Frontend:** S3 + CloudFront (global CDN with HTTPS)
- **Backend:** EC2 t3.micro (Ubuntu 24.04, Python 3.12, FastAPI)
- **Database:** SQLite with daily automated backups
- **Cost:** ~$10-15/month

**Next Steps:**
1. Test all application features end-to-end
2. Set up monitoring and alerts
3. Document your CloudFront domain for team access
4. Schedule regular updates and maintenance

**Support:**
- Backend documentation: `backend/README.md`
- Frontend documentation: `frontend/README.md`
- Development guide: `CLAUDE.md`

---

## Additional Resources

### AWS Documentation
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [EC2 User Guide](https://docs.aws.amazon.com/ec2/)

### Application Documentation
- **Backend API:** See `backend/README.md` for complete API documentation
- **Frontend:** See `frontend/README.md` for component architecture
- **Development:** See `CLAUDE.md` for local development setup

### Cost Management
- [AWS Cost Explorer](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/)
- [AWS Free Tier](https://aws.amazon.com/free/)
- [CloudFront Pricing](https://aws.amazon.com/cloudfront/pricing/)
- [EC2 Pricing Calculator](https://calculator.aws/)

### Troubleshooting
- Check application logs: `sudo journalctl -u etf-portfolio.service -f`
- Check CloudWatch logs (if enabled): `aws logs tail /aws/ec2/etf-portfolio/application --follow`
- Test backend health: `curl http://localhost:8000/health` (on EC2)
- Test via CloudFront: `curl https://[CLOUDFRONT_DOMAIN]/api/v1/health`

---

**Deployment Complete!** 🎉
