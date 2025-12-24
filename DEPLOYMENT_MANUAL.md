# AWS Manual Deployment Guide: ETF Portfolio Tracker (Console UI)

This guide provides step-by-step instructions for deploying the ETF Portfolio Tracker application to AWS using the **AWS Management Console** (web interface) instead of the AWS CLI. The architecture and cost remain identical to the CLI deployment guide.

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
- [Appendix A: Console vs CLI](#appendix-a-console-vs-cli)
- [Appendix B: Finding Resource Information](#appendix-b-finding-resource-information)

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
   - Sign up at https://aws.amazon.com if you don't have one
   - Verify email and complete setup
   - Add payment method

2. **AWS Console Access**
   - Log in to https://console.aws.amazon.com
   - Ensure you have permissions to create EC2, S3, CloudFront, IAM resources

3. **Important Security Note**
   - Consider creating an IAM user with appropriate permissions instead of using root account
   - Enable MFA (Multi-Factor Authentication) for security

### Local Development Environment
- **Node.js** 18+ and npm (for frontend build)
  - Download from https://nodejs.org
  - Verify: `node --version` and `npm --version`
- **Git** (for code deployment)
  - Download from https://git-scm.com
- **SSH client**
  - Built-in on macOS/Linux
  - Windows: Use PuTTY or Windows Terminal with OpenSSH
- **Text editor** for creating configuration files locally

### Repository Access
- Application code available locally at:
  - Backend: `backend/`
  - Frontend: `frontend/`

### Important Notes
- **Keep a notepad ready** to save important values (IPs, IDs, domain names) as you create resources
- **Bookmark AWS Console URLs** you'll use frequently (EC2, S3, CloudFront)
- **Allow 2-3 hours** for first-time deployment (including CloudFront propagation)

---

## Phase 1: AWS Infrastructure Setup

### Step 1.1: Create S3 Bucket for Frontend

#### Navigate to S3 Service

1. Log in to AWS Console: https://console.aws.amazon.com
2. In the top search bar, type **"S3"** and click on **"S3"** service
   - Alternatively: Click **"Services"** menu → **"Storage"** → **"S3"**

#### Create Bucket

1. Click the **"Create bucket"** button (orange button on the right)

2. **General configuration:**
   - **Bucket name**: Enter a unique name (e.g., `etf-portfolio-frontend-20251223`)
     - Must be globally unique across all AWS accounts
     - Use lowercase, numbers, and hyphens only
     - Suggestion: Add a timestamp or random number for uniqueness
   - **AWS Region**: Select your preferred region (e.g., `us-east-1`)
     - Choose a region close to your users
     - **Note this region** for later steps

3. **Object Ownership:**
   - Keep default: **"ACLs disabled (recommended)"**

4. **Block Public Access settings:**
   - **Enable ALL four checkboxes** (should be checked by default):
     - ☑ Block all public access
     - ☑ Block public access to buckets and objects granted through new access control lists (ACLs)
     - ☑ Block public access to buckets and objects granted through any access control lists (ACLs)
     - ☑ Block public access to buckets and objects granted through new public bucket or access point policies
     - ☑ Block public and cross-account access to buckets and objects through any public bucket or access point policies
   - **Why**: CloudFront will access via OAI (Origin Access Identity), not public access

5. **Bucket Versioning:**
   - Select **"Enable"** under Bucket Versioning
   - **Why**: Allows rollback if you upload incorrect files

6. **Default encryption:**
   - Keep default: **"Server-side encryption with Amazon S3 managed keys (SSE-S3)"**

7. **Advanced settings:**
   - Keep all defaults

8. Click **"Create bucket"** button at the bottom

#### Verify Bucket Creation

- You should see a green success banner: **"Successfully created bucket 'your-bucket-name'"**
- Your bucket should appear in the list of S3 buckets
- **Write down your bucket name** for later steps

---

### Step 1.2: Launch EC2 Instance

#### Navigate to EC2 Service

1. In the AWS Console top search bar, type **"EC2"**
2. Click on **"EC2"** (Virtual Servers in the Cloud)
3. You'll land on the EC2 Dashboard

#### Create Key Pair for SSH Access

Before launching an instance, create a key pair for secure SSH access:

1. In the left sidebar, scroll down to **"Network & Security"** section
2. Click **"Key Pairs"**
3. Click **"Create key pair"** button (top right)
4. Configure key pair:
   - **Name**: `etf-portfolio-backend-key`
   - **Key pair type**: Select **"RSA"**
   - **Private key file format**:
     - macOS/Linux: Select **".pem"**
     - Windows (PuTTY): Select **".ppk"**
5. Click **"Create key pair"** button
6. **File downloads automatically** - Save it to a secure location
   - **macOS/Linux**: Save to `~/.ssh/etf-portfolio-backend-key.pem`
   - **Windows**: Save to `C:\Users\YourName\.ssh\etf-portfolio-backend-key.ppk`
7. **Set permissions** (macOS/Linux only):
   ```bash
   chmod 400 ~/.ssh/etf-portfolio-backend-key.pem
   ```

#### Create Security Group

1. In the EC2 left sidebar, under **"Network & Security"**, click **"Security Groups"**
2. Click **"Create security group"** button (top right)
3. Configure security group:
   - **Security group name**: `etf-portfolio-backend-sg`
   - **Description**: `Security group for ETF Portfolio backend`
   - **VPC**: Keep default VPC selected

4. **Inbound rules** - Add two rules:

   **Rule 1 - SSH Access:**
   - Click **"Add rule"** button
   - **Type**: Select **"SSH"** from dropdown (auto-fills port 22)
   - **Source**: Select **"My IP"** from dropdown
     - This automatically detects and adds your current public IP
     - **Important**: If your IP changes, you'll need to update this rule

   **Rule 2 - Backend API (Temporary - will restrict later):**
   - Click **"Add rule"** button again
   - **Type**: Select **"Custom TCP"**
   - **Port range**: Enter `8000`
   - **Source**: Select **"Anywhere-IPv4"** (`0.0.0.0/0`)
     - **Note**: This is temporary for testing; we'll restrict to CloudFront IPs in Phase 5

5. **Outbound rules:**
   - Keep default (allows all outbound traffic)

6. Click **"Create security group"** button at the bottom

7. **Write down the Security Group ID** (e.g., `sg-0123456789abcdef0`)
   - You'll see it in the success message and in the security groups list

#### Launch EC2 Instance

1. In the EC2 left sidebar, click **"Instances"** (under "Instances" section)
2. Click **"Launch instances"** button (top right, orange button)

**Step 1: Name and tags**
- **Name**: Enter `etf-portfolio-backend`
- Tags are automatically created from the name

**Step 2: Application and OS Images (Amazon Machine Image)**
- Click on **"Browse more AMIs"** link
- In the search bar, type: `ubuntu 24.04`
- Select **"Ubuntu Server 24.04 LTS (HVM), SSD Volume Type"**
  - Architecture: **64-bit (x86)**
  - Look for the official Ubuntu AMI (owner: 099720109477)
  - Click **"Select"** button

**Step 3: Instance type**
- Select **"t3.micro"** from the list
  - 2 vCPU, 1 GiB Memory
  - **Cost**: ~$7.50/month
  - Alternative: **t4g.micro** (ARM-based, 20% cheaper) - requires different AMI

**Step 4: Key pair**
- Select **"etf-portfolio-backend-key"** from dropdown
  - This is the key pair you created earlier

**Step 5: Network settings**
- Click **"Edit"** button on the right
- **VPC**: Keep default VPC
- **Subnet**: Select any subnet (or "No preference")
- **Auto-assign public IP**: Select **"Enable"**
  - **Important**: This gives your instance a public IP address
- **Firewall (security groups)**: Select **"Select existing security group"**
- **Common security groups**: Select **"etf-portfolio-backend-sg"**
  - This is the security group you created earlier

**Step 6: Configure storage**
- **Root volume**:
  - Size: Change from default (8 GiB) to **20 GiB**
  - Volume type: Select **"gp3"** (General Purpose SSD)
  - Delete on termination: Keep checked
  - Encrypted: Keep default (not encrypted)

**Step 7: Advanced details**
- **Keep all defaults** (no changes needed)

**Step 8: Summary**
- Review your configuration on the right sidebar
- **Number of instances**: 1
- Click **"Launch instance"** button (orange button at bottom)

#### Verify Instance Launch

- You'll see a success message: **"Successfully initiated launch of instance"**
- Click on the **instance ID** link (e.g., `i-0123456789abcdef0`)
- You'll be taken to the instance details page
- **Instance state** will show:
  - First: **"Pending"** (yellow) - Wait 1-2 minutes
  - Then: **"Running"** (green) - Instance is ready!

#### Get Instance Information

Once instance is **"Running"**, note these values:

1. **Instance ID**: e.g., `i-0123456789abcdef0` (top of details page)
2. **Public IPv4 address**: e.g., `54.123.45.67` (in details tab)
3. **Public IPv4 DNS**: e.g., `ec2-54-123-45-67.compute-1.amazonaws.com`

**Write down** these values - you'll need them for SSH access and CloudFront configuration.

---

### Step 1.3: Allocate Elastic IP (Optional but Recommended)

**Why Elastic IP?**
- Regular public IPs change when you stop/start your instance
- Elastic IPs remain the same, preventing DNS/configuration issues
- **Cost**: Free while associated with a running instance; $0.005/hour if unassociated

#### Allocate Elastic IP

1. In EC2 left sidebar, under **"Network & Security"**, click **"Elastic IPs"**
2. Click **"Allocate Elastic IP address"** button (top right)
3. **Settings:**
   - **Network Border Group**: Keep default (your region)
   - **Public IPv4 address pool**: Select **"Amazon's pool of IPv4 addresses"**
   - **Tags** (optional): Add tag `Name` = `etf-portfolio-backend-eip`
4. Click **"Allocate"** button
5. **Success message** shows the allocated IP (e.g., `54.234.56.78`)
6. **Write down the Elastic IP address**

#### Associate Elastic IP with Instance

1. You should see your new Elastic IP in the list
2. Select the checkbox next to the Elastic IP
3. Click **"Actions"** dropdown (top right) → **"Associate Elastic IP address"**
4. **Configure association:**
   - **Resource type**: Select **"Instance"**
   - **Instance**: Select **"etf-portfolio-backend"** from dropdown
     - You'll see the instance ID: `i-0123456789abcdef0 (etf-portfolio-backend)`
   - **Private IP address**: Keep default (auto-selected)
   - **Reassociation**: Keep checked (if enabled)
5. Click **"Associate"** button
6. **Success message**: "Successfully associated Elastic IP address with instance"

#### Verify Association

1. Go back to **EC2 Dashboard** → **"Instances"**
2. Click on your **"etf-portfolio-backend"** instance
3. In the details tab, verify:
   - **Public IPv4 address** now shows your Elastic IP
   - **Elastic IP addresses** field shows the associated EIP

**From now on**, use the **Elastic IP** for all SSH connections and CloudFront configuration (not the original public IP).

---

### Step 1.4: Create CloudFront Origin Access Identity (OAI)

**What is OAI?**
- Allows CloudFront to access your private S3 bucket
- S3 bucket remains private, no public access needed
- More secure than making bucket public

#### Navigate to CloudFront

1. In AWS Console top search bar, type **"CloudFront"**
2. Click on **"CloudFront"** (Content delivery network service)

#### Create Origin Access Identity

1. In the left sidebar, scroll down and click **"Origin access identities"** (under "Security" section)
   - **Note**: In newer AWS console versions, this might be under **"Origin access"** → **"Origin access identities (legacy)"**
2. Click **"Create origin access identity"** button (or **"Create"** button)
3. **Configure OAI:**
   - **Name**: Enter `etf-portfolio-s3-oai`
   - **Comment** (optional): Enter `OAI for ETF Portfolio S3 frontend bucket`
4. Click **"Create"** button
5. **Success message**: "Successfully created origin access identity"

#### Get OAI Information

- You'll see your new OAI in the list
- **Write down these values:**
  - **ID**: e.g., `E2ABCDEFGHIJK`
  - **Amazon S3 Canonical User ID**: Long string starting with letters/numbers
    - Click on the OAI row to see full details
    - Copy the **"S3 Canonical User ID"** value

**Keep this tab open** - you'll need the OAI when creating the CloudFront distribution later.

---

## Phase 2: Backend Deployment (EC2)

From this point, you'll SSH into your EC2 instance to configure the backend. These commands run **ON the EC2 instance**, not on your local machine.

### Step 2.1: Connect to EC2 Instance

#### Option A: EC2 Instance Connect (Browser-based SSH)

**Easiest method** - No SSH client needed:

1. Go to **EC2 Dashboard** → **"Instances"**
2. Select your **"etf-portfolio-backend"** instance (checkbox)
3. Click **"Connect"** button (top right)
4. On the **"Connect to instance"** page, select **"EC2 Instance Connect"** tab
5. **Username**: Keep default (`ubuntu`)
6. Click **"Connect"** button
7. A new browser tab opens with a terminal connected to your instance

**Pros**: No setup, works from any computer
**Cons**: Connection timeout after 10 minutes of inactivity, no file transfer support

#### Option B: SSH from Local Terminal (Recommended)

**macOS/Linux:**
```bash
# Open Terminal
# Navigate to where you saved the key pair
cd ~/.ssh

# Connect to EC2 instance (replace with your Elastic IP)
ssh -i etf-portfolio-backend-key.pem ubuntu@YOUR_ELASTIC_IP

# Example:
ssh -i etf-portfolio-backend-key.pem ubuntu@54.234.56.78
```

**Windows (PowerShell with OpenSSH):**
```powershell
# Open PowerShell
# Navigate to key location
cd C:\Users\YourName\.ssh

# Connect to EC2 instance
ssh -i etf-portfolio-backend-key.pem ubuntu@YOUR_ELASTIC_IP
```

**Windows (PuTTY):**
1. Open PuTTY
2. **Session:**
   - Host Name: `ubuntu@YOUR_ELASTIC_IP`
   - Port: `22`
   - Connection type: SSH
3. **Connection** → **SSH** → **Auth** → **Credentials:**
   - Private key file: Browse to your `.ppk` file
4. Click **"Open"**

**First connection warning:**
- You'll see: "The authenticity of host... can't be established"
- Type `yes` and press Enter to continue

**Successful connection:**
- You'll see Ubuntu welcome message and command prompt: `ubuntu@ip-172-31-x-x:~$`

---

### Step 2.2: Update System and Install Dependencies

Now you're connected to the EC2 instance. Run these commands in the EC2 terminal:

```bash
# Update package lists
sudo apt update && sudo apt upgrade -y

# This will take 2-3 minutes
# Press Enter if prompted about any service restarts (default options)

# Verify Python 3.12 is installed (Ubuntu 24.04 includes it)
python3 --version
# Expected output: Python 3.12.x

# Install build dependencies
sudo apt install -y build-essential libssl-dev libffi-dev git curl python3-pip

# Install sqlite3 CLI (for database management)
sudo apt install -y sqlite3

# Verify installations
git --version
sqlite3 --version
```

**Expected output:**
```
git version 2.43.x
3.45.x 2024-01-xx...
```

---

### Step 2.3: Install UV Package Manager

UV is a fast Python package manager written in Rust (replacement for pip/poetry):

```bash
# Install UV (installer automatically sets up PATH)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add UV to PATH for current session
# Note: Newer installer uses ~/.local/bin, older uses ~/.cargo/bin
export PATH="$HOME/.local/bin:$PATH"

# Verify PATH was added to ~/.bashrc (installer should do this automatically)
tail -2 ~/.bashrc

# Reload bashrc
source ~/.bashrc

# Verify installation
uv --version
# Expected: uv 0.x.x (e.g., uv 0.5.0)

# Verify UV location
which uv
# Expected: /home/ubuntu/.local/bin/uv
```

---

### Step 2.4: Deploy Application Code

#### Create Application Directory

```bash
# Create directory for application
sudo mkdir -p /opt/etf-portfolio

# Change ownership to ubuntu user
sudo chown ubuntu:ubuntu /opt/etf-portfolio

# Navigate to directory
cd /opt/etf-portfolio
```

#### Option A: Deploy via Git Clone (Recommended for Production)

If your code is in a Git repository (GitHub, GitLab, etc.):

```bash
# Clone repository (replace with your repository URL)
git clone https://github.com/YOUR_USERNAME/finance_track_webapp.git .

# Note the dot (.) at the end - clones into current directory

# If using private repository, you'll need to authenticate:
# - Use HTTPS with personal access token
# - Or configure SSH keys

# Verify files
ls -la
# Should see: backend/, frontend/, README.md, etc.
```

#### Option B: Deploy via File Transfer

If deploying from local machine without Git:

**On your LOCAL machine** (not EC2):

**macOS/Linux - Using rsync:**
```bash
# Navigate to your project directory
cd /path/to/finance_track_webapp

# Transfer backend files
rsync -avz --exclude='node_modules' \
           --exclude='.venv' \
           --exclude='__pycache__' \
           --exclude='*.pyc' \
           --exclude='.git' \
           --exclude='portfolio.db' \
           -e "ssh -i ~/.ssh/etf-portfolio-backend-key.pem" \
           backend/ ubuntu@YOUR_ELASTIC_IP:/opt/etf-portfolio/backend/

# Verify upload
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@YOUR_ELASTIC_IP "ls -la /opt/etf-portfolio/backend"
```

**Windows - Using WinSCP:**
1. Download WinSCP: https://winscp.net
2. Configure connection:
   - File protocol: SFTP
   - Host: Your Elastic IP
   - Port: 22
   - Username: ubuntu
   - Advanced → SSH → Authentication → Private key: Select your `.ppk` file
3. Connect and transfer `backend/` folder to `/opt/etf-portfolio/backend/`

**Verify files are uploaded** (back on EC2 terminal):
```bash
ls -la /opt/etf-portfolio/backend
# Should see: app/, tests/, alembic/, pyproject.toml, etc.
```

---

### Step 2.5: Configure Backend Environment

```bash
# Navigate to backend directory
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

# Verify file created
cat .env

# Note: We'll update CORS_ORIGINS with actual CloudFront domain later in Phase 4
```

**Important Configuration Notes:**
- `DATABASE_URL`: Absolute path to SQLite database file
- `DEBUG=False`: Production mode (no debug output)
- `CORS_ORIGINS`: Will be updated after CloudFront distribution is created
- `LOG_LEVEL=INFO`: Production logging (change to `DEBUG` for troubleshooting)
- `LOG_FORMAT=json`: Structured logging for CloudWatch

---

### Step 2.6: Install Dependencies and Setup Database

```bash
# Ensure you're in backend directory
cd /opt/etf-portfolio/backend

# Install all dependencies (including dev tools)
uv sync --all-extras

# This will take 2-3 minutes
# Creates .venv/ directory with all Python packages

# Verify virtual environment created
ls -la .venv/
# Should see: bin/, lib/, pyvenv.cfg

# Run database migrations
uv run alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
# INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
# INFO  [alembic.runtime.migration] Running upgrade  -> abc123, initial schema

# Verify database file created
ls -lh portfolio.db
# Should show: -rw-r--r-- 1 ubuntu ubuntu 20K [date] portfolio.db

# Set proper permissions
chmod 644 portfolio.db
```

**If migrations fail:**
- Check `.env` file for correct `DATABASE_URL`
- Ensure `/opt/etf-portfolio/backend/` directory is writable
- Check logs: `uv run alembic history` to see migration status

---

### Step 2.7: Create Systemd Service for Auto-Start

Systemd will manage the backend process, automatically restarting it if it crashes:

_You might be tempted to run the backend with a simple background process_:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

**This approach has critical problems:**

❌ **No auto-restart**: If Python crashes, your backend stays down forever
❌ **No boot persistence**: Reboot EC2 and your backend doesn't start
❌ **Session dependency**: Process may die when SSH disconnects (unless using nohup)
❌ **No log management**: stdout/stderr output is lost
❌ **Hard to monitor**: No easy way to check if service is healthy
❌ **CI/CD incompatible**: GitHub Actions expects systemd service for deployments

**Systemd provides:**

✅ **Automatic restart** on crashes (RestartSec=10)
✅ **Boot persistence** - starts automatically after reboot
✅ **Session independent** - survives SSH disconnects
✅ **Centralized logging** - view logs with `journalctl`
✅ **Easy management** - start/stop/status commands
✅ **Health monitoring** - systemd tracks process state
✅ **Production ready** - industry standard for service management

**Bottom line**: Background processes (`&`) are for temporary testing only. Systemd is **required** for reliable production deployments.

```bash
# Create systemd service file
sudo tee /etc/systemd/system/etf-portfolio.service > /dev/null << 'EOF'
[Unit]
Description=ETF Portfolio Tracker Backend API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/etf-portfolio/backend
ExecStart=/home/ubuntu/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=etf-portfolio

[Install]
WantedBy=multi-user.target
EOF
```

**Important Note on UV Path:**

The UV path may vary depending on which installer version you used:
- **Newer UV installer**: `/home/ubuntu/.local/bin/uv` (used in this guide)

If you encounter `status=203/EXEC` errors, verify your UV location:
```bash
# Check UV location
which uv

# Update paths in service file if different:
# - Environment="PATH=..." line
# - ExecStart=... line
```

**Continue with service setup:**

```bash
# Verify file created
sudo cat /etc/systemd/system/etf-portfolio.service

# Reload systemd daemon to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable etf-portfolio.service

# Start the service now
sudo systemctl start etf-portfolio.service

# Check service status
sudo systemctl status etf-portfolio.service
```

**Expected output:**
```
● etf-portfolio.service - ETF Portfolio Tracker Backend API
     Loaded: loaded (/etc/systemd/system/etf-portfolio.service; enabled)
     Active: active (running) since [timestamp]
   Main PID: 1234 (python3)
      Tasks: 9 (limit: 1131)
     Memory: 120.0M
     CGroup: /system.slice/etf-portfolio.service
```

Look for **"Active: active (running)"** in green - this means it's working!

**If status shows "failed"**:
```bash
# View detailed error logs
sudo journalctl -u etf-portfolio.service -n 50 --no-pager

# Common issues:
# - Path errors: Check paths in .env and service file
# - Permission errors: Ensure ubuntu user owns /opt/etf-portfolio
# - Port conflict: Check if port 8000 is in use
```

---

### Step 2.8: Verify Backend Health

Test that the backend API is working:

```bash
# Test health endpoint locally on EC2
curl http://localhost:8000/health

# Expected output:
# {"status":"healthy"}

# Test API endpoint
curl http://localhost:8000/api/v1/analytics/portfolio-summary

# Expected output (empty portfolio):
# {"holdings":[],"total_invested":"0.00","total_fees":"0.00"}

# View live logs (press Ctrl+C to stop)
sudo journalctl -u etf-portfolio.service -f
```

**Test from your LOCAL machine:**

Open a browser or terminal on your computer and access:
```
http://YOUR_ELASTIC_IP:8000/health
```

**Example**: `http://54.234.56.78:8000/health`

**Expected**: `{"status":"healthy"}`

**If this fails:**
- Check security group allows port 8000 from 0.0.0.0/0
- Ensure service is running: `sudo systemctl status etf-portfolio.service`
- Check EC2 instance has public IP/Elastic IP assigned

---

### Step 2.9: Managing the Backend Service

Once the systemd service is configured, use these commands to manage it:

#### Check Service Status

```bash
# View service status
sudo systemctl status etf-portfolio.service

# Expected output for running service:
# ● etf-portfolio.service - ETF Portfolio Tracker Backend API
#      Loaded: loaded (/etc/systemd/system/etf-portfolio.service; enabled)
#      Active: active (running) since [timestamp]
```

#### Start Service

```bash
# Start the service
sudo systemctl start etf-portfolio.service

# Verify it started
sudo systemctl status etf-portfolio.service
```

#### Stop Service

```bash
# Stop the service
sudo systemctl stop etf-portfolio.service

# Verify it stopped
sudo systemctl status etf-portfolio.service
# Should show: Active: inactive (dead)
```

#### Restart Service

```bash
# Restart the service (stop then start)
sudo systemctl restart etf-portfolio.service

# Or reload configuration without fully stopping
sudo systemctl reload etf-portfolio.service
```

#### View Logs

```bash
# View last 50 log lines
sudo journalctl -u etf-portfolio.service -n 50

# Follow logs in real-time (like tail -f)
sudo journalctl -u etf-portfolio.service -f

# View logs from today
sudo journalctl -u etf-portfolio.service --since today

# View logs with timestamps
sudo journalctl -u etf-portfolio.service -n 50 --no-pager
```

#### Enable/Disable Auto-Start on Boot

```bash
# Enable service to start on boot (should already be enabled)
sudo systemctl enable etf-portfolio.service

# Disable auto-start on boot
sudo systemctl disable etf-portfolio.service

# Check if enabled
sudo systemctl is-enabled etf-portfolio.service
# Output: enabled
```

#### Common Service Management Scenarios

**After updating code via git pull:**
```bash
cd /opt/etf-portfolio/backend
git pull origin main
sudo systemctl restart etf-portfolio.service
```

**After changing .env configuration:**
```bash
nano /opt/etf-portfolio/backend/.env
# Make changes, save
sudo systemctl restart etf-portfolio.service
```

**If service fails to start, check logs:**
```bash
sudo systemctl status etf-portfolio.service
sudo journalctl -u etf-portfolio.service -n 100 --no-pager
```

**Test if backend is responding:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy"}
```

---

## Phase 3: Frontend Deployment (S3)

These steps run on your **LOCAL machine** (not on EC2).

### Step 3.1: Build Frontend for Production

```bash
# Open terminal on your local machine
# Navigate to your project directory
cd /path/to/finance_track_webapp/frontend

# Verify production environment file exists
cat .env.production
# Should contain: VITE_API_URL=/api/v1

# Install dependencies (if not already installed)
npm install

# This takes 1-2 minutes

# Build for production
npm run build

# This takes 30-60 seconds
# Creates optimized production bundle

# Verify build output
ls -lh dist/
# Should see:
# - index.html
# - assets/ directory with hashed JS/CSS files
# - vite.svg (favicon)
```

**Build Output Structure:**
```
dist/
├── index.html                    # Main HTML (5-10 KB)
├── assets/
│   ├── index-a1b2c3d4.js        # Main JS bundle (200-500 KB)
│   ├── index-e5f6g7h8.css       # Main CSS bundle (20-50 KB)
│   └── [other hashed assets]    # Images, fonts, etc.
└── vite.svg                      # Favicon
```

**If build fails:**
- Check Node.js version: `node --version` (should be 18+)
- Clear cache and retry: `rm -rf node_modules package-lock.json && npm install && npm run build`
- Check for errors in frontend code (TypeScript/ESLint issues)

---

### Step 3.2: Upload Frontend to S3 via Console

#### Navigate to S3 Bucket

1. Log in to AWS Console: https://console.aws.amazon.com
2. Navigate to **S3** service (search bar or Services menu)
3. Click on your bucket name: **"etf-portfolio-frontend-XXXXXXXX"**

#### Upload Files

**Method 1: Drag and Drop (Easiest)**

1. In your file explorer/finder, open the `frontend/dist/` folder
2. Select **ALL files and folders** inside `dist/`:
   - `index.html`
   - `assets/` folder
   - `vite.svg`
   - Any other files
3. **Drag and drop** them into the S3 bucket browser window
4. You'll see the **"Upload"** page with your files listed
5. **Important**: Ensure files are at the **root level** of the bucket, not inside a `dist/` folder
   - ✅ Correct: `s3://bucket-name/index.html`
   - ❌ Wrong: `s3://bucket-name/dist/index.html`

**Method 2: Upload Button**

1. Click **"Upload"** button (orange button)
2. Click **"Add files"** button
3. Select all files in `frontend/dist/` directory
   - Hold Ctrl (Windows) or Cmd (Mac) to select multiple files
4. Click **"Add folder"** button
5. Select the `assets/` folder
6. All files should appear in the upload list



## Phase 4: CloudFront Configuration

Now we'll create a CloudFront distribution with two origins (S3 + EC2).

### Step 4.1: Create CloudFront Distribution

#### Navigate to CloudFront

1. AWS Console → Search for **"CloudFront"** → Click **"CloudFront"**
2. Click **"Create distribution"** button (or "Create a CloudFront distribution")

---

#### Origin Settings

**Origin 1: S3 Bucket (Frontend)**

1. **Origin domain:**
   - Click in the field - dropdown shows your S3 buckets
   - Select your bucket: `etf-portfolio-frontend-XXXXXXXX.s3.amazonaws.com`
   - **Important**: Select the one ending in `.s3.amazonaws.com`, NOT the website endpoint

- standard configs just pick s3 bucket and keep all the same 

**Check that the correct policy is in S3**
S3 → Your bucket → Permissions → Bucket policy
the policy should be like this (edit placeholders):
```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontServicePrincipalReadOnly",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::YOUR_ACCOUNT_ID:distribution/YOUR_DISTRIBUTION_ID"
        }
      }
    }
  ]
}
```
---

#### Default Cache Behavior (for S3 Origin)

This applies to all paths **except** `/api/*` (which we'll configure separately).

1. **Path pattern**: `Default (*)` (auto-filled, don't change)

2. **Compress objects automatically**: Select **"Yes"**
   - Enables gzip compression for faster loading

3. **Viewer protocol policy**: Select **"Redirect HTTP to HTTPS"**
   - Forces HTTPS for all visitors

4. **Allowed HTTP methods**: Select **"GET, HEAD"** (default)
   - Frontend only needs read access

5. **Restrict viewer access**: Select **"No"** (public access)

6. **Cache key and origin requests:**
   - Select **"Cache policy and origin request policy (recommended)"**
   - **Cache policy**: Select **"CachingOptimized"** from dropdown
   - **Origin request policy**: Select **"None"**

7. **Response headers policy**: Select **"None"** (or choose CORS policy if needed)

8. Keep all other defaults

---

#### Settings

1. **Price class**: Select **"Use all edge locations (best performance)"**
   - Or choose cheaper option: **"Use only North America and Europe"**

2. **AWS WAF web ACL**: Select **"Do not enable security protections"** (for now)
   - Optional: Enable later for DDoS protection

3. **Alternate domain name (CNAME)**: Leave empty
   - For custom domain, you'd add it here (e.g., `app.yourdomain.com`)

4. **Custom SSL certificate**: Keep **"Default CloudFront SSL certificate"**
   - Free SSL for `*.cloudfront.net` domain

5. **Supported HTTP versions**: Select **"HTTP/2"** (default)

6. **Default root object**: Enter `index.html`
   - Serves `index.html` when accessing root URL

7. **Standard logging**: Keep **"Off"** (or enable to S3 for access logs)

8. **IPv6**: Keep **"On"** (recommended)

9. **Description** (optional): Enter `ETF Portfolio Tracker - Frontend + Backend`

---

#### Custom Error Responses (Important for React Router)

**Before creating the distribution**, scroll down to find **"Custom error responses"** section or plan to add these after creation.

We need to add error responses for React Router to work (single-page app routing):

**After clicking "Create distribution", immediately:**

1. Go to your new distribution
2. Click on **"Error pages"** tab
3. Click **"Create custom error response"** button

**Error Response 1:**
- **HTTP error code**: `403: Forbidden`
- **Customize error response**: Select **"Yes"**
- **Response page path**: `/index.html`
- **HTTP response code**: `200: OK`
- **Error caching minimum TTL**: `300` (5 minutes)
- Click **"Create custom error response"**

**Error Response 2:**
- Click **"Create custom error response"** again
- **HTTP error code**: `404: Not Found`
- **Customize error response**: Select **"Yes"**
- **Response page path**: `/index.html`
- **HTTP response code**: `200: OK`
- **Error caching minimum TTL**: `300` (5 minutes)
- Click **"Create custom error response"**

**Why**: When users refresh on `/transactions` or other React Router paths, S3 returns 404 (file doesn't exist). This redirects to `index.html`, which loads React and handles routing client-side.

---

#### Create Distribution

1. **Review all settings** in the summary on the right
2. Click **"Create distribution"** button at the bottom

**Distribution creation starts:**
- **Status**: "In Progress" (yellow)
- **State**: "Enabled"
- **Takes 15-30 minutes** to deploy globally

#### Get CloudFront Domain

1. You'll be redirected to the distribution details page
2. **Domain name** is shown at the top (e.g., `d1a2b3c4d5e6f7.cloudfront.net`)
3. **Write down this domain** - you'll need it for:
   - Accessing your app
   - Updating backend CORS settings
   - Adding the second origin (EC2)

**Your app will be accessible at**: `https://d1a2b3c4d5e6f7.cloudfront.net`

---

### Step 4.2: Add Second Origin (EC2 Backend)

Now add the EC2 backend as a second origin.

#### Add Origin

1. On your distribution details page, click **"Origins"** tab
2. Click **"Create origin"** button

**Origin settings:**

1. **Origin domain**: Enter your **EC2 Public DNS** (not IP)
   - Format: `ec2-54-123-45-67.compute-1.amazonaws.com`
   - Find it: Go to EC2 → Instances → Your instance → Public IPv4 DNS
   - **Do NOT** select from dropdown (it won't show EC2 instances)

2. **Protocol**: Select **"HTTP only"**
   - CloudFront terminates HTTPS, EC2 serves HTTP on port 8000

3. **HTTP port**: Enter `8000`

4. **HTTPS port**: Leave as `443` (not used)

5. **Minimum origin SSL protocol**: Select **"TLSv1.2"** (doesn't apply, but select anyway)

6. **Origin path**: Leave empty

7. **Name**: Auto-filled as EC2 DNS
   - Optional: Change to `EC2-Backend` for clarity

8. **Add custom header** (optional): Skip for now

9. **Origin Shield**: Keep **"No"** (not needed for single user)

10. **Additional settings**: Keep defaults

11. Click **"Create origin"** button

**Verify:**
- **Origins** tab now shows **2 origins**:
  - S3 bucket (Frontend)
  - EC2 DNS (Backend)

---

### Step 4.3: Add Behavior for API Routes

Create a cache behavior to route `/api/*` requests to EC2 backend.

#### Create Behavior

1. On distribution details page, click **"Behaviors"** tab
2. You should see 1 behavior: "Default (*)" pointing to S3
3. Click **"Create behavior"** button

**Behavior settings:**

1. **Path pattern**: Enter `/api/*`
   - This matches all API requests (e.g., `/api/v1/transactions`)

2. **Origin and origin groups**: Select **EC2-Backend** from dropdown
   - Or select the EC2 DNS if you didn't rename it

3. **Viewer protocol policy**: Select **"Redirect HTTP to HTTPS"**

4. **Allowed HTTP methods**: Select **"GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE"**
   - API needs all methods for CRUD operations

5. **Restrict viewer access**: Select **"No"**

6. **Cache key and origin requests:**
   - Select **"Legacy cache settings"**
   - **Headers**: Select **"Include the following headers"**
     - Add headers: `Authorization`, `Content-Type`, `Accept`, `Origin`
     - Click **"Add header"** for each one
   - **Query strings**: Select **"All"**
   - **Cookies**: Select **"All"**

7. **Object caching:**
   - **Origin Cache Headers**: Keep selected
   - Or select **"Customize"** and set:
     - **Minimum TTL**: `0`
     - **Maximum TTL**: `0`
     - **Default TTL**: `0`
   - **Why**: Don't cache API responses (always fetch fresh data)

8. **Compress objects automatically**: Select **"No"**
   - API returns JSON, compression handled by backend

9. Keep all other defaults

10. Click **"Create behavior"** button

#### Verify Behavior Order

1. **Behaviors** tab should now show **2 behaviors**:
   - **Precedence 0**: `/api/*` → EC2-Backend
   - **Precedence 1** (Default): `*` → S3-Frontend

2. **Order matters**: CloudFront matches patterns in order
   - `/api/*` is checked first
   - Everything else falls through to default (S3)

**If order is wrong:**
- Select a behavior → **"Actions"** → **"Move up/down"**
- Ensure `/api/*` has precedence 0 (checked first)

---

### Step 4.4: Wait for Distribution Deployment

#### Check Deployment Status

1. Go to **CloudFront** → **Distributions**
2. Find your distribution in the list
3. **Status** column shows:
   - **"Deploying"** (yellow) - In progress
   - **"Deployed"** (green) - Ready to use

**Deployment time**: 15-30 minutes

**Monitor progress:**
- Refresh the page every 5 minutes
- **Last modified** timestamp updates as changes propagate

#### Test CloudFront Distribution

Once status is **"Deployed"**, test your application:

**Test frontend:**
```
https://YOUR_CLOUDFRONT_DOMAIN
```
Example: `https://d1a2b3c4d5e6f7.cloudfront.net`

**Expected:**
- React app loads (Investment Dashboard page)
- No console errors in browser DevTools

**Test backend API:**
```
https://YOUR_CLOUDFRONT_DOMAIN/api/v1/health
```

**Expected**: `{"status":"healthy"}`

**If frontend works but API fails:**
- Check backend is running on EC2: `sudo systemctl status etf-portfolio.service`
- Verify EC2 security group allows port 8000
- Check CloudFront behavior for `/api/*` points to EC2 origin
- Wait longer (behavior changes take 5-10 minutes to propagate)

---

### Step 4.5: Update Backend CORS Configuration

Now that CloudFront is deployed, update the backend to accept requests from the CloudFront domain.

#### SSH to EC2 Instance

```bash
# From your local machine
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@YOUR_ELASTIC_IP
```

#### Update .env File

```bash
# Navigate to backend directory
cd /opt/etf-portfolio/backend

# Edit .env file
nano .env

# Find this line:
# CORS_ORIGINS=["https://CLOUDFRONT_DOMAIN_PLACEHOLDER"]

# Replace with your actual CloudFront domain:
# CORS_ORIGINS=["https://d1a2b3c4d5e6f7.cloudfront.net"]

# Press Ctrl+X, then Y, then Enter to save

# Verify changes
cat .env | grep CORS_ORIGINS
# Should show: CORS_ORIGINS=["https://d1a2b3c4d5e6f7.cloudfront.net"]
```

**Alternative: Use sed command**
```bash
sed -i 's|CLOUDFRONT_DOMAIN_PLACEHOLDER|d1a2b3c4d5e6f7.cloudfront.net|g' .env
```

#### Restart Backend Service

```bash
# Restart service to apply new configuration
sudo systemctl restart etf-portfolio.service

# Check status (should be "active (running)")
sudo systemctl status etf-portfolio.service

# Check logs for CORS configuration
sudo journalctl -u etf-portfolio.service -n 20
# Should show: "CORS origins: ['https://d1a2b3c4d5e6f7.cloudfront.net']"
```

#### Verify CORS

Open your application in browser:
```
https://YOUR_CLOUDFRONT_DOMAIN
```

1. Open browser DevTools (F12)
2. Go to **Console** tab
3. Refresh page
4. **Check for errors**:
   - ❌ No CORS errors should appear
   - ✅ API requests should complete successfully

**If CORS errors persist:**
- Verify .env has correct CloudFront domain (with `https://`, no trailing slash)
- Check backend service restarted successfully
- Clear browser cache and reload
- Wait 1-2 minutes for service to fully restart

---

## Phase 5: Security Hardening

Now that everything works, restrict access for security.

### Step 5.1: Restrict EC2 Security Group to CloudFront Only

Currently, your EC2 backend is accessible from anywhere (0.0.0.0/0). Let's restrict it to only CloudFront.

#### Navigate to Security Groups

1. AWS Console → **EC2** → **Security Groups** (left sidebar)
2. Find **"etf-portfolio-backend-sg"** in the list
3. Click on it to open details

#### Remove Open Port 8000 Rule

1. Click on **"Inbound rules"** tab
2. Find the rule:
   - **Type**: Custom TCP
   - **Port**: 8000
   - **Source**: 0.0.0.0/0
3. Select the checkbox next to this rule
4. Click **"Delete inbound rules"** button (top right)
5. Confirm deletion
6. **Success message**: "Successfully deleted inbound rules"

#### Add CloudFront Prefix List Rule

CloudFront provides a managed prefix list of IP ranges.

1. Still on **"Inbound rules"** tab
2. Click **"Edit inbound rules"** button
3. Click **"Add rule"** button
4. Configure new rule:
   - **Type**: Select **"Custom TCP"**
   - **Port range**: Enter `8000`
   - **Source**: Click in the field
     - Start typing: `CloudFront`
     - Select **"com.amazonaws.global.cloudfront.origin-facing"**
     - This is a managed prefix list maintained by AWS
5. **Description** (optional): Enter `Allow CloudFront to backend`
6. Click **"Save rules"** button

**Verify:**
- **Inbound rules** now shows:
  - Rule 1: SSH (port 22) from Your IP
  - Rule 2: Custom TCP (port 8000) from CloudFront prefix list

---

### Step 5.2: Test Security Configuration

#### Test Direct EC2 Access (Should Fail)

From your **local machine**, try to access the backend directly:

```bash
# Try to access EC2 backend directly (should timeout or refuse)
curl http://YOUR_ELASTIC_IP:8000/health

# Expected: Timeout or connection refused
# This is GOOD - direct access is blocked
```

#### Test CloudFront Access (Should Work)

```bash
# Access via CloudFront (should work)
curl https://YOUR_CLOUDFRONT_DOMAIN/api/v1/health

# Expected: {"status":"healthy"}
# This is GOOD - CloudFront can still reach backend
```

#### Test Frontend Application

Open browser and go to: `https://YOUR_CLOUDFRONT_DOMAIN`

1. **Dashboard loads**: ✅
2. **No console errors**: ✅
3. **API requests work**: Try adding a transaction or viewing analytics

**If API requests fail after security hardening:**
- **Issue**: CloudFront can't reach EC2 backend
- **Solution**:
  - Verify CloudFront prefix list is correct in security group
  - Check EC2 backend is running: `sudo systemctl status etf-portfolio.service`
  - CloudFront behavior for `/api/*` points to EC2 origin
  - Wait 5 minutes for security group changes to propagate

---

### Step 5.3: Verify Security Configuration Checklist

- [ ] **Backend `.env` file**:
  - `DEBUG=False`
  - `CORS_ORIGINS` includes only CloudFront domain (HTTPS)

- [ ] **EC2 Security Group**:
  - Port 22 (SSH) restricted to your IP only
  - Port 8000 restricted to CloudFront prefix list only
  - No 0.0.0.0/0 rules for port 8000

- [ ] **S3 Bucket**:
  - All public access blocked
  - Bucket policy allows only CloudFront OAI access
  - Versioning enabled (for rollback)

- [ ] **CloudFront**:
  - Forces HTTPS (redirect HTTP to HTTPS)
  - Custom error responses configured (403/404 → index.html)
  - Two origins: S3 (frontend) + EC2 (backend)
  - Behavior for `/api/*` routes to EC2

- [ ] **Direct EC2 Access**:
  - `curl http://EC2_IP:8000/health` should **fail** (timeout/refused)
  - This proves backend is not publicly accessible

- [ ] **CloudFront Access**:
  - `curl https://CLOUDFRONT_DOMAIN/api/v1/health` should **succeed**
  - This proves CloudFront → EC2 connection works

---

## Phase 6: Database Backup Strategy

Automated backups ensure you don't lose data. We'll create daily SQLite backups.

### Step 6.1: Create Backup Script on EC2

SSH to your EC2 instance:

```bash
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@YOUR_ELASTIC_IP
```

#### Create Backup Directory

```bash
# Create backup directory
sudo mkdir -p /opt/etf-portfolio/backups

# Set ownership to ubuntu user
sudo chown ubuntu:ubuntu /opt/etf-portfolio/backups
```

#### Create Backup Script

```bash
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

# Set ownership
sudo chown ubuntu:ubuntu /opt/etf-portfolio/backup-db.sh
```

#### Test Backup Script

```bash
# Run backup manually
/opt/etf-portfolio/backup-db.sh

# Expected output:
# [timestamp]: Backup completed - portfolio_20251223_143000.db.gz
# [timestamp]: Old backups cleaned up (retention: 7 days)

# Verify backup created
ls -lh /opt/etf-portfolio/backups/

# Should show:
# -rw-r--r-- 1 ubuntu ubuntu 5.2K [date] portfolio_20251223_143000.db.gz
```

---

### Step 6.2: Schedule Daily Backups with Cron

#### Edit Crontab

```bash
# Open crontab editor
crontab -e

# First time: Select editor
# Choose option 1 (nano) if prompted
```

#### Add Backup Job

Add this line at the end of the file:

```cron
# Daily database backup at 2:00 AM UTC
0 2 * * * /opt/etf-portfolio/backup-db.sh >> /var/log/db-backup.log 2>&1
```

**Explanation:**
- `0 2 * * *`: Run at 2:00 AM every day (UTC time)
- `/opt/etf-portfolio/backup-db.sh`: Script to run
- `>> /var/log/db-backup.log 2>&1`: Log output to file

**Save and exit:**
- Press `Ctrl+X`
- Press `Y` to confirm
- Press `Enter` to save

#### Verify Cron Job

```bash
# View active cron jobs
crontab -l

# Should show:
# 0 2 * * * /opt/etf-portfolio/backup-db.sh >> /var/log/db-backup.log 2>&1
```

#### Check Backup Logs (After First Run)

```bash
# View backup logs
cat /var/log/db-backup.log

# Or tail for live updates
tail -f /var/log/db-backup.log
```

---

### Step 6.3: Restore from Backup (When Needed)

If you need to restore the database from a backup:

#### Stop Backend Service

```bash
# Stop the service
sudo systemctl stop etf-portfolio.service
```

#### Restore Database

```bash
# Navigate to backend directory
cd /opt/etf-portfolio/backend

# Backup current database (just in case)
cp portfolio.db portfolio.db.before-restore

# List available backups
ls -lh /opt/etf-portfolio/backups/

# Restore from specific backup (replace date with your backup)
gunzip -c /opt/etf-portfolio/backups/portfolio_20251223_020000.db.gz > portfolio.db

# Verify restore
ls -lh portfolio.db
sqlite3 portfolio.db "PRAGMA integrity_check;"
# Should return: ok
```

#### Restart Backend Service

```bash
# Restart service
sudo systemctl start etf-portfolio.service

# Verify service started
sudo systemctl status etf-portfolio.service

# Test health endpoint
curl http://localhost:8000/health

# Test API
curl http://localhost:8000/api/v1/analytics/portfolio-summary
```

---

### Step 6.4: Optional: Upload Backups to S3

For extra safety, store backups in S3 (off-instance storage).

#### Create S3 Backup Bucket (AWS Console)

1. Navigate to **S3** → **Create bucket**
2. **Bucket name**: `etf-portfolio-backups-XXXXXXXX`
3. **Region**: Same as your application
4. **Block Public Access**: Enable all (keep private)
5. **Versioning**: Enable
6. **Encryption**: Enable (SSE-S3)
7. Click **"Create bucket"**

#### Configure Lifecycle Policy

To automatically delete old backups:

1. Go to your backup bucket
2. Click **"Management"** tab
3. Click **"Create lifecycle rule"**
4. **Rule configuration:**
   - **Rule name**: `delete-old-backups`
   - **Choose rule scope**: Apply to all objects
5. **Lifecycle rule actions**:
   - ☑ **Expire current versions of objects**
   - **Days after object creation**: `30`
6. Click **"Create rule"**

**Result**: Backups older than 30 days are automatically deleted.

#### Update Backup Script to Upload to S3

Edit backup script on EC2:

```bash
nano /opt/etf-portfolio/backup-db.sh
```

Add this line **before the cleanup section** (before `find` command):

```bash
# Upload to S3 (requires AWS CLI configured)
aws s3 cp $BACKUP_DIR/portfolio_$DATE.db.gz s3://YOUR_BACKUP_BUCKET_NAME/ --only-show-errors
```

**Save and exit** (Ctrl+X, Y, Enter)

**Note**: This requires AWS CLI to be installed and configured with credentials. See CLI deployment guide for setup.

---

## Phase 7: Monitoring & Maintenance

### Step 7.1: Set Up Billing Alerts (AWS Console)

Prevent unexpected charges by setting up billing alerts.

#### Enable Billing Alerts

1. AWS Console → Click on your **account name** (top right) → **Account**
2. Scroll down to **"Preferences"** section
3. Find **"Alert Preferences"**
4. Click **"Edit"**
5. ☑ Enable **"Receive Billing Alerts"**
6. Click **"Update"**

#### Create SNS Topic for Alerts

1. Navigate to **SNS (Simple Notification Service)**
2. In left sidebar, click **"Topics"**
3. Click **"Create topic"**
4. **Type**: Select **"Standard"**
5. **Name**: Enter `etf-portfolio-billing-alerts`
6. **Display name** (optional): Enter `ETF Portfolio Billing`
7. Keep other defaults
8. Click **"Create topic"**
9. **Copy the Topic ARN** (e.g., `arn:aws:sns:us-east-1:123456789012:etf-portfolio-billing-alerts`)

#### Subscribe to Topic

1. You'll be on the topic details page
2. Click **"Create subscription"** button
3. **Protocol**: Select **"Email"**
4. **Endpoint**: Enter your email address
5. Click **"Create subscription"**
6. **Check your email** for confirmation
7. Click the **"Confirm subscription"** link in the email

#### Create CloudWatch Billing Alarm

1. Navigate to **CloudWatch** service
2. In left sidebar, click **"Alarms"** → **"All alarms"**
3. Click **"Create alarm"** button
4. Click **"Select metric"**
5. Click **"Billing"** → **"Total Estimated Charge"**
6. Select the checkbox for **"EstimatedCharges"** (currency: USD)
7. Click **"Select metric"**
8. **Metric and conditions:**
   - **Statistic**: Maximum
   - **Period**: 6 hours
   - **Threshold type**: Static
   - **Whenever EstimatedCharges is...**: Greater than
   - **Threshold value**: Enter `20` (dollars)
9. Click **"Next"**
10. **Configure actions:**
    - **Alarm state trigger**: In alarm
    - **Send notification to**: Select your SNS topic (`etf-portfolio-billing-alerts`)
11. Click **"Next"**
12. **Alarm name**: Enter `etf-portfolio-billing-alert-20`
13. **Description**: Enter `Alert when monthly bill exceeds $20`
14. Click **"Next"**
15. **Review and create** → Click **"Create alarm"**

**Result**: You'll receive an email if your monthly AWS bill exceeds $20.

---

### Step 7.2: Create Health Check Script (EC2)

Automatically restart backend if it crashes.

SSH to EC2 instance:

```bash
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@YOUR_ELASTIC_IP
```

#### Create Health Check Script

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

# Make executable
sudo chmod +x /opt/etf-portfolio/health-check.sh

# Set ownership
sudo chown ubuntu:ubuntu /opt/etf-portfolio/health-check.sh
```

#### Test Health Check

```bash
# Run manually
/opt/etf-portfolio/health-check.sh

# Expected output:
# [2025-12-23 14:30:00] Health check PASSED (HTTP 200)
```

#### Schedule Health Check (Every 5 Minutes)

```bash
# Edit crontab
crontab -e

# Add line:
*/5 * * * * /opt/etf-portfolio/health-check.sh >> /var/log/health-check.log 2>&1

# Save and exit (Ctrl+X, Y, Enter)

# Verify
crontab -l
```

#### View Health Check Logs

```bash
# View last 20 health checks
tail -20 /var/log/health-check.log

# Or follow live
tail -f /var/log/health-check.log
```

---

### Step 7.3: Application Update Procedures

#### Update Backend (EC2)

SSH to EC2:

```bash
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@YOUR_ELASTIC_IP

# Navigate to application directory
cd /opt/etf-portfolio/backend

# Pull latest code (if using Git)
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

#### Update Frontend (Local Machine)

**On your LOCAL machine:**

```bash
# Navigate to frontend directory
cd /path/to/finance_track_webapp/frontend

# Pull latest code
git pull origin main

# Install new dependencies (if any)
npm install

# Build for production
npm run build

# Verify build
ls -lh dist/
```

**Upload to S3** (choose one method):

**Method A: AWS CLI (Recommended)**

```bash
# Upload all files except index.html
aws s3 sync dist/ s3://YOUR_BUCKET_NAME/ \
  --delete \
  --cache-control "public, max-age=31536000, immutable" \
  --exclude "index.html"

# Upload index.html separately
aws s3 cp dist/index.html s3://YOUR_BUCKET_NAME/index.html \
  --cache-control "public, max-age=300, must-revalidate"

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

**Method B: AWS Console**

1. Go to **S3** → Your bucket
2. Delete old files in `assets/` folder (or select all and delete)
3. Upload new files from `dist/` folder (drag and drop)
4. Ensure correct cache headers are set (see Phase 3)

**Invalidate CloudFront Cache** (Console):

1. Go to **CloudFront** → Your distribution
2. Click **"Invalidations"** tab
3. Click **"Create invalidation"**
4. **Object paths**: Enter `/*` (invalidate all)
5. Click **"Create invalidation"**
6. Wait 1-2 minutes for completion

**Verify update:**
```
https://YOUR_CLOUDFRONT_DOMAIN
```
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Should see new changes

---

## Troubleshooting

### Backend Issues

#### Service Not Starting

**Check service status:**

```bash
# SSH to EC2
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@YOUR_ELASTIC_IP

# Check status
sudo systemctl status etf-portfolio.service

# View detailed logs
sudo journalctl -u etf-portfolio.service -n 100 --no-pager
```

**Common issues:**

1. **Port 8000 already in use:**
   ```bash
   # Check what's using port 8000
   sudo lsof -i :8000

   # Kill process if needed
   sudo kill -9 <PID>
   ```

2. **Environment variable errors:**
   ```bash
   # Check .env file
   cat /opt/etf-portfolio/backend/.env

   # Ensure DATABASE_URL, CORS_ORIGINS are correct
   ```

3. **Permission errors:**
   ```bash
   # Fix ownership
   sudo chown -R ubuntu:ubuntu /opt/etf-portfolio
   ```

4. **Missing dependencies:**
   ```bash
   cd /opt/etf-portfolio/backend
   uv sync --all-extras
   ```

5. **UV command not found (status=203/EXEC):**

   **Symptom**: Service status shows:
   ```
   Active: activating (auto-restart) (Result: exit-code)
   Main PID: XXXX (code=exited, status=203/EXEC)
   ```

   **Cause**: Systemd cannot find or execute the UV command (wrong path)

   **Solution**:
   ```bash
   # Find where UV is actually installed
   which uv
   # Output shows actual path (e.g., /home/ubuntu/.local/bin/uv)

   # Common locations:
   # - /home/ubuntu/.local/bin/uv (newer UV installer)
   # - /home/ubuntu/.cargo/bin/uv (older UV installer)

   # Update systemd service with correct path
   sudo nano /etc/systemd/system/etf-portfolio.service

   # Change these two lines to match your UV location:
   # Environment="PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin"
   # ExecStart=/home/ubuntu/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

   # Save and exit (Ctrl+X, Y, Enter)

   # Reload and restart
   sudo systemctl daemon-reload
   sudo systemctl start etf-portfolio.service
   sudo systemctl status etf-portfolio.service
   ```

   **Test command manually first**:
   ```bash
   cd /opt/etf-portfolio/backend
   /home/ubuntu/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
   # If this works, systemd should work after path fix
   # Press Ctrl+C to stop
   ```

#### Database Issues

```bash
# Check database exists
ls -lh /opt/etf-portfolio/backend/portfolio.db

# Check database integrity
sqlite3 /opt/etf-portfolio/backend/portfolio.db "PRAGMA integrity_check;"
# Should return: ok

# Check current migration
cd /opt/etf-portfolio/backend
uv run alembic current

# Apply migrations if needed
uv run alembic upgrade head
```

#### CORS Errors

**Symptoms**: Browser console shows CORS errors

**Solution:**

```bash
# SSH to EC2
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@YOUR_ELASTIC_IP

# Check CORS_ORIGINS
cat /opt/etf-portfolio/backend/.env | grep CORS_ORIGINS
# Should be: CORS_ORIGINS=["https://YOUR_CLOUDFRONT_DOMAIN"]

# If incorrect, edit
nano /opt/etf-portfolio/backend/.env
# Update CORS_ORIGINS with correct CloudFront domain
# Save: Ctrl+X, Y, Enter

# Restart service
sudo systemctl restart etf-portfolio.service
```

---

### Frontend Issues

#### 404 Errors on React Router Paths

**Problem**: Refreshing on `/transactions` returns 404

**Solution**: Verify CloudFront custom error responses

1. Go to **CloudFront** → Your distribution → **"Error pages"** tab
2. Should have two rules:
   - **403** → `/index.html` (200)
   - **404** → `/index.html` (200)
3. If missing, add them (see Phase 4, Step 4.1)
4. Wait 5-10 minutes for changes to propagate

#### API Requests Failing

**Check CloudFront behavior:**

1. **CloudFront** → Your distribution → **"Behaviors"** tab
2. Should have behavior:
   - **Path pattern**: `/api/*`
   - **Origin**: EC2 backend
3. Click on behavior → **"Edit"**
4. Verify:
   - **Allowed HTTP methods**: All methods (GET, POST, PUT, DELETE, etc.)
   - **Cache settings**: TTL all set to 0 (no caching)
   - **Headers**: Forward `Authorization`, `Content-Type`, `Accept`, `Origin`

**Check EC2 security group:**

1. **EC2** → **Security Groups** → `etf-portfolio-backend-sg`
2. **Inbound rules** should have:
   - Port 8000 from **CloudFront prefix list**

**Test backend directly from EC2:**

```bash
# SSH to EC2
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@YOUR_ELASTIC_IP

# Test locally
curl http://localhost:8000/api/v1/health
# Should return: {"status":"healthy"}
```

#### Stale Cache After Update

**Solution**: Invalidate CloudFront cache

1. **CloudFront** → Your distribution → **"Invalidations"** tab
2. Click **"Create invalidation"**
3. **Object paths**: Enter `/*` (all files)
4. Click **"Create invalidation"**
5. Wait 1-2 minutes for completion
6. Hard refresh browser: Ctrl+Shift+R

---

### Performance Issues

#### High CPU on EC2

**Check CPU usage:**

```bash
# SSH to EC2
ssh -i ~/.ssh/etf-portfolio-backend-key.pem ubuntu@YOUR_ELASTIC_IP

# View live CPU usage
top
# Press 'q' to quit

# View Uvicorn processes
ps aux | grep uvicorn
```

**Solution**: Reduce Uvicorn workers

```bash
# Edit systemd service
sudo nano /etc/systemd/system/etf-portfolio.service

# Find line: --workers 4
# Change to: --workers 2

# Save: Ctrl+X, Y, Enter

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart etf-portfolio.service
```

#### Database Lock Issues (SQLite)

**Symptoms**: API requests timeout or fail intermittently

**Solution**: Verify WAL mode is enabled

```bash
# Check journal mode
sqlite3 /opt/etf-portfolio/backend/portfolio.db "PRAGMA journal_mode;"
# Should return: wal

# If not, enable WAL mode
sqlite3 /opt/etf-portfolio/backend/portfolio.db "PRAGMA journal_mode=WAL;"
```

---

## Deployment Checklists

### Pre-Deployment Checklist

**Infrastructure:**
- [ ] S3 bucket created with versioning enabled
- [ ] EC2 instance launched (t3.micro, Ubuntu 24.04)
- [ ] Security group configured (SSH + port 8000)
- [ ] Elastic IP allocated and associated (optional)
- [ ] CloudFront OAI created

**Backend:**
- [ ] SSH connection to EC2 successful
- [ ] Python 3.12 and UV installed
- [ ] Application code deployed to `/opt/etf-portfolio`
- [ ] Production `.env` file created
- [ ] Dependencies installed (`uv sync --all-extras`)
- [ ] Database migrations applied (`uv run alembic upgrade head`)
- [ ] Systemd service created and enabled
- [ ] Service running (`systemctl status etf-portfolio.service`)

**Frontend:**
- [ ] Node.js and npm installed locally
- [ ] Frontend built (`npm run build`)
- [ ] Build output verified (`dist/` directory exists)

**CloudFront:**
- [ ] CloudFront distribution created
- [ ] Two origins configured (S3 + EC2)
- [ ] Behavior for `/api/*` routes to EC2
- [ ] Custom error responses configured (403/404 → index.html)
- [ ] Distribution deployed (status: Deployed)

---

### Post-Deployment Verification Checklist

**Application Access:**
- [ ] Frontend loads: `https://YOUR_CLOUDFRONT_DOMAIN`
- [ ] No console errors in browser DevTools
- [ ] Navigation works (Dashboard, Transactions, etc.)
- [ ] API requests work (try creating a transaction)

**Backend:**
- [ ] Health endpoint accessible: `https://YOUR_CLOUDFRONT_DOMAIN/api/v1/health`
- [ ] Backend logs show no errors: `sudo journalctl -u etf-portfolio.service`
- [ ] Database file exists and has data
- [ ] Service auto-starts on boot: `systemctl is-enabled etf-portfolio.service`

**Security:**
- [ ] Backend CORS_ORIGINS includes CloudFront domain
- [ ] EC2 security group restricts port 8000 to CloudFront only
- [ ] Direct EC2 access blocked: `curl http://EC2_IP:8000/health` times out
- [ ] S3 bucket blocks public access
- [ ] DEBUG=False in backend `.env`

**Reliability:**
- [ ] Database backups scheduled (cron job exists)
- [ ] Health check script configured
- [ ] Billing alerts set up

---

## Appendix A: Console vs CLI

### Key Differences

| Task | Console (Manual) | CLI (Automated) |
|------|-----------------|----------------|
| **Learning Curve** | Easier for beginners | Requires command-line knowledge |
| **Speed** | Slower (lots of clicking) | Faster (scriptable) |
| **Automation** | Not repeatable | Can be scripted |
| **Verification** | Visual confirmation at each step | Need to verify programmatically |
| **Bulk Operations** | Tedious (e.g., setting cache headers) | Efficient (one command) |
| **Error Recovery** | Manual cleanup | Can script rollback |

### When to Use Each

**Use Console when:**
- First time deploying (learning architecture)
- One-time setup or changes
- Visual verification is important
- You're not comfortable with command line

**Use CLI when:**
- Deploying multiple environments
- Automating deployments (CI/CD)
- Bulk operations (uploading many files)
- You need repeatable, scriptable deployments

### Hybrid Approach (Recommended)

- **Console**: Create infrastructure (S3, EC2, CloudFront)
- **CLI**: Deploy updates (frontend builds, backend code)
- **Scripts**: Automate recurring tasks (backups, health checks)

---

## Appendix B: Finding Resource Information

### How to Find IDs and ARNs in Console

#### S3 Bucket Name
1. **S3** → **Buckets** → Find your bucket in list
2. Bucket name is in the **"Name"** column

#### EC2 Instance ID
1. **EC2** → **Instances**
2. Find your instance: **"etf-portfolio-backend"**
3. **Instance ID** is in the list (e.g., `i-0123456789abcdef0`)

#### EC2 Public IP / Elastic IP
1. **EC2** → **Instances** → Click on your instance
2. **Details** tab → **"Public IPv4 address"** or **"Elastic IP addresses"**

#### EC2 Public DNS
1. **EC2** → **Instances** → Click on your instance
2. **Details** tab → **"Public IPv4 DNS"**

#### Security Group ID
1. **EC2** → **Security Groups**
2. Find **"etf-portfolio-backend-sg"**
3. **Security group ID** is in the list (e.g., `sg-0123456789abcdef0`)

#### CloudFront Distribution ID
1. **CloudFront** → **Distributions**
2. Find your distribution in list
3. **ID** column shows distribution ID (e.g., `E1A2B3C4D5E6F7`)

#### CloudFront Domain Name
1. **CloudFront** → **Distributions**
2. Find your distribution
3. **Domain name** column (e.g., `d1a2b3c4d5e6f7.cloudfront.net`)

#### CloudFront OAI ID
1. **CloudFront** → **Origin access identities** (left sidebar)
2. Find **"etf-portfolio-s3-oai"**
3. **ID** column (e.g., `E2ABCDEFGHIJK`)

---

## Summary

Congratulations! You have successfully deployed the ETF Portfolio Tracker application to AWS using the AWS Management Console!

**Your Application URLs:**
- **Frontend**: `https://YOUR_CLOUDFRONT_DOMAIN`
- **Backend API**: `https://YOUR_CLOUDFRONT_DOMAIN/api/v1`
- **API Docs**: `https://YOUR_CLOUDFRONT_DOMAIN/api/v1/docs`
- **Health Check**: `https://YOUR_CLOUDFRONT_DOMAIN/api/v1/health`

**Architecture Summary:**
- **Frontend**: S3 + CloudFront (global CDN with HTTPS)
- **Backend**: EC2 t3.micro (Ubuntu 24.04, Python 3.12, FastAPI)
- **Database**: SQLite with automated daily backups
- **Cost**: ~$10-15/month

**Security Measures:**
- CloudFront handles HTTPS encryption
- S3 bucket is private (CloudFront OAI access only)
- EC2 backend restricted to CloudFront IPs only
- SSH access restricted to your IP
- CORS configured for CloudFront domain only

**Reliability Features:**
- Systemd auto-restarts backend on crash
- Daily database backups (7-day retention)
- Health check with auto-recovery every 5 minutes
- Billing alerts to prevent unexpected charges

**Next Steps:**
1. Test all application features end-to-end
2. Configure custom domain (optional) - see Route 53 documentation
3. Set up CloudWatch Logs for centralized logging (optional)
4. Document your CloudFront domain for team access
5. Schedule regular maintenance and updates

**Support:**
- Backend documentation: `backend/README.md`
- Frontend documentation: `frontend/README.md`
- Development guide: `CLAUDE.md`
- CLI deployment guide: `DEPLOYMENT.md`

---

**Deployment Complete!**

Thank you for using this guide. Your application is now live and accessible globally via CloudFront's edge network!
