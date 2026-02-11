# Flash CLI Reference

Complete reference for the Flash command-line interface. The Flash CLI provides tools for creating, developing, building, and deploying distributed inference applications.

## Quick Navigation

- [Getting Started Guide](docs/cli/getting-started.md) - Your first Flash project in 5 minutes
- [Command Reference](docs/cli/commands.md) - Exhaustive documentation for all commands
- [Workflows](docs/cli/workflows.md) - Common development workflows
- [Troubleshooting](docs/cli/troubleshooting.md) - Solutions to common problems

## Command Overview

```bash
flash --help              # Show all available commands
flash --version           # Show Flash version
flash <command> --help    # Show help for specific command
```

### Core Commands

| Command | Purpose |
|---------|---------|
| [`flash init`](#flash-init) | Create new Flash project |
| [`flash run`](#flash-run) | Run development server |
| [`flash build`](#flash-build) | Build application package |
| [`flash deploy`](#flash-deploy) | Build and deploy application |
| [`flash undeploy`](#flash-undeploy) | Delete deployed endpoints |

### Management Commands

| Command | Purpose |
|---------|---------|
| [`flash env`](#flash-env) | Manage deployment environments |
| [`flash app`](#flash-app) | Manage Flash applications |

## Learning Path

**New to Flash?** Follow this progression:

1. **Start Here**: [Getting Started Guide](docs/cli/getting-started.md)
   - Create your first project
   - Run locally and test
   - Deploy to RunPod

2. **Deep Dive**: [Command Reference](docs/cli/commands.md)
   - Understand all options and parameters
   - Learn advanced features
   - Master build configuration

3. **Real Workflows**: [Workflows Guide](docs/cli/workflows.md)
   - Local development workflow
   - Multi-environment management
   - Testing strategies

4. **When Issues Arise**: [Troubleshooting](docs/cli/troubleshooting.md)
   - Common error solutions
   - Build size optimization
   - Deployment debugging

---

## flash init

Create a new Flash project with the correct structure and boilerplate code.

### Syntax

```bash
flash init [PROJECT_NAME] [OPTIONS]
```

### Arguments

- `PROJECT_NAME` - Name for the project directory, or `.` for current directory

### Options

| Option | Description |
|--------|-------------|
| `--force`, `-f` | Overwrite existing files without prompting |

### Examples

**Create new project in subdirectory:**
```bash
flash init my-api
cd my-api
```

**Initialize in current directory:**
```bash
mkdir my-api && cd my-api
flash init .
```

**Overwrite existing files:**
```bash
flash init my-api --force
```

### What It Creates

- `main.py` - FastAPI application entry point
- `mothership.py` - Mothership endpoint configuration
- `gpu_worker.py` - GPU worker template with `@remote` decorator
- `pyproject.toml` - Project dependencies
- `.env.example` - Environment variable template
- `.gitignore` - Git ignore patterns
- `.flashignore` - Build ignore patterns
- `README.md` - Project documentation

### Related Commands

- [`flash run`](#flash-run) - Run the initialized project locally
- [Getting Started Guide](docs/cli/getting-started.md) - Full tutorial

---

## flash run

Run the Flash development server locally with hot reloading.

### Syntax

```bash
flash run [OPTIONS]
```

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `localhost` | Host to bind to (env: `FLASH_HOST`) |
| `--port`, `-p` | `8888` | Port to bind to (env: `FLASH_PORT`) |
| `--reload` | enabled | Auto-reload on file changes (use `--no-reload` to disable) |
| `--auto-provision` | disabled | Auto-provision deployable resources on startup |

### Environment Variables

- `FLASH_HOST` - Default host (overrides default, overridden by `--host`)
- `FLASH_PORT` - Default port (overrides default, overridden by `--port`)

### Examples

**Basic local development:**
```bash
flash run
# Server runs at http://localhost:8888
# Visit http://localhost:8888/docs for Swagger UI
```

**Custom host and port:**
```bash
flash run --host 0.0.0.0 --port 3000
# Accessible from network at http://<your-ip>:3000
```

**Disable auto-reload:**
```bash
flash run --no-reload
# Useful for debugging or production-like testing
```

**Auto-provision resources:**
```bash
flash run --auto-provision
# Automatically creates RunPod endpoints on startup
```

**Using environment variables:**
```bash
export FLASH_HOST=0.0.0.0
export FLASH_PORT=9000
flash run
```

### What It Does

1. Loads `main.py` FastAPI application
2. Discovers all `@remote` decorated functions
3. Starts uvicorn development server with hot reload
4. Provides interactive API documentation at `/docs`
5. Optionally provisions remote resources if `--auto-provision` is enabled

### Testing Your Application

After starting the server, test your endpoints:

**Swagger UI (recommended):**
Visit `http://localhost:8888/docs` for interactive API testing

**curl:**
```bash
curl -X POST http://localhost:8888/your-endpoint \
  -H "Content-Type: application/json" \
  -d '{"input": "test"}'
```

### Related Commands

- [`flash init`](#flash-init) - Create a project to run
- [`flash build`](#flash-build) - Build for deployment
- [Local Development Workflow](docs/cli/workflows.md#local-development-workflow)

---

## flash build

Build the Flash application into a deployable package without deploying.

### Syntax

```bash
flash build [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--no-deps` | Skip transitive dependencies (only install direct dependencies) |
| `--output`, `-o` | Custom archive name (default: `artifact.tar.gz`) |
| `--exclude` | Comma-separated packages to exclude (e.g., `torch,torchvision`) |
| `--use-local-flash` | Bundle local `runpod_flash` source instead of PyPI version |

### Examples

**Standard build:**
```bash
flash build
# Creates artifact.tar.gz
```

**Custom archive name:**
```bash
flash build -o my-app-v1.0.tar.gz
```

**Exclude packages present in base image:**
```bash
flash build --exclude torch,torchvision,torchaudio
# Reduces archive size by excluding packages already in RunPod base images
```

**Skip transitive dependencies:**
```bash
flash build --no-deps
# Only installs packages listed in pyproject.toml, not their dependencies
```

**Development build with local Flash:**
```bash
flash build --use-local-flash
# Uses your local runpod_flash source for testing changes
```

### What It Does

1. Creates `.build/` directory (kept for inspection)
2. Installs dependencies via pip for Linux x86_64
3. Generates `flash_manifest.json` with resource configurations
4. Creates handler files for each `@remote` function
5. Packages everything into `artifact.tar.gz`
6. Reports archive size (max 500MB for deployment)

### Build Size Optimization

If your build exceeds 500MB:

1. **Identify large packages:**
```bash
du -sh .build/lib/* | sort -h | tail -10
```

2. **Exclude packages in base image:**
```bash
flash build --exclude torch,torchvision,torchaudio,transformers
```

3. **Check base image packages:**
See [Troubleshooting: Archive Size Limit](docs/cli/troubleshooting.md#archive-size-limit)

### Debugging Builds

The `.build/` directory is preserved for inspection. Check:

- `.build/lib/` - Installed dependencies
- `.build/flash_manifest.json` - Resource configurations
- `.build/handler_*.py` - Generated handlers

### Related Commands

- [`flash deploy`](#flash-deploy) - Build and deploy in one step
- [Build and Deploy Workflow](docs/cli/workflows.md#build-and-deploy-workflow)
- [Troubleshooting: Build Failures](docs/cli/troubleshooting.md#build-failures)

---

## flash deploy

Build and deploy the Flash application to RunPod in a single command.

### Syntax

```bash
flash deploy [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--env`, `-e` | Target environment name |
| `--app`, `-a` | Flash app name |
| `--preview` | Build and launch local preview instead of deploying |
| **Build Options** | (same as `flash build`) |
| `--no-deps` | Skip transitive dependencies |
| `--exclude` | Comma-separated packages to exclude |
| `--use-local-flash` | Bundle local runpod_flash source |
| `--output`, `-o` | Custom archive name |

### Environment Variables

- `RUNPOD_API_KEY` - Required for deployment (get from https://runpod.io/console/user/settings)

### Examples

**Auto-select environment:**
```bash
flash deploy
# Deploys to the only environment, or prompts if multiple exist
```

**Deploy to specific environment:**
```bash
flash deploy --env production
```

**Deploy different app:**
```bash
flash deploy --app my-app --env staging
```

**Deploy with size optimization:**
```bash
flash deploy --env prod --exclude torch,torchvision
```

**Local preview without deploying:**
```bash
flash deploy --preview
# Builds and runs in Docker locally for testing
```

### What It Does

1. Runs `flash build` with specified options
2. Validates `RUNPOD_API_KEY` environment variable
3. Selects target environment (auto or via `--env`)
4. Uploads artifact to RunPod
5. Creates/updates serverless endpoints for each resource
6. Displays endpoint URLs and access information
7. Provides next steps for testing

### Environment Selection

- **One environment:** Used automatically
- **Multiple environments:** Prompts for selection (or use `--env`)
- **No environments:** Error (create with `flash env create`)

### Post-Deployment

After successful deployment:

```bash
# Test endpoints
curl -X POST https://<endpoint-id>.runpod.io/run \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"your": "data"}}'

# View deployment status
flash env get production

# Update deployment
flash deploy --env production  # Redeploy with changes
```

### Related Commands

- [`flash build`](#flash-build) - Build without deploying
- [`flash env`](#flash-env) - Manage environments
- [`flash undeploy`](#flash-undeploy) - Delete endpoints
- [Build and Deploy Workflow](docs/cli/workflows.md#build-and-deploy-workflow)

---

## flash undeploy

Delete deployed RunPod serverless endpoints.

### Syntax

```bash
flash undeploy [NAME] [OPTIONS]
```

### Arguments

- `NAME` - Endpoint name to undeploy, or `list` to show all endpoints

### Options

| Option | Description |
|--------|-------------|
| `--all` | Undeploy all endpoints (with confirmation) |
| `--interactive`, `-i` | Interactive selection with checkboxes |
| `--cleanup-stale` | Remove endpoints already deleted externally |
| `--force`, `-f` | Skip confirmation prompts |

### Examples

**List all endpoints:**
```bash
flash undeploy list
# Shows all deployed endpoints with status
```

**Undeploy specific endpoint:**
```bash
flash undeploy my-api
# Prompts for confirmation before deletion
```

**Undeploy all endpoints:**
```bash
flash undeploy --all
# Prompts for confirmation, then deletes all
```

**Force undeploy without confirmation:**
```bash
flash undeploy my-api --force
# Deletes immediately, no prompts
```

**Interactive selection:**
```bash
flash undeploy --interactive
# Shows checkbox UI to select endpoints to delete
```

**Cleanup stale tracking:**
```bash
flash undeploy --cleanup-stale
# Removes endpoints from local tracking that were deleted externally
```

### What It Does

1. Lists tracked endpoints (from `.runpod/` directory)
2. Verifies endpoints exist on RunPod
3. Prompts for confirmation (unless `--force`)
4. Deletes endpoints via RunPod API
5. Removes local tracking files

### Use Cases

**Development cleanup:**
```bash
flash undeploy --all --force
# Quick cleanup of all test deployments
```

**Selective cleanup:**
```bash
flash undeploy --interactive
# Choose which endpoints to keep/delete
```

**Fix tracking inconsistencies:**
```bash
flash undeploy --cleanup-stale
# If endpoints deleted manually via RunPod console
```

### Related Commands

- [`flash deploy`](#flash-deploy) - Deploy endpoints
- [`flash env`](#flash-env) - View environment status
- [Cleanup Workflow](docs/cli/workflows.md#cleanup-and-maintenance)

---

## flash env

Manage deployment environments. Environments represent different deployment targets (e.g., staging, production).

### Subcommands

- `flash env list` - Show all environments
- `flash env create` - Create new environment
- `flash env get` - Show environment details
- `flash env delete` - Delete environment

---

### flash env list

Show all available deployment environments.

#### Syntax

```bash
flash env list [OPTIONS]
```

#### Options

| Option | Description |
|--------|-------------|
| `--app`, `-a` | Filter by Flash app name |

#### Examples

**List all environments:**
```bash
flash env list
# Shows all environments across all apps
```

**List environments for specific app:**
```bash
flash env list --app my-app
```

---

### flash env create

Create a new deployment environment.

#### Syntax

```bash
flash env create NAME [OPTIONS]
```

#### Arguments

- `NAME` - Environment name (e.g., `staging`, `production`)

#### Options

| Option | Description |
|--------|-------------|
| `--app`, `-a` | Flash app name to create environment in |

#### Examples

**Create environment:**
```bash
flash env create staging
```

**Create environment in specific app:**
```bash
flash env create production --app my-app
```

#### What It Creates

- Environment entry in Flash configuration
- Deployment target for `flash deploy --env <name>`
- Isolated namespace for endpoints

---

### flash env get

Show detailed information about a deployment environment.

#### Syntax

```bash
flash env get ENV_NAME [OPTIONS]
```

#### Arguments

- `ENV_NAME` - Name of environment to inspect

#### Options

| Option | Description |
|--------|-------------|
| `--app`, `-a` | Flash app name |

#### Examples

**Get environment details:**
```bash
flash env get production
# Shows deployed endpoints, resource configs, status
```

**Get environment in specific app:**
```bash
flash env get staging --app my-app
```

---

### flash env delete

Delete a deployment environment and all its endpoints.

#### Syntax

```bash
flash env delete ENV_NAME [OPTIONS]
```

#### Arguments

- `ENV_NAME` - Name of environment to delete

#### Options

| Option | Description |
|--------|-------------|
| `--app`, `-a` | Flash app name |

#### Examples

**Delete environment:**
```bash
flash env delete staging
# Prompts for confirmation, deletes all endpoints in environment
```

**Delete environment in specific app:**
```bash
flash env delete production --app my-app
```

#### Warning

This deletes all endpoints in the environment. Ensure you have backups or can redeploy.

### Related Commands

- [`flash deploy`](#flash-deploy) - Deploy to environment
- [`flash undeploy`](#flash-undeploy) - Delete individual endpoints
- [Multi-Environment Workflow](docs/cli/workflows.md#multi-environment-management)

---

## flash app

Manage Flash applications. Apps provide namespace isolation for environments and endpoints.

### Subcommands

- `flash app list` - Show all apps
- `flash app create` - Create new app
- `flash app get` - Show app details
- `flash app delete` - Delete app

---

### flash app list

List all Flash applications under your account.

#### Syntax

```bash
flash app list
```

#### Examples

```bash
flash app list
# Shows all apps with environment counts
```

---

### flash app create

Create a new Flash application.

#### Syntax

```bash
flash app create APP_NAME
```

#### Arguments

- `APP_NAME` - Name for the new Flash app

#### Examples

**Create app:**
```bash
flash app create my-new-app
```

#### What It Creates

- App namespace for environments and endpoints
- Configuration entry for app-scoped operations

---

### flash app get

Get detailed information about a Flash app.

#### Syntax

```bash
flash app get APP_NAME
```

#### Arguments

- `APP_NAME` - Name of app to inspect

#### Examples

```bash
flash app get my-app
# Shows environments, endpoints, resource usage
```

---

### flash app delete

Delete a Flash app and all associated resources.

#### Syntax

```bash
flash app delete [OPTIONS]
```

#### Options

| Option | Required | Description |
|--------|----------|-------------|
| `--app`, `-a` | Yes | Flash app name to delete |

#### Examples

**Delete app:**
```bash
flash app delete --app my-app
# Prompts for confirmation, deletes all environments and endpoints
```

#### Warning

This deletes the entire app including all environments and endpoints. This operation cannot be undone.

### Related Commands

- [`flash env`](#flash-env) - Manage environments within apps
- [`flash deploy`](#flash-deploy) - Deploy to app environments

---

## Environment Variables

Flash CLI respects these environment variables:

| Variable | Purpose | Used By |
|----------|---------|---------|
| `RUNPOD_API_KEY` | RunPod API authentication | `deploy`, `undeploy`, `env`, `app` |
| `FLASH_HOST` | Default development server host | `run` |
| `FLASH_PORT` | Default development server port | `run` |

### Setting Environment Variables

**Bash/Zsh:**
```bash
export RUNPOD_API_KEY=your-key-here
export FLASH_PORT=9000
```

**.env file:**
```bash
# .env (loaded automatically by Flash)
RUNPOD_API_KEY=your-key-here
FLASH_HOST=0.0.0.0
FLASH_PORT=8888
```

## Configuration Files

Flash uses these configuration files:

| File | Purpose | Location |
|------|---------|----------|
| `.env` | Environment variables | Project root |
| `.runpod/` | Deployment tracking | Project root |
| `flash_manifest.json` | Build artifact metadata | `.build/` (auto-generated) |
| `.flashignore` | Files to exclude from build | Project root |

## Common Workflows

See the [Workflows Guide](docs/cli/workflows.md) for detailed step-by-step instructions:

- **Local Development** - Create, run, test, iterate
- **Build and Deploy** - Package and deploy to RunPod
- **Multi-Environment** - Manage staging and production
- **Testing** - Validate before production
- **Cleanup** - Remove unused resources
- **Troubleshooting** - Debug deployment issues

## Getting Help

- **Command-specific help:** `flash <command> --help`
- **Getting Started:** [docs/cli/getting-started.md](docs/cli/getting-started.md)
- **Troubleshooting:** [docs/cli/troubleshooting.md](docs/cli/troubleshooting.md)
- **Flash Documentation:** https://docs.runpod.io
- **Report Issues:** https://github.com/runpod/flash/issues

## Next Steps

1. **New to Flash?** Start with the [Getting Started Guide](docs/cli/getting-started.md)
2. **Ready to deploy?** Follow the [Build and Deploy Workflow](docs/cli/workflows.md#build-and-deploy-workflow)
3. **Need help?** Check the [Troubleshooting Guide](docs/cli/troubleshooting.md)
