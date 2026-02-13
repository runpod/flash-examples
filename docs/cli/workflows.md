# Flash CLI Workflows

Common development workflows with step-by-step guidance. Each workflow includes prerequisites, commands, expected output, and decision points.

## Table of Contents

1. [Local Development Workflow](#local-development-workflow)
2. [Build and Deploy Workflow](#build-and-deploy-workflow)
3. [Multi-Environment Management](#multi-environment-management)
4. [Testing Before Production](#testing-before-production)
5. [Cleanup and Maintenance](#cleanup-and-maintenance)
6. [Troubleshooting Deployments](#troubleshooting-deployments)

---

## Local Development Workflow

Rapidly iterate on your Flash application locally without deploying to Runpod.

### Goal

Develop and test new features locally with fast feedback loops before deploying to production.

### Prerequisites

- Flash project initialized (`flash init`)
- Dependencies installed
- Virtual environment activated

### Workflow Steps

#### 1. Create or Clone Project

**New project:**
```bash
flash init my-api
cd my-api
```

**Existing project:**
```bash
git clone https://github.com/yourorg/my-api.git
cd my-api
```

#### 2. Set Up Environment

```bash
# Create virtual environment (if needed)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .
```

**Validation:**
```bash
python --version  # Should show 3.10+
pip list | grep runpod-flash  # Should show runpod-flash
```

#### 3. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file
# Required: RUNPOD_API_KEY (for deployment)
# Optional: FLASH_HOST, FLASH_PORT (for development)
```

Example `.env`:
```bash
RUNPOD_API_KEY=your-key-here
FLASH_HOST=localhost
FLASH_PORT=8888
```

#### 4. Start Development Server

```bash
flash run
```

**Expected output:**
```
INFO: Started server process [12345]
INFO: Uvicorn running on http://localhost:8888 (Press CTRL+C to quit)
INFO: Application startup complete.
```

**Validation:** Visit http://localhost:8888/docs to see Swagger UI

#### 5. Make Code Changes

Edit your worker files (e.g., `gpu_worker.py`):

```python
@remote(resource_config=gpu_config)
async def process_request(input_data: dict) -> dict:
    """Updated function with new logic."""
    # Add new feature here
    result = perform_processing(input_data)
    return {"status": "success", "result": result}
```

**With hot reload enabled (default):**
- Save file
- Server automatically restarts
- Changes immediately available

#### 6. Test via Swagger UI

1. Open http://localhost:8888/docs
2. Find your endpoint (e.g., `POST /process`)
3. Click "Try it out"
4. Enter test data:
   ```json
   {
     "input_data": {"test": "value"}
   }
   ```
5. Click "Execute"
6. Review response

#### 7. Test via curl

```bash
curl -X POST http://localhost:8888/process \
  -H "Content-Type: application/json" \
  -d '{"input_data": {"test": "value"}}'
```

**Validation:** Response matches expected output

#### 8. Iterate

Repeat steps 5-7:
- Make changes
- Test immediately
- Fix issues
- Validate behavior

### Development Tips

**Use Multiple Terminals:**
```bash
# Terminal 1: Run server
flash run

# Terminal 2: Test with curl
curl http://localhost:8888/process ...

# Terminal 3: Monitor logs, edit code
tail -f logs/application.log
```

**Disable Hot Reload for Debugging:**
```bash
flash run --no-reload
# Easier to attach debugger
```

**Change Port if Conflict:**
```bash
flash run --port 9000
```

**Access from Network:**
```bash
flash run --host 0.0.0.0
# Access from mobile devices or other machines
```

### Common Issues

**Port in use:**
```bash
# Solution: Use different port
flash run --port 9000
```

**Import errors:**
```bash
# Solution: Install dependencies
pip install -e .
```

**Changes not reflecting:**
```bash
# Solution: Check hot reload is enabled
flash run  # --reload is default

# Or manually restart
# Ctrl+C to stop
flash run
```

### Next Step

Once feature is working locally, proceed to [Build and Deploy Workflow](#build-and-deploy-workflow).

---

## Build and Deploy Workflow

Package and deploy your application to Runpod production infrastructure.

### Goal

Deploy a tested application to Runpod with proper environment isolation and validation.

### Prerequisites

- Application tested locally (`flash run`)
- Runpod API key configured (`RUNPOD_API_KEY`)
- Environment created (or will create in workflow)

### Workflow Steps

#### 1. Verify Local Tests Pass

Before deploying, ensure everything works locally:

```bash
flash run
# Test all endpoints via http://localhost:8888/docs
# Ctrl+C when done
```

**Validation:** All features work as expected locally

#### 2. Create Deployment Environment

First deployment needs an environment:

```bash
# Check existing environments
flash env list

# Create if needed
flash env create production
```

**For multiple environments:**
```bash
flash env create dev
flash env create staging
flash env create production
```

#### 3. Review Dependencies

Check `pyproject.toml` for accuracy:

```toml
[project]
dependencies = [
    "runpod-flash>=1.0.0",
    "torch>=2.0.0",
    # ... your dependencies
]
```

**Remove unused dependencies** to reduce build size.

#### 4. Test Build Locally

Build without deploying to check for issues:

```bash
flash build
```

**Expected output:**
```
Building Flash application...
Installing dependencies... ✓
Generating manifest... ✓
Creating archive... ✓
Build complete: artifact.tar.gz (45.2 MB)
```

**Validation:**
- Build succeeds without errors
- Archive size < 500MB
- `.build/` directory created

**If build too large:**
```bash
# Check package sizes
du -sh .build/lib/* | sort -h | tail -10

# Exclude packages in base image
flash build --exclude torch,torchvision,torchaudio
```

#### 5. Deploy to Environment

Deploy to your target environment:

```bash
flash deploy --env production
```

**With size optimization:**
```bash
flash deploy --env production --exclude torch,torchvision,torchaudio
```

**Expected output:**
```
Building Flash application... ✓
Build complete: artifact.tar.gz (45.2 MB)

Deploying to environment: production
Uploading artifact... 100%
Creating endpoints...
  ✓ my-api-gpu: https://abcd1234-my-api-gpu.runpod.io
  ✓ my-api-mothership: https://efgh5678-my-api-mothership.runpod.io

Deployment successful!
```

**Copy endpoint URLs** for testing.

#### 6. Verify Deployment

Check environment status:

```bash
flash env get production
```

**Expected:** All endpoints show "Active" status

#### 7. Test Production Endpoints

Test each deployed endpoint:

**GPU worker endpoint:**
```bash
curl -X POST https://abcd1234-my-api-gpu.runpod.io/run \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "input_data": {"test": "production"}
    }
  }'
```

**Expected response:**
```json
{
  "id": "request-id",
  "status": "COMPLETED",
  "delayTime": 123,
  "executionTime": 456,
  "output": {
    "status": "success",
    "result": "..."
  }
}
```

**Mothership endpoint:**
```bash
curl -X POST https://efgh5678-my-api-mothership.runpod.io/your-route \
  -H "Content-Type: application/json" \
  -d '{"your": "data"}'
```

**Validation:** All endpoints respond correctly

#### 8. Monitor Deployment

**Check Runpod Console:**
1. Visit https://runpod.io/console/serverless
2. Find your endpoints
3. Check metrics:
   - Request rate
   - Error rate
   - Worker scaling
   - Response times

**Check logs:**
- Click endpoint in console
- View "Logs" tab
- Look for errors or warnings

#### 9. Update Deployment (If Needed)

To deploy code changes:

```bash
# Make changes to code
# Test locally
flash run

# Redeploy (same environment)
flash deploy --env production
```

Updates existing endpoints without downtime.

### Deployment Checklist

Before deploying to production:

- [ ] All features tested locally
- [ ] Dependencies in `pyproject.toml` are accurate
- [ ] Build size < 500MB (or optimized)
- [ ] API key configured
- [ ] Environment created
- [ ] Test endpoints documented
- [ ] Monitoring plan in place

### Common Issues

**Build too large:**
```bash
# Exclude packages from build
flash build --exclude torch,torchvision,torchaudio
# See troubleshooting guide for details
```

**Upload failed:**
```bash
# Check internet connection
# Retry deployment
flash deploy --env production
```

**Endpoint creation failed:**
```bash
# Check API key
echo $RUNPOD_API_KEY

# Check Runpod account status
# Visit https://runpod.io/console
```

### Next Step

For managing multiple environments, see [Multi-Environment Management](#multi-environment-management).

---

## Multi-Environment Management

Manage separate staging and production deployments with isolated configurations.

### Goal

Maintain multiple deployment environments (dev, staging, production) for safe testing and gradual rollout.

### Prerequisites

- Working Flash application
- Runpod API key configured
- Understanding of environment isolation

### Environment Strategy

**Recommended setup:**

| Environment | Purpose | Worker Config |
|-------------|---------|---------------|
| `dev` | Active development, frequent deploys | Min workers: 0, Max: 2 |
| `staging` | Pre-production testing, client demos | Min workers: 0, Max: 3 |
| `production` | Live production traffic | Min workers: 1, Max: 10 |

### Workflow Steps

#### 1. Create All Environments

```bash
# Development environment
flash env create dev

# Staging environment
flash env create staging

# Production environment
flash env create production
```

**Validation:**
```bash
flash env list
# Should show all three environments
```

#### 2. Deploy to Development

First deployment goes to dev:

```bash
flash deploy --env dev
```

**Test thoroughly in dev:**
```bash
# Get dev endpoint URL
flash env get dev

# Test endpoint
curl -X POST https://dev-endpoint-url/run ...
```

#### 3. Promote to Staging

Once dev is stable, deploy to staging:

```bash
# Same code, different environment
flash deploy --env staging
```

**Staging testing:**
- Perform full integration tests
- Run load tests
- Client acceptance testing
- Security review

```bash
# Monitor staging
flash env get staging

# Check logs in Runpod console
```

#### 4. Promote to Production

After staging validation:

```bash
flash deploy --env production
```

**Production deployment checks:**
- [ ] Staging tests passed
- [ ] Load testing complete
- [ ] Client approval received
- [ ] Rollback plan ready

#### 5. Monitor All Environments

```bash
# View all environments
flash env list

# Check specific environment
flash env get production
flash env get staging
flash env get dev
```

**Monitor in Runpod Console:**
- Request rates
- Error rates
- Scaling behavior
- Cost tracking

#### 6. Manage Environment Lifecycle

**Update existing environment:**
```bash
# Make code changes
# Test locally
# Deploy to dev first
flash deploy --env dev

# Then staging
flash deploy --env staging

# Finally production
flash deploy --env production
```

**Rollback if needed:**
```bash
# Undeploy problematic deployment
flash undeploy production-endpoint-name

# Redeploy previous version
git checkout previous-tag
flash deploy --env production
```

### Environment Configuration Differences

**Customize per environment:**

**dev environment** (`dev_worker.py`):
```python
dev_gpu_config = LiveServerless(
    name="myapi_dev_gpu",
    gpus=[GpuGroup.ANY],  # Any GPU is fine
    workersMin=0,         # Scale to zero when idle
    workersMax=2,         # Small max for cost
    idleTimeout=60,       # Quick shutdown
)
```

**production environment** (`prod_worker.py`):
```python
prod_gpu_config = LiveServerless(
    name="myapi_prod_gpu",
    gpus=[GpuGroup.A100],  # Specific GPU for consistency
    workersMin=1,          # Always have one ready
    workersMax=10,         # Handle load spikes
    idleTimeout=300,       # Keep warm longer
)
```

**Use environment variables:**
```python
import os

env = os.getenv("ENVIRONMENT", "dev")

if env == "production":
    workers_min = 1
    workers_max = 10
else:
    workers_min = 0
    workers_max = 2
```

### Cost Management

**Development (lowest cost):**
```bash
# Scale to zero when not in use
# Use cheaper GPUs
flash deploy --env dev
```

**Staging (moderate cost):**
```bash
# Active during business hours
# Similar to production but smaller scale
```

**Production (optimized cost):**
```bash
# Right-sized for actual traffic
# Monitor and adjust worker limits
```

**View costs:**
1. Runpod Console → Billing
2. Filter by environment
3. Adjust worker configs if too expensive

### Environment Isolation Benefits

- **Safety:** Production unaffected by dev/staging issues
- **Testing:** Validate changes before production
- **Rollback:** Easy to revert production separately
- **Cost:** Dev/staging can use cheaper resources
- **Experimentation:** Try new features in dev first

### Common Patterns

**Feature Branch Workflow:**
```bash
# Create feature environment
flash env create feature-auth-v2

# Deploy feature branch
git checkout feature/auth-v2
flash deploy --env feature-auth-v2

# Test feature independently
# When approved, merge and deploy to staging
```

**Blue-Green Deployment:**
```bash
# Deploy to production-blue
flash deploy --env production-blue

# Test production-blue
# Switch traffic (via load balancer)
# Keep production-green as fallback
```

**Canary Deployment:**
```bash
# Deploy to production-canary (10% traffic)
flash deploy --env production-canary

# Monitor metrics
# If successful, deploy to production-main
flash deploy --env production-main
```

### Common Issues

**Wrong environment deployed:**
```bash
# Accidentally deployed to production
# Rollback:
flash undeploy production-endpoint --force
git checkout previous-version
flash deploy --env production
```

**Environment confusion:**
```bash
# Always specify environment explicitly
flash deploy --env production  # Not just "flash deploy"
```

**Cost overruns:**
```bash
# Check all environments
flash env list

# Scale down or delete unused
flash undeploy --interactive
flash env delete old-feature-env
```

### Next Step

For safe production deployment testing, see [Testing Before Production](#testing-before-production).

---

## Testing Before Production

Validate deployments before they reach production traffic.

### Goal

Ensure code quality and catch issues before production deployment using local previews and staging validation.

### Prerequisites

- Application working locally
- Staging environment available (or will create)
- Docker installed (for local preview testing)

### Testing Strategies

1. **Local preview** - Test deployment package locally
2. **Staging deployment** - Test in cloud before production
3. **Integration tests** - Automated test suite
4. **Load testing** - Performance validation

### Workflow Steps

#### Strategy 1: Local Preview Testing

Test the deployment package locally before uploading to Runpod.

**1. Build and Preview:**
```bash
flash deploy --preview
```

**Expected output:**
```
Building Flash application... ✓
Build complete: artifact.tar.gz (45.2 MB)

Launching local preview...
✓ Docker container started
✓ Preview running at http://localhost:8000

Test your preview:
  curl -X POST http://localhost:8000/run \
    -H "Content-Type: application/json" \
    -d '{"input": {"test": "data"}}'

Press Ctrl+C to stop preview
```

**2. Test Preview Endpoints:**
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"input": {"input_data": {"test": "preview"}}}'
```

**3. Validate Response:**
- Check response format
- Verify logic correctness
- Test error handling
- Check performance

**4. Stop Preview:**
```
Ctrl+C
```

**When to use preview:**
- Before first deployment
- After major refactoring
- When dependencies changed
- To debug packaging issues

#### Strategy 2: Staging Validation

Deploy to staging environment for comprehensive testing.

**1. Deploy to Staging:**
```bash
flash deploy --env staging
```

**2. Run Integration Tests:**
```bash
# Run test suite against staging
pytest tests/integration/ --base-url https://staging-endpoint/

# Or manual tests
./scripts/test-staging.sh
```

Example test script:
```bash
#!/bin/bash
# scripts/test-staging.sh

ENDPOINT="https://staging-endpoint.runpod.io"

echo "Testing staging deployment..."

# Test 1: Health check
echo "1. Health check"
curl -f "$ENDPOINT/health" || exit 1

# Test 2: Basic functionality
echo "2. Basic functionality"
response=$(curl -X POST "$ENDPOINT/run" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": "data"}}')
echo $response | jq -e '.output.status == "success"' || exit 1

# Test 3: Error handling
echo "3. Error handling"
response=$(curl -X POST "$ENDPOINT/run" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"invalid": true}}')
echo $response | jq -e '.output.error' || exit 1

echo "All tests passed!"
```

**3. Perform Load Testing:**
```bash
# Using Apache Bench
ab -n 1000 -c 10 \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -p test-payload.json \
  https://staging-endpoint/run

# Using hey
hey -n 1000 -c 10 \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"test": "data"}}' \
  https://staging-endpoint/run
```

**4. Monitor Staging:**
```bash
# Check worker scaling
flash env get staging

# Watch Runpod console
# - Request rate
# - Error rate
# - Response times
# - Worker scaling behavior
```

**5. Validate Results:**
- [ ] All integration tests pass
- [ ] Load test performance acceptable
- [ ] Error rate < 1%
- [ ] Worker scaling works correctly
- [ ] Response times within SLA

**6. Promote to Production:**
```bash
# Only after staging validation passes
flash deploy --env production
```

#### Strategy 3: Automated Testing Pipeline

Set up CI/CD pipeline for automated testing.

**Example GitHub Actions workflow:**

```yaml
# .github/workflows/deploy.yml
name: Deploy Flash Application

on:
  push:
    branches: [main]

jobs:
  test-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install runpod-flash
          pip install -e .

      - name: Run unit tests
        run: pytest tests/unit/

      - name: Deploy to staging
        env:
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
        run: flash deploy --env staging

      - name: Run integration tests
        env:
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
        run: pytest tests/integration/ --base-url ${{ env.STAGING_URL }}

      - name: Deploy to production
        if: success()
        env:
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
        run: flash deploy --env production
```

### Testing Checklist

Before production deployment:

**Local Testing:**
- [ ] `flash run` works without errors
- [ ] All endpoints tested via Swagger UI
- [ ] Edge cases handled correctly
- [ ] Error handling tested

**Preview Testing:**
- [ ] `flash deploy --preview` builds successfully
- [ ] Preview endpoints work correctly
- [ ] Response format validated

**Staging Testing:**
- [ ] Deployed to staging successfully
- [ ] Integration tests pass
- [ ] Load testing complete
- [ ] Error rate acceptable
- [ ] Performance meets SLA

**Production Readiness:**
- [ ] All tests passed
- [ ] Monitoring configured
- [ ] Rollback plan ready
- [ ] Team notified

### Common Issues

**Preview fails to start:**
```bash
# Check Docker is running
docker ps

# Check port availability
lsof -i:8000

# View Docker logs
docker logs <container-id>
```

**Integration tests fail on staging:**
```bash
# Check endpoint URL
flash env get staging

# Test manually first
curl https://staging-endpoint/run ...

# Check API key
echo $RUNPOD_API_KEY
```

**Load test shows performance issues:**
```bash
# Increase worker max
# Edit resource config in code:
# workersMax=5  # Increase from 3

# Redeploy
flash deploy --env staging
```

### Next Step

For removing old deployments, see [Cleanup and Maintenance](#cleanup-and-maintenance).

---

## Cleanup and Maintenance

Remove unused endpoints and environments to manage costs and keep infrastructure organized.

### Goal

Regularly clean up stale deployments, test environments, and unused resources to minimize costs and maintain clarity.

### Prerequisites

- Access to Runpod account
- List of active projects and their environments

### Cleanup Strategies

1. **Remove individual endpoints**
2. **Clean up entire environments**
3. **Remove stale tracking**
4. **Audit and optimize**

### Workflow Steps

#### Strategy 1: Remove Individual Endpoints

**1. List All Endpoints:**
```bash
flash undeploy list
```

**Output:**
```
Deployed Endpoints:
┌──────────────────────────┬─────────────────────┬──────────────────────┬────────────┐
│ Name                     │ Type                │ Environment          │ Status     │
├──────────────────────────┼─────────────────────┼──────────────────────┼────────────┤
│ my-api-gpu               │ LiveServerless      │ production           │ Active     │
│ test-feature-gpu         │ LiveServerless      │ dev                  │ Idle       │
│ old-worker-v1            │ LiveServerless      │ staging              │ Inactive   │
└──────────────────────────┴─────────────────────┴──────────────────────┴────────────┘
```

**2. Identify Endpoints to Remove:**
- Inactive endpoints (deleted externally)
- Test/dev endpoints no longer needed
- Old versions after deploying new version

**3. Remove Specific Endpoint:**
```bash
flash undeploy test-feature-gpu
```

**4. Or Use Interactive Selection:**
```bash
flash undeploy --interactive
```

Select endpoints with checkboxes, confirm deletion.

#### Strategy 2: Clean Up Environments

**1. List Environments:**
```bash
flash env list
```

**2. Identify Unused Environments:**
- Feature branches that are merged
- Old test environments
- Temporary staging environments

**3. Remove Individual Endpoints First (Optional):**
```bash
flash undeploy --env old-feature-env --all
```

**4. Delete Environment:**
```bash
flash env delete old-feature-env
```

Deletes environment and all its endpoints.

#### Strategy 3: Remove Stale Tracking

When endpoints are deleted manually via Runpod console:

**1. Identify Stale Entries:**
```bash
flash undeploy list
# Look for "Inactive" or "Not found" status
```

**2. Clean Up Stale Tracking:**
```bash
flash undeploy --cleanup-stale
```

**Output:**
```
Checking endpoint status...
Found 2 stale endpoints:
  - old-worker-v1 (deleted externally)
  - test-endpoint-abc (deleted externally)

Remove from tracking? [y/N]: y

Cleaning up... ✓
```

#### Strategy 4: Audit and Optimize

**1. Review All Deployments:**
```bash
# List all apps
flash app list

# Check each app
flash app get my-app

# List all environments
flash env list

# Check each environment
flash env get production
```

**2. Identify Cost Opportunities:**
- Environments with workersMin > 0 (always running)
- Multiple environments for same purpose
- Old test deployments still active

**3. Optimize Worker Configuration:**

**Before (high cost):**
```python
expensive_config = LiveServerless(
    workersMin=5,  # Always 5 running
    workersMax=10
)
```

**After (optimized):**
```python
optimized_config = LiveServerless(
    workersMin=0,   # Scale to zero
    workersMax=10,  # Handle spikes
    idleTimeout=60  # Quick shutdown
)
```

Redeploy with optimized config:
```bash
flash deploy --env production
```

### Weekly Cleanup Routine

**Every Monday morning:**

```bash
#!/bin/bash
# scripts/weekly-cleanup.sh

echo "Weekly Flash Cleanup"
echo "===================="

# 1. List all endpoints
echo "Current endpoints:"
flash undeploy list

# 2. Remove stale tracking
echo "Cleaning stale endpoints..."
flash undeploy --cleanup-stale --force

# 3. Check costs
echo "Checking costs at Runpod console..."
echo "Visit: https://runpod.io/console/billing"

# 4. List environments
echo "Current environments:"
flash env list

echo "Cleanup complete!"
```

Run weekly:
```bash
./scripts/weekly-cleanup.sh
```

### Cost Monitoring

**1. Check Runpod Billing:**
- Visit https://runpod.io/console/billing
- Review costs by environment
- Identify expensive endpoints

**2. Optimize High-Cost Endpoints:**
```bash
# Identify workers always running
flash env get production

# Adjust workersMin if traffic doesn't require it
# Edit worker config:
# workersMin=0  # Was 5

# Redeploy
flash deploy --env production
```

**3. Remove Unused Resources:**
```bash
# Delete test environments
flash env delete old-test-env

# Remove feature branch endpoints
flash undeploy feature-* --all --force
```

### Cleanup Checklist

Monthly maintenance:

- [ ] Review all deployed endpoints
- [ ] Remove inactive endpoints
- [ ] Delete merged feature environments
- [ ] Clean up stale tracking
- [ ] Review and optimize worker configs
- [ ] Check Runpod billing
- [ ] Document active deployments

### Common Issues

**Cannot delete endpoint (active requests):**
```bash
# Wait for requests to finish
# Or force deletion
flash undeploy my-endpoint --force
```

**Stale tracking persists:**
```bash
# Manual cleanup
rm .runpod/stale-endpoint.json

# Or force cleanup
flash undeploy --cleanup-stale --force
```

**High costs despite cleanup:**
```bash
# Check for workers with workersMin > 0
flash env get production

# Review Runpod console for all resources
# May have resources outside Flash tracking
```

### Next Step

For resolving deployment issues, see [Troubleshooting Deployments](#troubleshooting-deployments).

---

## Troubleshooting Deployments

Debug and resolve common deployment issues.

### Goal

Quickly identify and fix deployment problems using systematic troubleshooting approaches.

### Prerequisites

- Understanding of Flash deployment process
- Access to Runpod console
- Deployment logs available

### Troubleshooting Categories

1. Build failures
2. Upload issues
3. Endpoint creation failures
4. Runtime errors
5. Performance problems

### Troubleshooting Steps

#### Issue 1: Build Fails

**Symptom:**
```
ERROR: Failed to install dependencies
```

**Diagnosis:**
```bash
# Check pyproject.toml for issues
cat pyproject.toml

# Try building with verbose output
flash build -o test.tar.gz
```

**Solutions:**

**A. Dependency conflicts:**
```bash
# Check for version conflicts
pip install -e .

# If conflicts exist, update pyproject.toml
# Use compatible versions
```

**B. Package not found:**
```toml
# Fix typo or wrong package name in pyproject.toml
[project]
dependencies = [
    "corrected-package-name>=1.0.0"
]
```

```bash
flash build
```

**C. Manylinux compatibility:**
```
ERROR: No matching distribution found for package-name
```

Package doesn't support Linux. Solutions:
- Find alternative package
- Build from source (add build dependencies)
- Contact package maintainer

#### Issue 2: Build Size Too Large

**Symptom:**
```
ERROR: Archive size (523MB) exceeds 500MB limit
```

**Diagnosis:**
```bash
# Identify large packages
du -sh .build/lib/* | sort -h | tail -20
```

**Output example:**
```
156M    .build/lib/torch
89M     .build/lib/torchvision
45M     .build/lib/transformers
```

**Solutions:**

**A. Exclude packages in base image:**
```bash
flash build --exclude torch,torchvision,torchaudio
```

**B. Use --no-deps:**
```bash
flash build --no-deps --exclude torch
```

**C. Remove unnecessary dependencies:**
```toml
# Edit pyproject.toml - remove unused packages
[project]
dependencies = [
    # "pandas",  # Not needed for inference
    "torch>=2.0.0",
]
```

See [Troubleshooting Guide](troubleshooting.md#archive-size-limit) for details.

#### Issue 3: Upload Fails

**Symptom:**
```
ERROR: Upload failed: Connection timeout
```

**Diagnosis:**
```bash
# Check internet connection
ping runpod.io

# Check file size
ls -lh artifact.tar.gz
```

**Solutions:**

**A. Retry upload:**
```bash
flash deploy --env production
```

**B. Check network:**
```bash
# Test connectivity
curl -I https://api.runpod.io

# Check firewall settings
```

**C. Reduce archive size:**
```bash
flash deploy --env production --exclude torch,torchvision
```

#### Issue 4: Endpoint Creation Fails

**Symptom:**
```
ERROR: Failed to create endpoint: Insufficient GPU availability
```

**Diagnosis:**
```bash
# Check GPU type in worker config
cat gpu_worker.py

# Check Runpod console for GPU availability
```

**Solutions:**

**A. Change GPU type:**
```python
# Before (specific GPU)
gpu_config = LiveServerless(
    gpus=[GpuGroup.A100]  # May not be available
)

# After (more flexible)
gpu_config = LiveServerless(
    gpus=[GpuGroup.ANY]  # Any available GPU
)
```

Redeploy:
```bash
flash deploy --env production
```

**B. Wait and retry:**
```bash
# GPUs may become available
sleep 300
flash deploy --env production
```

**C. Choose different region:**
Modify config to try different GPU types:
```python
gpus=[GpuGroup.RTX_4090]  # More common
```

#### Issue 5: Runtime Errors

**Symptom:**
Endpoint deployed but returns errors when called.

**Diagnosis:**

**A. Check endpoint status:**
```bash
flash env get production
```

**B. View logs in Runpod console:**
1. Visit https://runpod.io/console/serverless
2. Click on endpoint
3. View "Logs" tab

**C. Test locally first:**
```bash
flash deploy --preview
# Test to isolate deployment vs code issues
```

**Solutions:**

**A. Import errors:**
```
ModuleNotFoundError: No module named 'your_module'
```

Solution: Add to `pyproject.toml`:
```toml
dependencies = ["your-module>=1.0.0"]
```

Redeploy:
```bash
flash deploy --env production
```

**B. Path errors:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'models/model.pt'
```

Solution: Check paths are relative and files included:
```bash
# Add to version control
git add models/model.pt

# Or update .flashignore to include
```

**C. GPU not available at runtime:**
```
RuntimeError: CUDA not available
```

Solution: Verify GPU configuration:
```python
gpu_config = LiveServerless(
    gpus=[GpuGroup.ANY],  # Ensure GPU specified
    ...
)
```

#### Issue 6: Performance Issues

**Symptom:**
Slow response times or frequent cold starts.

**Diagnosis:**
```bash
# Check worker configuration
flash env get production

# Monitor in Runpod console
# - Worker count
# - Cold start frequency
# - Response times
```

**Solutions:**

**A. Reduce cold starts:**
```python
# Increase workersMin to keep workers warm
gpu_config = LiveServerless(
    workersMin=1,  # Was 0
    workersMax=5,
    idleTimeout=300  # Keep alive longer
)
```

**B. Optimize startup time:**
- Reduce dependencies
- Lazy load large models
- Cache model loading

```python
# Lazy loading example
_model = None

@remote(resource_config=gpu_config)
async def infer(input_data: dict) -> dict:
    global _model
    if _model is None:
        _model = load_model()  # Only load once
    return _model.predict(input_data)
```

**C. Increase worker capacity:**
```python
# Handle more concurrent requests
gpu_config = LiveServerless(
    workersMax=10,  # Was 3
    ...
)
```

### General Debugging Approach

**1. Isolate the issue:**
- Works locally? → Deployment problem
- Build fails? → Dependency or config problem
- Upload fails? → Network problem
- Runtime fails? → Code or resource problem

**2. Check logs:**
- Flash CLI output
- `.build/` directory contents
- Runpod console logs

**3. Test incrementally:**
```bash
# Local
flash run  # Does it work?

# Preview
flash deploy --preview  # Does build work?

# Staging
flash deploy --env staging  # Does deployment work?

# Production
flash deploy --env production  # Ready!
```

**4. Use verbose output:**
```bash
# Add -v flag when available
# Or check detailed logs in console
```

### Emergency Rollback

If production is broken:

```bash
# 1. Undeploy broken version
flash undeploy production-endpoint --force

# 2. Checkout previous version
git checkout previous-tag

# 3. Redeploy
flash deploy --env production --force

# 4. Verify
flash env get production
```

### Getting Help

**If stuck:**

1. Check [Troubleshooting Guide](troubleshooting.md)
2. Review [Command Reference](commands.md)
3. Search Runpod documentation
4. Open issue: https://github.com/runpod/flash/issues

### Prevention Checklist

Avoid deployment issues:

- [ ] Test locally with `flash run`
- [ ] Test build with `flash build`
- [ ] Test preview with `flash deploy --preview`
- [ ] Deploy to staging first
- [ ] Run integration tests
- [ ] Monitor staging before production
- [ ] Have rollback plan ready

---

## Summary

These six workflows cover the complete Flash development lifecycle:

1. **[Local Development](#local-development-workflow)** - Fast iteration locally
2. **[Build and Deploy](#build-and-deploy-workflow)** - Production deployment
3. **[Multi-Environment](#multi-environment-management)** - Staging and production isolation
4. **[Testing](#testing-before-production)** - Validation before production
5. **[Cleanup](#cleanup-and-maintenance)** - Cost and resource management
6. **[Troubleshooting](#troubleshooting-deployments)** - Debug deployment issues

For detailed command documentation, see:
- [CLI Reference](../CLI-REFERENCE.md)
- [Commands Guide](commands.md)
- [Troubleshooting Guide](troubleshooting.md)
