# Docker Setup - Quick Summary

## What Was Created

### 1. Files for Momentum Strategy (This Project)
- ✅ `Dockerfile` - Container definition for momentum trading bot
- ✅ `docker-compose.unified.yml` - Manages all 3 projects in one place
- ✅ `.env.server.example` - Template for server environment variables
- ✅ `DOCKER_DEPLOYMENT.md` - Complete deployment guide

### 2. Issues Identified and Fixed

#### Server Issues:
1. **Docker Compose Version Mismatch**:
   - Server uses old `docker-compose` (v1.29.2)
   - Must use `docker-compose` (hyphen) not `docker compose` (space)

2. **Shortseller Container "Unhealthy"**:
   - Health check expects web server on port 8080
   - But shortseller doesn't run a web server
   - **Fixed**: Changed to process check instead

3. **Separate Docker Compose Files**:
   - Each project has its own docker-compose.yml
   - Hard to manage all projects together
   - **Fixed**: Created unified docker-compose.yml

## Quick Start

### Option 1: Test Locally First

```bash
cd /home/william/STRATEGIES/momentum\ strat/momentum2

# Build momentum container
docker build -t momentum:test .

# Test run
docker run --rm --env-file .env momentum:test
```

### Option 2: Deploy to Server via Git

```bash
# 1. Initialize git repo if not already done
cd /home/william/STRATEGIES/momentum\ strat/momentum2
git init
git add .
git commit -m "Add Docker configuration"

# 2. Push to GitHub
git remote add origin https://github.com/yourusername/momentum2.git
git push -u origin main

# 3. On server, pull the changes
ssh root@194.146.12.132
cd /root/projects
git clone https://github.com/yourusername/momentum2.git
# OR if already cloned: cd momentum2 && git pull

# 4. Copy unified compose file to projects root
cp momentum2/docker-compose.unified.yml .

# 5. Set up environment
cp .env.server.example .env
nano .env  # Add your credentials

# 6. Build and start
docker-compose -f docker-compose.unified.yml build momentum
docker-compose -f docker-compose.unified.yml up -d momentum
```

## The Unified Setup Advantage

Instead of managing 3 separate docker-compose files:
```bash
# OLD WAY (Current)
cd /root/projects/lxalgo && docker-compose up -d && cd ..
cd /root/projects/shortseller && docker-compose up -d && cd ..
cd /root/projects/momentum2 && docker-compose up -d && cd ..
```

You manage everything from one place:
```bash
# NEW WAY (Unified)
cd /root/projects
docker-compose -f docker-compose.unified.yml up -d

# Or start individually
docker-compose -f docker-compose.unified.yml up -d lxalgo
docker-compose -f docker-compose.unified.yml up -d shortseller
docker-compose -f docker-compose.unified.yml up -d momentum
```

## What Needs to Be Done

### For Each Project Repository:

1. **Momentum2** (this one):
   - [x] Create Dockerfile
   - [ ] Push to GitHub
   - [ ] Pull on server

2. **LXAlgo**:
   - [x] Already has Dockerfile ✓
   - [ ] No changes needed (uses existing)

3. **Shortseller**:
   - [x] Already has Dockerfile ✓
   - [ ] Health check fixed in unified compose

### On Server:

1. [ ] Upload `docker-compose.unified.yml` to `/root/projects/`
2. [ ] Create `/root/projects/.env` with server credentials
3. [ ] Stop current containers
4. [ ] Start with unified compose file
5. [ ] Verify all containers are healthy

## Container Structure

```
/root/projects/
│
├── docker-compose.unified.yml ← ONE FILE RULES THEM ALL
├── .env ← Server-level env vars
│
├── lxalgo/
│   ├── Dockerfile
│   ├── .env
│   └── (no changes needed)
│
├── shortseller/
│   ├── Dockerfile
│   ├── .env
│   ├── docker-compose.yml ← Can keep but not used
│   └── (health check fixed in unified)
│
└── momentum2/
    ├── Dockerfile ← NEW
    ├── .env
    └── trading_system.py
```

## Benefits of This Setup

1. **Single Command Management**: Start/stop all projects with one command
2. **Shared Network**: All containers can communicate if needed
3. **Unified Logging**: View all logs from one place
4. **Resource Management**: Better control over memory/CPU
5. **Health Monitoring**: Consistent health checks across all projects
6. **Easier Updates**: Pull code, rebuild, restart - done

## Next Actions

Choose your workflow:

### A. Full Git Workflow (Recommended)
1. Push momentum2 Dockerfile to GitHub
2. SSH to server and pull changes
3. Copy unified compose file to `/root/projects/`
4. Set up .env file
5. Deploy with unified compose

### B. Direct Upload (Faster for Testing)
1. SCP files directly to server
2. Test individual containers
3. Switch to unified compose when ready

## Commands Cheat Sheet

```bash
# Server commands
ssh root@194.146.12.132

# Navigate to projects
cd /root/projects

# Build all
docker-compose -f docker-compose.unified.yml build

# Start all
docker-compose -f docker-compose.unified.yml up -d

# Check status
docker-compose -f docker-compose.unified.yml ps
docker ps

# View logs
docker-compose -f docker-compose.unified.yml logs -f momentum

# Restart one service
docker-compose -f docker-compose.unified.yml restart momentum

# Stop all
docker-compose -f docker-compose.unified.yml down
```
