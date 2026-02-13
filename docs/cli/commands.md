# Flash CLI Commands: Complete Reference

Exhaustive documentation for all Flash CLI commands. This guide covers every option, parameter, and use case.

## Table of Contents

- [flash init](#flash-init) - Create new Flash project
- [flash run](#flash-run) - Run development server
- [flash build](#flash-build) - Build deployment package
- [flash deploy](#flash-deploy) - Build and deploy application
- [flash undeploy](#flash-undeploy) - Delete deployed endpoints
- [flash env](#flash-env) - Manage deployment environments
  - [flash env list](#flash-env-list)
  - [flash env create](#flash-env-create)
  - [flash env get](#flash-env-get)
  - [flash env delete](#flash-env-delete)
- [flash app](#flash-app) - Manage Flash applications
  - [flash app list](#flash-app-list)
  - [flash app create](#flash-app-create)
  - [flash app get](#flash-app-get)
  - [flash app delete](#flash-app-delete)

---

## flash init

Create a new Flash project with the correct structure, boilerplate code, and configuration files.

### Synopsis

```bash
flash init [PROJECT_NAME] [OPTIONS]
```

### Description

Creates a new Flash project directory with all necessary files for development and deployment. The command generates a complete project structure including FastAPI application, worker templates, configuration files, and documentation.

If `PROJECT_NAME` is omitted or set to `.`, the project is initialized in the current directory.

### Arguments

**`PROJECT_NAME`** (optional)
- Type: String
- Default: Current directory if `.` specified
- Description: Name for the project directory. Creates a new subdirectory with this name.

### Options

**`--force`, `-f`**
- Type: Boolean flag
- Default: `false`
- Description: Overwrite existing files without prompting for confirmation. Use with caution as this can replace modified files.

### Generated Project Structure

```
project-name/
├── main.py                 # FastAPI application entry point
├── mothership.py          # Mothership endpoint configuration
├── gpu_worker.py          # GPU worker template with @remote decorator
├── pyproject.toml         # Project dependencies and metadata
├── requirements.txt       # Pinned dependencies (generated)
├── .env.example           # Environment variable template
├── .gitignore            # Git ignore patterns (includes flash auto-generated files)
├── .flashignore          # Files to exclude from build
├── .python-version       # Python version specification
└── README.md             # Project documentation
```

### Generated Files Explained

**main.py**
- FastAPI application that loads routers from worker files
- Configured for local development and testing
- Automatically discovers `@remote` decorated functions

**mothership.py**
- Configures the mothership endpoint (load-balanced FastAPI application endpoint)
- Can be customized for different scaling requirements
- Delete this file if you don't want to deploy the mothership endpoint

**gpu_worker.py**
- Template worker with `@remote` decorator
- Configured for GPU resources via `LiveServerless`
- Contains example endpoint with proper structure

**pyproject.toml**
- Project metadata and dependencies
- Used by `flash build` to install packages
- Update this file to add dependencies

**.flashignore**
- Specifies files to exclude from deployment package
- Similar to `.gitignore` but for builds
- Reduces package size by excluding unnecessary files

### Examples

#### Create New Project in Subdirectory

```bash
flash init my-api
cd my-api
ls -la
```

Output:
```
drwxr-xr-x  12 user  staff   384 Jan 01 12:00 .
drwxr-xr-x   8 user  staff   256 Jan 01 12:00 ..
-rw-r--r--   1 user  staff   271 Jan 01 12:00 .env.example
-rw-r--r--   1 user  staff   350 Jan 01 12:00 .flashignore
-rw-r--r--   1 user  staff   580 Jan 01 12:00 .gitignore
-rw-r--r--   1 user  staff    10 Jan 01 12:00 .python-version
-rw-r--r--   1 user  staff  2154 Jan 01 12:00 README.md
-rw-r--r--   1 user  staff  1256 Jan 01 12:00 gpu_worker.py
-rw-r--r--   1 user  staff   845 Jan 01 12:00 main.py
-rw-r--r--   1 user  staff   456 Jan 01 12:00 mothership.py
-rw-r--r--   1 user  staff   512 Jan 01 12:00 pyproject.toml
```

#### Initialize in Current Directory

```bash
mkdir my-api && cd my-api
flash init .
```

Creates all files in the current `my-api/` directory.

#### Overwrite Existing Project

```bash
# Project already exists with modifications
flash init my-api --force
```

Overwrites all template files without prompting. Useful for resetting a project to template defaults.

#### Create Multiple Projects

```bash
flash init api-v1
flash init api-v2
flash init testing-env
```

Creates three separate project directories.

#### Initialize with Git

```bash
flash init my-api
cd my-api
git init
git add .
git commit -m "Initial commit"
```

The generated `.gitignore` already includes necessary patterns.

### What Happens Internally

1. **Directory Creation**: Creates project directory if it doesn't exist
2. **Template Rendering**: Generates files from internal templates
3. **Dependency Setup**: Creates `pyproject.toml` with base dependencies
4. **Configuration Files**: Generates `.flashignore`, `.gitignore`, `.env.example`
5. **Documentation**: Creates README with project-specific instructions
6. **Validation**: Ensures all files are created successfully

### Next Steps After Initialization

1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your RUNPOD_API_KEY
   ```

2. **Install Dependencies**
   ```bash
   pip install -e .
   ```

3. **Run Locally**
   ```bash
   flash run
   ```

4. **View Documentation**
   ```
   http://localhost:8888/docs
   ```

### Common Issues

**Directory Already Exists**

Problem:
```
Error: Directory 'my-api' already exists. Use --force to overwrite.
```

Solution:
```bash
flash init my-api --force
# Or use a different name
flash init my-api-v2
```

**Permission Denied**

Problem:
```
Error: Permission denied: '/path/to/directory'
```

Solution:
```bash
# Ensure you have write permissions
chmod u+w /path/to/directory
# Or create in a directory you own
cd ~
flash init my-api
```

### Related Commands

- [`flash run`](#flash-run) - Run the initialized project
- [`flash build`](#flash-build) - Build the project
- [`flash deploy`](#flash-deploy) - Deploy the project

### Related Workflows

- [Local Development Workflow](workflows.md#local-development-workflow)
- [Project Setup Best Practices](workflows.md#project-setup-best-practices)

---

## flash run

Run the Flash development server locally with hot reloading for rapid development and testing.

### Synopsis

```bash
flash run [OPTIONS]
```

### Description

Starts a local uvicorn development server that runs your Flash application. The server automatically discovers all `@remote` decorated functions and makes them available as HTTP endpoints. Supports hot reloading, custom host/port configuration, and optional resource auto-provisioning.

### Architecture: Hybrid Local + Cloud

With `flash run`, your system operates in a **hybrid architecture**:

- **Your FastAPI app runs locally** on your machine (localhost:8888)
- **`@remote` functions run on Runpod** as serverless endpoints
- **Hot reload works** because your app code is local—changes are picked up instantly
- **Endpoints are prefixed with `live-`** to distinguish from production (e.g., `gpu-worker` becomes `live-gpu-worker`)

This hybrid approach enables rapid development: iterate on your orchestration logic locally with hot-reload while testing real GPU/CPU workloads in the cloud.

### Options

**`--host`**
- Type: String
- Default: `localhost`
- Environment Variable: `FLASH_HOST`
- Description: Host address to bind the server to. Use `0.0.0.0` to make the server accessible from your network.

**`--port`, `-p`**
- Type: Integer
- Default: `8888`
- Environment Variable: `FLASH_PORT`
- Description: Port number to bind the server to. Must be available (not in use).

**`--reload` / `--no-reload`**
- Type: Boolean flag
- Default: `--reload` (enabled)
- Description: Enable or disable automatic reloading when source files change. Disable for production-like testing.

**`--auto-provision`**
- Type: Boolean flag
- Default: `false`
- Description: Automatically provision Runpod serverless endpoints on startup. Useful for testing deployed resources locally.

### Environment Variables

Variables can be set in `.env` file or exported in shell:

```bash
# .env file
FLASH_HOST=0.0.0.0
FLASH_PORT=9000
RUNPOD_API_KEY=your-key-here
```

**Precedence (highest to lowest):**
1. Command-line options (`--host`, `--port`)
2. Environment variables (`FLASH_HOST`, `FLASH_PORT`)
3. Default values (`localhost`, `8888`)

### Examples

#### Basic Development Server

```bash
flash run
```

Output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8888 (Press CTRL+C to quit)
INFO:     Started reloader process [12346] using StatReload
```

Visit `http://localhost:8888/docs` for interactive API documentation.

#### Custom Host and Port

```bash
flash run --host 0.0.0.0 --port 3000
```

Makes server accessible from network at `http://<your-ip>:3000`. Useful for:
- Testing on mobile devices
- Accessing from other machines on your network
- Development in containers or VMs

#### Disable Auto-Reload

```bash
flash run --no-reload
```

Useful for:
- Debugging issues related to hot reload
- Testing production-like behavior
- Profiling performance without reload overhead

#### Using Environment Variables

```bash
export FLASH_HOST=0.0.0.0
export FLASH_PORT=9000
flash run
```

Or with `.env` file:
```bash
# .env
FLASH_HOST=0.0.0.0
FLASH_PORT=9000
```

```bash
flash run
# Automatically loads .env
```

#### Auto-Provision Resources

```bash
flash run --auto-provision
```

This will:
1. Start local development server
2. Provision Runpod endpoints for all `@remote` functions
3. Allow testing with real Runpod infrastructure
4. Incur Runpod costs (workers will spin up)

**Use case:** Testing autoscaling behavior and cold start times.

#### Combine Options

```bash
flash run --host 0.0.0.0 --port 9000 --no-reload
```

Runs on all network interfaces, port 9000, without auto-reload.

#### Development with External Access

```bash
flash run --host 0.0.0.0
# Server accessible at http://192.168.1.100:8888 (your local IP)
```

Share the URL with team members for testing.

### What Happens Internally

1. **Application Loading**: Imports `main.py` and discovers FastAPI app
2. **Router Discovery**: Scans for APIRouter exports in worker files
3. **Remote Function Discovery**: Finds all `@remote` decorated functions
4. **Uvicorn Startup**: Starts ASGI server with specified configuration
5. **Hot Reload Setup**: Watches Python files for changes (if enabled)
6. **Documentation Generation**: Creates OpenAPI schema at `/docs`

### Testing Your Application

After starting the server, test your endpoints using:

**Swagger UI (Recommended)**

Visit `http://localhost:8888/docs`
- Interactive API explorer
- Try requests directly in browser
- See request/response schemas
- View example payloads

**curl**

```bash
curl -X POST http://localhost:8888/your-endpoint \
  -H "Content-Type: application/json" \
  -d '{"input": "test data"}'
```

**Python requests**

```python
import requests

response = requests.post(
    "http://localhost:8888/your-endpoint",
    json={"input": "test data"}
)
print(response.json())
```

**HTTPie**

```bash
http POST localhost:8888/your-endpoint input="test data"
```

### Hot Reload Behavior

When `--reload` is enabled (default):

1. **File Watching**: Monitors `.py` files in project directory
2. **Change Detection**: Detects file modifications
3. **Process Restart**: Restarts server with new code
4. **State Loss**: In-memory state is reset

**Files watched:**
- `*.py` in project root
- `workers/**/*.py`
- Excludes: `.venv/`, `.build/`, `__pycache__/`

**Example workflow:**
```bash
# Terminal 1: Run server
flash run

# Terminal 2: Edit code
echo 'print("Updated!")' >> gpu_worker.py

# Terminal 1: Automatic reload
# INFO: Detected file change, reloading...
# INFO: Application startup complete.
```

### Performance Considerations

**Development Mode:**
- Hot reload adds overhead
- Debug logging enabled
- Not optimized for high load

**For production-like testing:**
```bash
flash run --no-reload
# More representative of deployed performance
```

### Common Issues

**Port Already in Use**

Problem:
```
ERROR: [Errno 48] Address already in use
```

Solutions:
```bash
# Option 1: Use different port
flash run --port 9000

# Option 2: Kill process using port
lsof -ti:8888 | xargs kill -9

# Option 3: Find and manually kill
lsof -i:8888  # Shows process ID
kill <pid>
```

**Import Errors**

Problem:
```
ModuleNotFoundError: No module named 'your_module'
```

Solutions:
```bash
# Ensure dependencies installed
pip install -e .

# Or install specific package
pip install your-module

# Check virtual environment active
which python  # Should point to .venv/bin/python
```

**Slow Hot Reload**

Problem: Server takes long time to reload after changes.

Solutions:
```bash
# Reduce watched files
# Add to .gitignore (uvicorn respects it):
echo "large_files/" >> .gitignore

# Or disable reload temporarily
flash run --no-reload
```

**Cannot Access from Network**

Problem: Cannot reach server from other devices.

Solutions:
```bash
# Use 0.0.0.0 instead of localhost
flash run --host 0.0.0.0

# Check firewall settings
# macOS: System Preferences → Security & Privacy → Firewall
# Linux: sudo ufw allow 8888
```

**API Key Not Found (with --auto-provision)**

Problem:
```
Error: RUNPOD_API_KEY environment variable not set
```

Solution:
```bash
export RUNPOD_API_KEY=your-key-here
flash run --auto-provision
```

### Related Commands

- [`flash init`](#flash-init) - Create project to run
- [`flash build`](#flash-build) - Build for deployment
- [`flash deploy`](#flash-deploy) - Deploy to production

### Related Workflows

- [Local Development Workflow](workflows.md#local-development-workflow)
- [Testing Before Production](workflows.md#testing-before-production)

---

## flash build

Build the Flash application into a deployable package for Runpod serverless infrastructure.

### Synopsis

```bash
flash build [OPTIONS]
```

### Description

Packages your Flash application and its dependencies into a tar.gz archive suitable for deployment to Runpod. The build process installs dependencies cross-platform (Linux x86_64), generates handler files for each `@remote` function, creates a manifest with resource configurations, and produces a final artifact ready for upload.

The `.build/` directory is preserved after building for inspection and debugging.

**Build does not deploy.** Use `flash deploy` to build and deploy in one step.

### Options

**`--no-deps`**
- Type: Boolean flag
- Default: `false`
- Description: Skip transitive dependencies during pip install. Only installs packages directly listed in `pyproject.toml`, not their dependencies. Use when dependencies are pre-installed in base image.

**`--output`, `-o`**
- Type: String
- Default: `artifact.tar.gz`
- Description: Custom name for the output archive. Useful for versioning or multiple builds.

**`--exclude`**
- Type: String (comma-separated)
- Default: None
- Description: Packages to exclude from the build. Used to avoid bundling packages already present in Runpod base images. Significantly reduces archive size.

**`--use-local-flash`**
- Type: Boolean flag
- Default: `false`
- Description: Bundle local `runpod_flash` source code instead of installing from PyPI. For Flash SDK development and testing.

### Build Process

The build command executes these steps:

1. **Create Build Directory**
   - Creates/cleans `.build/` directory
   - Preserves directory after completion for inspection

2. **Install Dependencies**
   - Runs `pip install --target .build/lib --platform manylinux2014_x86_64`
   - Installs packages for Linux x86_64 (Runpod platform)
   - Respects `--no-deps` and `--exclude` options

3. **Generate Manifest**
   - Scans code for `@remote` decorated functions
   - Extracts resource configurations (`LiveServerless`, etc.)
   - Creates `flash_manifest.json` with deployment metadata

4. **Generate Handlers**
   - Creates handler file for each `@remote` function
   - Handlers interface between Runpod and your functions
   - Includes error handling and serialization logic

5. **Copy Application Code**
   - Copies project files to `.build/`
   - Respects `.flashignore` patterns
   - Includes all necessary source files

6. **Create Archive**
   - Packages `.build/` contents into tar.gz
   - Compresses for upload efficiency
   - Reports final size

### Examples

#### Standard Build

```bash
flash build
```

Output:
```
Building Flash application...
Creating build directory...
Installing dependencies...
  ✓ Installed 25 packages
Generating manifest...
  ✓ Found 3 remote functions
  ✓ Generated flash_manifest.json
Generating handlers...
  ✓ Created handler_gpu_worker_process_request.py
  ✓ Created handler_mothership.py
Copying application code...
Creating archive...
  ✓ Build complete: artifact.tar.gz (45.2 MB)

Archive size: 45.2 MB (500 MB limit)
Build directory preserved at: .build/
```

#### Custom Archive Name

```bash
flash build -o my-app-v1.2.3.tar.gz
```

Useful for versioning:
```bash
VERSION=1.2.3
flash build -o my-app-v${VERSION}.tar.gz
```

#### Exclude Large Packages

```bash
flash build --exclude torch,torchvision,torchaudio
```

Reduces build size by excluding packages in Runpod base image.

**Common packages to exclude:**
- `torch`, `torchvision`, `torchaudio` - PyTorch stack
- `transformers` - Hugging Face transformers
- `tensorflow`, `tf-keras` - TensorFlow stack
- `jax`, `jaxlib` - JAX ML framework
- `opencv-python` - OpenCV

Check Runpod base image documentation for full list.

#### Multiple Exclusions

```bash
flash build --exclude torch,torchvision,torchaudio,transformers,opencv-python
```

#### Skip Transitive Dependencies

```bash
flash build --no-deps
```

Only installs packages in `pyproject.toml` `dependencies` list, not their subdependencies. Use when:
- Base image has most dependencies
- You want minimal package size
- Dependencies conflict with base image versions

#### Development Build

```bash
flash build --use-local-flash
```

Bundles your local `runpod_flash` modifications for testing. Path detected automatically from your environment.

#### Combined Options

```bash
flash build \
  -o my-app-prod-v2.tar.gz \
  --exclude torch,torchvision,torchaudio \
  --no-deps
```

Creates optimized production build with custom name.

### Build Size Optimization

If your build exceeds the 500MB deployment limit:

**1. Identify Large Packages**

```bash
du -sh .build/lib/* | sort -h | tail -20
```

Example output:
```
156M    .build/lib/torch
89M     .build/lib/torchvision
45M     .build/lib/transformers
23M     .build/lib/opencv_python
...
```

**2. Exclude Packages in Base Image**

```bash
# Exclude PyTorch (already in Runpod GPU images)
flash build --exclude torch,torchvision,torchaudio
```

**3. Use --no-deps for Common Packages**

```bash
# Base image has most ML packages
flash build --no-deps --exclude torch,torchvision
```

**4. Check .flashignore**

```bash
# Exclude large files not needed at runtime
echo "tests/" >> .flashignore
echo "docs/" >> .flashignore
echo "*.md" >> .flashignore
echo "data/" >> .flashignore
```

**5. Remove Unnecessary Dependencies**

Edit `pyproject.toml`:
```toml
[project]
dependencies = [
    # Remove unused packages
    # "pandas",  # Not needed for inference
    "torch>=2.0.0",
]
```

### Debugging Builds

The `.build/` directory is preserved for inspection:

```bash
# View build contents
ls -lah .build/

# Check installed packages
ls -1 .build/lib/

# Inspect manifest
cat .build/flash_manifest.json

# View generated handler
cat .build/handler_gpu_worker_process_request.py

# Check package sizes
du -sh .build/lib/* | sort -h
```

### Understanding the Manifest

The `flash_manifest.json` contains deployment metadata:

```json
{
  "resources": [
    {
      "name": "gpu_worker_process_request",
      "type": "LiveServerless",
      "config": {
        "name": "my_api_gpu",
        "gpus": ["ANY"],
        "workersMin": 0,
        "workersMax": 3,
        "idleTimeout": 300
      },
      "handler": "handler_gpu_worker_process_request.py"
    }
  ],
  "mothership": {
    "enabled": true,
    "config": {
      "name": "my_api_mothership",
      "workersMin": 1,
      "workersMax": 3
    }
  }
}
```

### Cross-Platform Builds

Flash builds for Linux x86_64 regardless of your development platform:

**macOS (ARM64) → Linux x86_64:**
```bash
flash build
# Packages installed for manylinux2014_x86_64
```

**Windows → Linux x86_64:**
```bash
flash build
# Packages installed for manylinux2014_x86_64
```

**Linux (x86_64) → Linux x86_64:**
```bash
flash build
# Native platform build
```

This ensures your application works on Runpod's Linux infrastructure.

### Common Issues

**Archive Too Large**

Problem:
```
ERROR: Archive size (523MB) exceeds 500MB limit
```

Solution:
```bash
# Identify large packages
du -sh .build/lib/* | sort -h | tail -10

# Exclude packages in base image
flash build --exclude torch,torchvision,torchaudio,transformers

# Check size again
ls -lh artifact.tar.gz
```

**Dependency Installation Failed**

Problem:
```
ERROR: Could not find a version that satisfies the requirement
```

Solutions:
```bash
# Check pyproject.toml for typos
cat pyproject.toml

# Update dependency versions
# Edit pyproject.toml, then:
flash build

# Install locally first to verify
pip install <package-name>
```

**Import Error During Build**

Problem:
```
ModuleNotFoundError: No module named 'your_module'
```

Solution:
```bash
# Ensure dependencies in pyproject.toml
# Add missing dependency:
# [project]
# dependencies = ["your-module>=1.0.0"]

flash build
```

**Permission Denied**

Problem:
```
Permission denied: '.build/...'
```

Solution:
```bash
# Remove .build directory
rm -rf .build

# Retry
flash build
```

**Manylinux Compatibility Error**

Problem:
```
ERROR: Package has no compatible wheels for manylinux2014_x86_64
```

Solution:
```bash
# Package may not support Linux
# Options:
# 1. Use alternative package
# 2. Build from source (add build dependencies)
# 3. Contact package maintainer

# Temporarily skip package
flash build --exclude problematic-package
```

### Related Commands

- [`flash deploy`](#flash-deploy) - Build and deploy in one step
- [`flash run`](#flash-run) - Test before building

### Related Workflows

- [Build and Deploy Workflow](workflows.md#build-and-deploy-workflow)
- [Build Optimization](workflows.md#build-optimization)

---

## flash deploy

Build and deploy the Flash application to Runpod in a single command.

### Synopsis

```bash
flash deploy [OPTIONS]
```

### Description

Combines building and deploying into one streamlined command. Packages your application (same as `flash build`), then uploads to Runpod and creates serverless endpoints for each resource defined in your code.

If only one environment exists, it's used automatically. With multiple environments, specify with `--env` or select interactively.

### Architecture: Fully Deployed to Runpod

With `flash deploy`, your **entire application** runs on Runpod Serverless:

- **Your FastAPI app runs on Runpod** as the "mothership" endpoint
- **`@remote` functions run on Runpod** as separate worker endpoints
- **Users call the mothership URL** directly (e.g., `https://xyz123.api.runpod.ai/api/hello`)
- **No `live-` prefix** on endpoint names—these are production endpoints
- **No hot reload**—code changes require a new deployment

This is different from `flash run`, where your FastAPI app runs locally on your machine. With `flash deploy`, everything is in the cloud for production use.

### Options

**Deployment Options**

**`--env`, `-e`**
- Type: String
- Default: Auto-select if only one exists
- Description: Target environment name for deployment. Environments isolate deployments (staging, production, etc.).

**`--app`, `-a`**
- Type: String
- Default: Current app context
- Description: Flash app name to deploy to. Apps provide namespace isolation.

**`--preview`**
- Type: Boolean flag
- Default: `false`
- Description: Build and launch local Docker preview environment instead of deploying to Runpod. Useful for testing the deployment package locally.

**Build Options** (same as `flash build`)

**`--no-deps`**
- Skip transitive dependencies during pip install

**`--exclude`**
- Comma-separated packages to exclude from build

**`--use-local-flash`**
- Bundle local runpod_flash source instead of PyPI version

**`--output`, `-o`**
- Custom archive name (default: `artifact.tar.gz`)

### Environment Variables

**`RUNPOD_API_KEY`** (required)
- Runpod API authentication key
- Get from https://runpod.io/console/user/settings
- Can be set in `.env` file

### Examples

#### Basic Deployment (Auto-Select Environment)

```bash
flash deploy
```

Output:
```
Building Flash application...
✓ Build complete: artifact.tar.gz (45.2 MB)

Deploying to environment: dev (auto-selected)
Uploading artifact... ████████████████████ 100% (45.2 MB)
Creating endpoints...
  ✓ gpu_worker: https://abcd1234-my-api-gpu.runpod.io
  ✓ mothership: https://efgh5678-my-api-mothership.runpod.io

Deployment successful!

Test your endpoints:
  curl -X POST https://abcd1234-my-api-gpu.runpod.io/run \
    -H "Authorization: Bearer $RUNPOD_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"input": {"your": "data"}}'

Next steps:
  1. Test endpoints with curl or Postman
  2. Monitor at https://runpod.io/console/serverless
  3. Update deployment: flash deploy --env dev
  4. View logs: Visit Runpod console
```

#### Deploy to Specific Environment

```bash
flash deploy --env production
```

Explicitly targets "production" environment.

#### Deploy with Size Optimization

```bash
flash deploy --env prod --exclude torch,torchvision,torchaudio
```

Reduces deployment package size by excluding packages in Runpod base image.

#### Deploy Different App

```bash
flash deploy --app my-other-app --env staging
```

Deploys to "staging" environment in "my-other-app" namespace.

#### Local Preview (No Deployment)

```bash
flash deploy --preview
```

Builds and launches in local Docker container for testing:
```
Building Flash application...
✓ Build complete: artifact.tar.gz (45.2 MB)

Launching local preview...
✓ Docker container started
✓ Preview running at http://localhost:8000

Test your preview:
  curl -X POST http://localhost:8000/run \
    -H "Content-Type: application/json" \
    -d '{"input": {"your": "data"}}'

Press Ctrl+C to stop preview
```

#### Development Deployment

```bash
flash deploy --env dev --use-local-flash
```

Deploys with local Flash SDK modifications for testing SDK changes.

#### Full Production Deployment

```bash
flash deploy \
  --env production \
  --exclude torch,torchvision,torchaudio,transformers \
  --no-deps
```

Optimized deployment to production environment.

### Deployment Process

1. **Build Phase** (same as `flash build`)
   - Create `.build/` directory
   - Install dependencies
   - Generate manifest and handlers
   - Create archive

2. **Validation**
   - Check `RUNPOD_API_KEY` is set
   - Verify archive size ≤ 500MB
   - Validate environment exists

3. **Upload**
   - Authenticate with Runpod API
   - Upload artifact with progress bar
   - Verify upload integrity

4. **Endpoint Creation**
   - Create/update serverless endpoints for each resource
   - Configure autoscaling (workers min/max)
   - Set idle timeout
   - Assign GPU types

5. **Verification**
   - Check endpoint status
   - Wait for endpoints to become active
   - Report endpoint URLs

### Environment Selection Logic

**One Environment:**
```bash
flash deploy
# Automatically uses the only environment
```

**Multiple Environments:**
```bash
flash deploy
# Prompts:
# Available environments:
# 1. dev
# 2. staging
# 3. production
# Select environment (1-3): _
```

Or specify explicitly:
```bash
flash deploy --env staging
```

**No Environments:**
```bash
flash deploy
# Error: No environments found
# Create one with: flash env create <name>
```

### Post-Deployment Testing

After successful deployment, test your endpoints:

**Test GPU Worker Endpoint:**
```bash
curl -X POST https://abcd1234-my-api-gpu.runpod.io/run \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "input_data": {"message": "test"}
    }
  }'
```

**Test Mothership Endpoint:**
```bash
curl -X POST https://efgh5678-my-api-mothership.runpod.io/your-route \
  -H "Content-Type: application/json" \
  -d '{"your": "data"}'
```

### Monitoring Deployments

**View in Runpod Console:**
https://runpod.io/console/serverless

**Check deployment status:**
```bash
flash env get production
```

**View logs:**
1. Go to Runpod console
2. Select your endpoint
3. View "Logs" tab

### Updating Deployments

To update an existing deployment:

```bash
# Make code changes
# ...

# Redeploy to same environment
flash deploy --env production
```

This:
- Rebuilds with new code
- Uploads new artifact
- Updates existing endpoints (zero downtime)

### Common Issues

**Missing API Key**

Problem:
```
Error: RUNPOD_API_KEY environment variable not set
```

Solution:
```bash
export RUNPOD_API_KEY=your-key-here
# Or add to .env file
echo "RUNPOD_API_KEY=your-key-here" >> .env
```

**Archive Too Large**

Problem:
```
ERROR: Archive size (523MB) exceeds 500MB limit
```

Solution:
```bash
flash deploy --env prod --exclude torch,torchvision,torchaudio
```

See [Build Size Optimization](#build-size-optimization) for details.

**Environment Not Found**

Problem:
```
Error: Environment 'production' not found
```

Solution:
```bash
# List available environments
flash env list

# Create missing environment
flash env create production

# Deploy
flash deploy --env production
```

**Upload Failed**

Problem:
```
Error: Upload failed: Connection timeout
```

Solutions:
```bash
# Check internet connection
ping runpod.io

# Retry deployment
flash deploy --env production

# Check firewall settings
```

**Endpoint Creation Failed**

Problem:
```
Error: Failed to create endpoint: Insufficient GPU availability
```

Solutions:
```bash
# Wait and retry (GPUs may become available)
flash deploy --env production

# Change GPU type in resource config
# Edit gpu_worker.py:
# gpus=[GpuGroup.RTX_3090]  # More common GPU

# Redeploy
flash deploy --env production
```

**Authentication Failed**

Problem:
```
Error: Invalid API key
```

Solutions:
```bash
# Verify API key
echo $RUNPOD_API_KEY

# Get new key from https://runpod.io/console/user/settings
export RUNPOD_API_KEY=new-key-here

# Retry
flash deploy --env production
```

### Related Commands

- [`flash build`](#flash-build) - Build without deploying
- [`flash env`](#flash-env) - Manage environments
- [`flash undeploy`](#flash-undeploy) - Delete deployments
- [`flash run`](#flash-run) - Test locally before deploying

### Related Workflows

- [Build and Deploy Workflow](workflows.md#build-and-deploy-workflow)
- [Multi-Environment Management](workflows.md#multi-environment-management)
- [Testing Before Production](workflows.md#testing-before-production)

---

## flash undeploy

Delete deployed Runpod serverless endpoints and clean up resources.

### Synopsis

```bash
flash undeploy [NAME] [OPTIONS]
```

### Description

Removes deployed endpoints from Runpod infrastructure. Supports deleting individual endpoints, bulk deletion, interactive selection, and cleaning up stale tracking data.

Undeployment is permanent and cannot be undone. Endpoints are deleted from Runpod and removed from local tracking.

### Arguments

**`NAME`** (optional)
- Type: String
- Special value: `list` - Show all endpoints without deleting
- Description: Name of the endpoint to undeploy. If omitted, other options determine behavior.

### Options

**`--all`**
- Type: Boolean flag
- Default: `false`
- Description: Undeploy all tracked endpoints. Prompts for confirmation unless `--force` is used.

**`--interactive`, `-i`**
- Type: Boolean flag
- Default: `false`
- Description: Show interactive checkbox UI to select which endpoints to delete. Useful for selective cleanup.

**`--cleanup-stale`**
- Type: Boolean flag
- Default: `false`
- Description: Remove endpoints from local tracking that were already deleted externally (e.g., via Runpod console). Does not delete active endpoints.

**`--force`, `-f`**
- Type: Boolean flag
- Default: `false`
- Description: Skip all confirmation prompts. Use with caution as deletions are permanent.

### Usage Modes

The command operates in different modes based on options:

1. **List Mode** - `flash undeploy list`
2. **Single Endpoint** - `flash undeploy <name>`
3. **All Endpoints** - `flash undeploy --all`
4. **Interactive Selection** - `flash undeploy --interactive`
5. **Cleanup Stale** - `flash undeploy --cleanup-stale`

### Examples

#### List All Endpoints

```bash
flash undeploy list
```

Output:
```
Deployed Endpoints:
┌──────────────────────────┬─────────────────────┬──────────────────────┬────────────┐
│ Name                     │ Type                │ Environment          │ Status     │
├──────────────────────────┼─────────────────────┼──────────────────────┼────────────┤
│ my-api-gpu               │ LiveServerless      │ production           │ Active     │
│ my-api-mothership        │ LiveLoadBalancer    │ production           │ Active     │
│ test-worker              │ LiveServerless      │ dev                  │ Active     │
│ old-api-gpu              │ LiveServerless      │ staging              │ Inactive   │
└──────────────────────────┴─────────────────────┴──────────────────────┴────────────┘

Total: 4 endpoints
```

#### Undeploy Specific Endpoint

```bash
flash undeploy my-api-gpu
```

Output:
```
Endpoint: my-api-gpu
Type: LiveServerless (GPU)
Environment: production
Status: Active

This will permanently delete the endpoint.
Continue? [y/N]: y

Deleting endpoint... ✓
Removed from tracking ✓

Endpoint 'my-api-gpu' undeployed successfully.
```

#### Undeploy with Force (No Confirmation)

```bash
flash undeploy test-worker --force
```

Output:
```
Deleting endpoint 'test-worker'... ✓
Endpoint undeployed successfully.
```

#### Undeploy All Endpoints

```bash
flash undeploy --all
```

Output:
```
Found 4 endpoints to undeploy:
  - my-api-gpu (production)
  - my-api-mothership (production)
  - test-worker (dev)
  - old-api-gpu (staging)

This will permanently delete ALL endpoints.
Continue? [y/N]: y

Deleting endpoints...
  my-api-gpu ✓
  my-api-mothership ✓
  test-worker ✓
  old-api-gpu ✓

All endpoints undeployed successfully.
```

#### Undeploy All (Force, No Confirmation)

```bash
flash undeploy --all --force
```

Immediately deletes all endpoints without prompting.

#### Interactive Selection

```bash
flash undeploy --interactive
```

Output:
```
Select endpoints to undeploy:
[✓] my-api-gpu (production)
[✓] my-api-mothership (production)
[ ] test-worker (dev)
[✓] old-api-gpu (staging)

Press SPACE to toggle, ENTER to confirm, ESC to cancel

Selected 3 endpoints.
Continue? [y/N]: y

Deleting endpoints...
  my-api-gpu ✓
  my-api-mothership ✓
  old-api-gpu ✓

Selected endpoints undeployed successfully.
```

#### Cleanup Stale Tracking

```bash
flash undeploy --cleanup-stale
```

Output:
```
Checking endpoint status...
Found 2 stale endpoints (deleted externally):
  - old-worker-v1
  - test-endpoint-abc

Remove from tracking? [y/N]: y

Cleaning up...
  old-worker-v1 ✓
  test-endpoint-abc ✓

Stale tracking cleaned up successfully.
```

### What Gets Deleted

**On Runpod:**
- Serverless endpoint and its configuration
- Auto-scaling settings
- Worker instances (if running)
- Endpoint metrics and logs (after retention period)

**Locally:**
- `.runpod/<endpoint-name>.json` tracking file
- Endpoint reference in environment configuration

**Not Deleted:**
- Source code
- Build artifacts (`.build/`, `artifact.tar.gz`)
- Environment configuration
- Other endpoints in the same environment

### Use Cases

**Development Cleanup:**
```bash
# After testing feature
flash undeploy feature-test-gpu --force
```

**Remove Old Deployments:**
```bash
# Interactive selection
flash undeploy --interactive
# Select old endpoints, keep active ones
```

**Environment Teardown:**
```bash
# Remove all staging endpoints
flash env get staging  # Note endpoint names
flash undeploy staging-* --force
# Or delete entire environment
flash env delete staging
```

**Fix Tracking Issues:**
```bash
# Deleted endpoints manually via console
flash undeploy --cleanup-stale
```

**Bulk Cleanup:**
```bash
# Remove everything for fresh start
flash undeploy --all --force
```

### Safety Features

**Confirmation Prompts:**
- Single endpoint: Shows endpoint details, asks confirmation
- Multiple endpoints: Shows count and list, asks confirmation
- Can be bypassed with `--force` flag

**Stale Detection:**
- Checks endpoint status on Runpod before deletion
- Identifies endpoints deleted externally
- Prevents errors from trying to delete non-existent endpoints

**Rollback Not Possible:**
- Undeployment is permanent
- Must redeploy with `flash deploy` to restore
- Ensure you have source code and can rebuild

### Common Issues

**Endpoint Not Found Locally**

Problem:
```
Error: Endpoint 'my-api' not found in tracking
```

Solutions:
```bash
# List endpoints
flash undeploy list

# Check spelling
flash undeploy my-api-gpu  # Note: exact name required

# If deleted externally, cleanup
flash undeploy --cleanup-stale
```

**Endpoint Already Deleted**

Problem:
```
Warning: Endpoint 'my-api' not found on Runpod (may be deleted)
Remove from tracking anyway? [y/N]:
```

Solution:
```bash
# Confirm to remove from tracking
y

# Or cleanup all stale at once
flash undeploy --cleanup-stale
```

**Deletion Failed**

Problem:
```
Error: Failed to delete endpoint: Insufficient permissions
```

Solutions:
```bash
# Check API key permissions
# Generate new key at https://runpod.io/console/user/settings

# Verify API key
echo $RUNPOD_API_KEY

# Try again
flash undeploy my-api
```

**Cannot Delete While Processing Requests**

Problem:
```
Error: Endpoint has active requests. Wait or force deletion.
```

Solutions:
```bash
# Wait for requests to complete
# Check Runpod console for request status

# Or force deletion (requests will be terminated)
flash undeploy my-api --force
```

### Post-Undeployment

**Verify Deletion:**
```bash
# List remaining endpoints
flash undeploy list

# Check specific environment
flash env get production

# Verify on Runpod console
# https://runpod.io/console/serverless
```

**Redeploy if Needed:**
```bash
# Undeploy was a mistake? Redeploy:
flash deploy --env production
```

### Related Commands

- [`flash deploy`](#flash-deploy) - Deploy endpoints
- [`flash env`](#flash-env) - Manage environments
- [`flash env delete`](#flash-env-delete) - Delete environment and all its endpoints

### Related Workflows

- [Cleanup and Maintenance](workflows.md#cleanup-and-maintenance)
- [Environment Management](workflows.md#multi-environment-management)

---

## flash env

Manage deployment environments. Environments represent isolated deployment targets (dev, staging, production) with their own endpoints and configurations.

### Subcommands

- `flash env list` - Show all environments
- `flash env create` - Create new environment
- `flash env get` - Show environment details
- `flash env delete` - Delete environment and all its endpoints

See individual subcommand sections for detailed documentation.

---

## flash env list

Show all available deployment environments across all Flash apps.

### Synopsis

```bash
flash env list [OPTIONS]
```

### Options

**`--app`, `-a`**
- Type: String
- Default: Show all apps
- Description: Filter environments by Flash app name.

### Examples

**List All Environments:**
```bash
flash env list
```

Output:
```
Environments:
┌────────────────┬─────────────────┬───────────────┬────────────────┐
│ Name           │ App             │ Endpoints     │ Status         │
├────────────────┼─────────────────┼───────────────┼────────────────┤
│ dev            │ my-app          │ 3             │ Active         │
│ staging        │ my-app          │ 2             │ Active         │
│ production     │ my-app          │ 4             │ Active         │
│ dev            │ other-app       │ 1             │ Idle           │
└────────────────┴─────────────────┴───────────────┴────────────────┘

Total: 4 environments across 2 apps
```

**Filter by App:**
```bash
flash env list --app my-app
```

Output:
```
Environments in 'my-app':
┌────────────────┬───────────────┬────────────────┐
│ Name           │ Endpoints     │ Status         │
├────────────────┼───────────────┼────────────────┤
│ dev            │ 3             │ Active         │
│ staging        │ 2             │ Active         │
│ production     │ 4             │ Active         │
└────────────────┴───────────────┴────────────────┘

Total: 3 environments
```

### Related Commands

- [`flash env create`](#flash-env-create) - Create new environment
- [`flash env get`](#flash-env-get) - View environment details
- [`flash deploy`](#flash-deploy) - Deploy to environment

---

## flash env create

Create a new deployment environment in a Flash app.

### Synopsis

```bash
flash env create NAME [OPTIONS]
```

### Arguments

**`NAME`** (required)
- Type: String
- Description: Name for the new environment (e.g., `dev`, `staging`, `production`)

### Options

**`--app`, `-a`**
- Type: String
- Default: Current app context
- Description: Flash app name to create environment in

### Examples

**Create Environment:**
```bash
flash env create dev
```

Output:
```
Creating environment 'dev'...
✓ Environment created successfully

Deploy to this environment:
  flash deploy --env dev
```

**Create in Specific App:**
```bash
flash env create production --app my-app
```

**Create Multiple Environments:**
```bash
flash env create dev
flash env create staging
flash env create production
```

### What It Creates

- Environment entry in Flash configuration
- Namespace for deploying endpoints
- Isolated resource group

### Naming Conventions

**Common environment names:**
- `dev`, `development` - Local or shared development
- `staging`, `stage` - Pre-production testing
- `prod`, `production` - Live production
- `test`, `testing` - Automated testing
- `preview` - Temporary preview deployments

**Best practices:**
- Use lowercase names
- Avoid spaces (use hyphens or underscores)
- Keep names short and descriptive
- Match your CI/CD pipeline stages

### Common Issues

**Environment Already Exists:**

Problem:
```
Error: Environment 'dev' already exists
```

Solution:
```bash
# List environments
flash env list

# Use different name or delete existing
flash env delete dev
flash env create dev
```

### Related Commands

- [`flash deploy`](#flash-deploy) - Deploy to environment
- [`flash env list`](#flash-env-list) - List environments
- [`flash env delete`](#flash-env-delete) - Delete environment

---

## flash env get

Show detailed information about a specific deployment environment.

### Synopsis

```bash
flash env get ENV_NAME [OPTIONS]
```

### Arguments

**`ENV_NAME`** (required)
- Type: String
- Description: Name of environment to inspect

### Options

**`--app`, `-a`**
- Type: String
- Default: Current app context
- Description: Flash app name

### Examples

**Get Environment Details:**
```bash
flash env get production
```

Output:
```
Environment: production
App: my-app
Status: Active
Created: 2024-01-15 10:30:00

Endpoints (4):
┌──────────────────────────┬─────────────────────┬────────────┬──────────────┐
│ Name                     │ Type                │ Status     │ Workers      │
├──────────────────────────┼─────────────────────┼────────────┼──────────────┤
│ my-api-gpu               │ LiveServerless      │ Active     │ 0/3          │
│ my-api-mothership        │ LiveLoadBalancer    │ Active     │ 1/3          │
│ batch-processor          │ LiveServerless      │ Idle       │ 0/5          │
│ image-worker             │ LiveServerless      │ Active     │ 2/3          │
└──────────────────────────┴─────────────────────┴────────────┴──────────────┘

Resource Configuration:
  GPU Types: A100, RTX_4090
  CPU Workers: 2 endpoints
  Total Workers: 3 active, 0-14 range

Recent Deployments:
  2024-01-20 14:15 - Updated my-api-gpu
  2024-01-19 10:00 - Created batch-processor
  2024-01-15 10:30 - Initial deployment

Endpoint URLs:
  my-api-gpu: https://abcd1234-my-api-gpu.runpod.io
  my-api-mothership: https://efgh5678-my-api-mothership.runpod.io
  batch-processor: https://ijkl9012-batch-processor.runpod.io
  image-worker: https://mnop3456-image-worker.runpod.io
```

**Get in Specific App:**
```bash
flash env get staging --app my-app
```

### Use Cases

**Check deployment status:**
```bash
flash env get production
# See which endpoints are active
```

**Get endpoint URLs:**
```bash
flash env get production | grep "https://"
```

**Monitor worker scaling:**
```bash
flash env get production
# Check "Workers" column for current/max values
```

### Related Commands

- [`flash env list`](#flash-env-list) - List all environments
- [`flash deploy`](#flash-deploy) - Deploy to environment
- [`flash undeploy`](#flash-undeploy) - Remove endpoints

---

## flash env delete

Delete a deployment environment and all its endpoints permanently.

### Synopsis

```bash
flash env delete ENV_NAME [OPTIONS]
```

### Arguments

**`ENV_NAME`** (required)
- Type: String
- Description: Name of environment to delete

### Options

**`--app`, `-a`**
- Type: String
- Default: Current app context
- Description: Flash app name

### Examples

**Delete Environment:**
```bash
flash env delete staging
```

Output:
```
Environment: staging
App: my-app
Endpoints: 3

This will permanently delete:
  - staging environment configuration
  - All 3 endpoints in this environment
  - All endpoint data and metrics

This action cannot be undone.
Continue? [y/N]: y

Deleting endpoints...
  my-api-gpu ✓
  my-api-worker ✓
  batch-processor ✓

Removing environment configuration... ✓

Environment 'staging' deleted successfully.
```

**Delete in Specific App:**
```bash
flash env delete production --app old-app
```

### What Gets Deleted

**On Runpod:**
- All serverless endpoints in environment
- Endpoint configurations and autoscaling settings
- Running worker instances
- Endpoint metrics (after retention period)

**Locally:**
- Environment configuration
- All endpoint tracking files for this environment

**Not Deleted:**
- Source code
- Build artifacts
- Other environments
- Flash app (unless this was the last environment)

### Safety Warnings

**Confirmation Required:**
Shows endpoint count and asks for explicit confirmation before deletion.

**Production Protection:**
Deleting production is risky. Consider:
```bash
# Safer: Undeploy endpoints individually first
flash undeploy --interactive
# Then delete empty environment
flash env delete production
```

**No Rollback:**
Deletion is permanent. Must redeploy to restore:
```bash
# After accidental deletion
flash env create production
flash deploy --env production
```

### Common Issues

**Environment Not Found:**

Problem:
```
Error: Environment 'staging' not found
```

Solution:
```bash
# List available environments
flash env list

# Check spelling and app context
flash env list --app my-app
```

**Endpoints Still Active:**

Problem:
```
Warning: Environment has 3 active endpoints with running requests
Continue anyway? [y/N]:
```

Solutions:
```bash
# Wait for requests to complete
# Check Runpod console

# Or confirm to force deletion (terminates requests)
y
```

### Related Commands

- [`flash env create`](#flash-env-create) - Create environment
- [`flash undeploy`](#flash-undeploy) - Delete individual endpoints
- [`flash deploy`](#flash-deploy) - Redeploy after deletion

---

## flash app

Manage Flash applications. Apps provide namespace isolation for organizing multiple projects, teams, or deployment groups.

### Subcommands

- `flash app list` - Show all apps
- `flash app create` - Create new app
- `flash app get` - Show app details
- `flash app delete` - Delete app and all resources

See individual subcommand sections for detailed documentation.

---

## flash app list

List all Flash applications under your Runpod account.

### Synopsis

```bash
flash app list
```

### Examples

```bash
flash app list
```

Output:
```
Flash Apps:
┌────────────────────┬─────────────────┬───────────────┬────────────────┐
│ Name               │ Environments    │ Endpoints     │ Status         │
├────────────────────┼─────────────────┼───────────────┼────────────────┤
│ my-api             │ 3               │ 9             │ Active         │
│ batch-processing   │ 2               │ 4             │ Active         │
│ ml-inference       │ 1               │ 2             │ Idle           │
│ legacy-app         │ 0               │ 0             │ Empty          │
└────────────────────┴─────────────────┴───────────────┴────────────────┘

Total: 4 apps, 6 environments, 15 endpoints
```

### Related Commands

- [`flash app create`](#flash-app-create) - Create new app
- [`flash app get`](#flash-app-get) - View app details

---

## flash app create

Create a new Flash application namespace.

### Synopsis

```bash
flash app create APP_NAME
```

### Arguments

**`APP_NAME`** (required)
- Type: String
- Description: Name for the new Flash app

### Examples

**Create App:**
```bash
flash app create my-new-app
```

Output:
```
Creating Flash app 'my-new-app'...
✓ App created successfully

Next steps:
  1. Create an environment:
     flash env create dev --app my-new-app

  2. Deploy your application:
     flash deploy --app my-new-app --env dev
```

### Use Cases

**Organize by Project:**
```bash
flash app create api-v1
flash app create api-v2
flash app create mobile-backend
```

**Team Isolation:**
```bash
flash app create team-alpha
flash app create team-beta
```

**Client Separation:**
```bash
flash app create client-acme
flash app create client-globex
```

### Related Commands

- [`flash env create`](#flash-env-create) - Create environment in app
- [`flash deploy`](#flash-deploy) - Deploy to app
- [`flash app list`](#flash-app-list) - List apps

---

## flash app get

Get detailed information about a Flash application.

### Synopsis

```bash
flash app get APP_NAME
```

### Arguments

**`APP_NAME`** (required)
- Type: String
- Description: Name of app to inspect

### Examples

```bash
flash app get my-app
```

Output:
```
Flash App: my-app
Status: Active
Created: 2024-01-10 09:00:00

Environments (3):
┌────────────────┬───────────────┬────────────────┐
│ Name           │ Endpoints     │ Status         │
├────────────────┼───────────────┼────────────────┤
│ dev            │ 3             │ Active         │
│ staging        │ 2             │ Active         │
│ production     │ 4             │ Active         │
└────────────────┴───────────────┴────────────────┘

Total Endpoints: 9
Active Workers: 12
Resource Usage:
  GPU: 8 workers (A100, RTX_4090)
  CPU: 4 workers

Recent Activity:
  2024-01-20 14:15 - Deployed to production
  2024-01-19 10:00 - Created staging environment
  2024-01-15 16:30 - Updated dev deployment
```

### Related Commands

- [`flash env get`](#flash-env-get) - Environment details
- [`flash app list`](#flash-app-list) - List all apps

---

## flash app delete

Delete a Flash app and all associated environments and endpoints.

### Synopsis

```bash
flash app delete [OPTIONS]
```

### Options

**`--app`, `-a`** (required)
- Type: String
- Description: Flash app name to delete

### Examples

**Delete App:**
```bash
flash app delete --app my-old-app
```

Output:
```
Flash App: my-old-app
Environments: 2
Total Endpoints: 5

This will permanently delete:
  - Flash app 'my-old-app'
  - 2 environments (dev, staging)
  - All 5 endpoints
  - All configurations and data

This action cannot be undone.
Type app name to confirm: my-old-app

Deleting endpoints...
  dev (3 endpoints) ✓
  staging (2 endpoints) ✓

Deleting environments...
  dev ✓
  staging ✓

Deleting app configuration... ✓

Flash app 'my-old-app' deleted successfully.
```

### Safety Warnings

**Confirmation Required:**
Must type exact app name to confirm deletion.

**Complete Deletion:**
Removes everything:
- All environments
- All endpoints
- All tracking data
- App configuration

**No Rollback:**
Cannot undo. Must recreate and redeploy:
```bash
flash app create my-app
flash env create production --app my-app
flash deploy --app my-app --env production
```

### Related Commands

- [`flash env delete`](#flash-env-delete) - Delete individual environment
- [`flash undeploy`](#flash-undeploy) - Delete individual endpoints

---

## See Also

- [Getting Started Guide](getting-started.md) - First Flash project tutorial
- [Workflows Guide](workflows.md) - Common development workflows
- [Troubleshooting Guide](troubleshooting.md) - Solutions to common problems
- [CLI Reference](../CLI-REFERENCE.md) - Quick reference for all commands
