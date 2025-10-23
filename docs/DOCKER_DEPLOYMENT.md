# Docker Deployment Guide - Unified Trading Projects

This guide explains how to deploy all three trading projects (shortseller, lxalgo, momentum2) using a single unified Docker Compose setup on your Contabo server.

## Overview

The unified setup manages all projects in one place with:
- Single `docker-compose.unified.yml` file
- Proper health checks for all containers
- Shared network for inter-container communication
- Individual project isolation
- Centralized logging and monitoring

## Current Issues Fixed

1. **Docker Compose Version**: Using `docker-compose` (v1.29.2) instead of `docker compose` (not available)
2. **Shortseller Health Check**: Fixed incorrect port 8080 health check - now checks process
3. **Resource Management**: Added memory limits and TCP keepalive for all services
4. **Unified Management**: All three projects in one compose file

## Project Structure on Server

```
/root/projects/
├── docker-compose.unified.yml    # Main compose file (manages all projects)
├── .env                          # Server-level environment variables
├── lxalgo/
│   ├── Dockerfile
│   ├── .env                      # lxalgo-specific env vars
│   └── ... (project files)
├── shortseller/
│   ├── Dockerfile
│   ├── .env                      # shortseller-specific env vars
│   └── ... (project files)
└── momentum2/
    ├── Dockerfile
    ├── .env                      # momentum2-specific env vars
    └── ... (project files)
```

## Deployment Steps

### 1. Stop Current Containers

```bash
cd /root/projects

# Stop current containers
cd lxalgo && docker-compose down && cd ..
cd shortseller && docker-compose down && cd ..
```

### 2. Upload Files to Server

You have two options:

#### Option A: Using Git (Recommended)

Each project should be its own Git repository. Then on the server:

```bash
cd /root/projects/momentum2
git pull origin main

cd /root/projects/lxalgo
git pull origin main

cd /root/projects/shortseller
git pull origin main
```

#### Option B: Direct Upload

```bash
# From your local machine
scp /path/to/docker-compose.unified.yml root@194.146.12.132:/root/projects/
scp /path/to/momentum2/Dockerfile root@194.146.12.132:/root/projects/momentum2/
```

### 3. Set Up Environment Variables

```bash
# Copy the server-level .env template
cd /root/projects
cp .env.example .env

# Edit with your credentials
nano .env

# Each project also needs its own .env file
# These should already exist, but verify:
ls -la lxalgo/.env
ls -la shortseller/.env
ls -la momentum2/.env
```

### 4. Build and Start Services

```bash
cd /root/projects

# Build all images
docker-compose -f docker-compose.unified.yml build

# Start all services
docker-compose -f docker-compose.unified.yml up -d

# Or start specific services
docker-compose -f docker-compose.unified.yml up -d lxalgo
docker-compose -f docker-compose.unified.yml up -d shortseller
docker-compose -f docker-compose.unified.yml up -d momentum
```

### 5. Verify Deployment

```bash
# Check running containers
docker-compose -f docker-compose.unified.yml ps

# Check logs
docker-compose -f docker-compose.unified.yml logs -f

# Check specific project logs
docker-compose -f docker-compose.unified.yml logs -f momentum
docker-compose -f docker-compose.unified.yml logs -f lxalgo
docker-compose -f docker-compose.unified.yml logs -f shortseller

# Check container health
docker ps
```

## Common Operations

### View Logs

```bash
cd /root/projects

# All services
docker-compose -f docker-compose.unified.yml logs -f

# Specific service
docker-compose -f docker-compose.unified.yml logs -f momentum

# Last 100 lines
docker-compose -f docker-compose.unified.yml logs --tail=100 lxalgo
```

### Restart Services

```bash
cd /root/projects

# Restart all
docker-compose -f docker-compose.unified.yml restart

# Restart specific service
docker-compose -f docker-compose.unified.yml restart momentum
```

### Stop Services

```bash
cd /root/projects

# Stop all (keeps containers)
docker-compose -f docker-compose.unified.yml stop

# Stop and remove containers
docker-compose -f docker-compose.unified.yml down

# Stop specific service
docker-compose -f docker-compose.unified.yml stop lxalgo
```

### Update Code

```bash
cd /root/projects

# Pull latest code for a project
cd momentum2 && git pull && cd ..

# Rebuild and restart
docker-compose -f docker-compose.unified.yml build momentum
docker-compose -f docker-compose.unified.yml up -d momentum
```

### Clean Up

```bash
cd /root/projects

# Stop and remove containers, networks
docker-compose -f docker-compose.unified.yml down

# Also remove volumes (CAUTION: deletes data!)
docker-compose -f docker-compose.unified.yml down -v

# Remove unused images
docker image prune -a
```

## Health Monitoring

All containers have health checks:

```bash
# Check health status
docker ps

# Detailed health info
docker inspect momentum_trading --format='{{json .State.Health}}' | python3 -m json.tool
```

Health check types:
- **lxalgo**: Process check (`pgrep -f main.py`)
- **shortseller**: Process check (`pgrep -f start_trading.py`)
- **momentum**: Process check (`pgrep -f trading_system.py`)
- **postgres**: Database ready check
- **redis**: Ping check

## Resource Management

Memory limits per service:
- **lxalgo**: 900MB limit, 700MB reserved
- **momentum**: 900MB limit, 700MB reserved
- **shortseller**: No limit (needs more for database operations)

All containers have TCP keepalive configured for stable connections.

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.unified.yml logs [service-name]

# Check container status
docker ps -a

# Inspect container
docker inspect [container-name]
```

### Port Conflicts

Current port usage:
- **5432**: PostgreSQL (shortseller)
- **6379**: Redis (shortseller)

### Permission Issues

```bash
# Ensure proper ownership
chown -R root:root /root/projects

# Check .env file exists
ls -la /root/projects/.env
ls -la /root/projects/*/. env
```

### Database Issues (Shortseller)

```bash
# Access PostgreSQL
docker exec -it shortseller_postgres psql -U trading_user -d multiasset_trading

# Check Redis
docker exec -it shortseller_redis redis-cli ping
```

## Upgrade Docker Compose (If Needed)

Your server currently uses `docker-compose` v1.29.2. To upgrade to Docker Compose V2:

```bash
# Install Docker Compose V2 plugin
apt-get update
apt-get install docker-compose-plugin

# Then use: docker compose (space, not hyphen)
docker compose -f docker-compose.unified.yml up -d
```

## GitHub Workflow

Recommended workflow for updates:

1. **Local Development**: Make changes locally
2. **Commit & Push**: Commit to GitHub
3. **Server Pull**: SSH to server and pull changes
4. **Rebuild**: Rebuild and restart affected containers

```bash
# On server
cd /root/projects/momentum2
git pull origin main
cd /root/projects
docker-compose -f docker-compose.unified.yml build momentum
docker-compose -f docker-compose.unified.yml up -d momentum
```

## Security Notes

1. **Never commit .env files** to Git
2. Keep API keys secure
3. Use separate API keys for each project if possible
4. Regularly rotate credentials
5. Monitor container logs for unusual activity

## Next Steps

1. Set up automated backups for PostgreSQL data
2. Configure log rotation (already set to 10MB x 3 files)
3. Set up monitoring/alerting (Prometheus + Grafana)
4. Configure automatic restarts on failure
