# Flash CLI Troubleshooting Guide

Solutions to common Flash CLI problems organized by command and error type.

## Table of Contents

- [Installation Issues](#installation-issues)
- [flash init Problems](#flash-init-problems)
- [flash run Issues](#flash-run-issues)
- [flash build Failures](#flash-build-failures)
- [flash deploy Errors](#flash-deploy-errors)
- [Environment Management](#environment-management)
- [API Key Problems](#api-key-problems)
- [Network and Connectivity](#network-and-connectivity)

---

## Installation Issues

### Command Not Found: flash

**Problem:** Bash cannot find the `flash` command

**Symptoms:**
```bash
$ flash --version
bash: flash: command not found
```

**Solutions:**

**1. Install Flash:**
```bash
pip install runpod-flash

# Verify installation
flash --version
```

**2. Check PATH:**
```bash
# Find where flash is installed
which flash

# If not in PATH, add pip bin directory
export PATH="$PATH:$HOME/.local/bin"

# Add to shell profile for persistence
echo 'export PATH="$PATH:$HOME/.local/bin"' >> ~/.bashrc
source ~/.bashrc
```

**3. Use virtual environment:**
```bash
# Create and activate venv
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate  # Windows

# Install in venv
pip install runpod-flash
flash --version
```

**4. Check Python version:**
```bash
python --version  # Should be 3.10+

# If too old, install newer Python
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
```

**References:**
- [Getting Started Guide](getting-started.md#prerequisites)
- [Python Installation](https://www.python.org/downloads/)

### Import Error After Installation

**Problem:** Flash imports fail even after installation

**Symptoms:**
```bash
$ flash run
Traceback (most recent call last):
  ImportError: cannot import name 'remote' from 'runpod_flash'
```

**Solutions:**

**1. Reinstall Flash:**
```bash
pip uninstall runpod-flash
pip install runpod-flash

# Or upgrade to latest
pip install --upgrade runpod-flash
```

**2. Check for conflicting packages:**
```bash
pip list | grep runpod

# Uninstall all runpod packages
pip uninstall runpod runpod-flash runpod-python

# Reinstall Flash only
pip install runpod-flash
```

**3. Fresh virtual environment:**
```bash
# Remove old venv
rm -rf .venv

# Create new
python -m venv .venv
source .venv/bin/activate
pip install runpod-flash
```

**References:**
- [pip Documentation](https://pip.pypa.io/en/stable/)

---

## flash init Problems

### Directory Already Exists

**Problem:** Cannot initialize project because directory exists

**Symptoms:**
```bash
$ flash init my-api
Error: Directory 'my-api' already exists. Use --force to overwrite.
```

**Solutions:**

**1. Use different name:**
```bash
flash init my-api-v2
```

**2. Initialize in existing directory:**
```bash
cd my-api
flash init .
```

**3. Force overwrite:**
```bash
flash init my-api --force
# Warning: This overwrites existing files
```

**4. Remove existing directory:**
```bash
# Backup first if needed
mv my-api my-api.backup

# Then initialize
flash init my-api
```

**References:**
- [flash init command](commands.md#flash-init)

### Permission Denied

**Problem:** Cannot create project directory due to permissions

**Symptoms:**
```bash
$ flash init my-api
Error: Permission denied: '/path/to/directory'
```

**Solutions:**

**1. Check directory permissions:**
```bash
ls -la /path/to/directory

# Fix permissions
chmod u+w /path/to/directory
```

**2. Create in user-owned directory:**
```bash
cd ~
flash init my-api

# Or in current directory
mkdir my-api && cd my-api
flash init .
```

**3. Don't use sudo:**
```bash
# Wrong: Creates files owned by root
sudo flash init my-api

# Right: Creates files owned by you
flash init my-api
```

**References:**
- [File Permissions Guide](https://www.linux.com/training-tutorials/understanding-linux-file-permissions/)

---

## flash run Issues

### Port Already in Use

**Problem:** Cannot start server because port is occupied

**Symptoms:**
```bash
$ flash run
ERROR: [Errno 48] error while attempting to bind on address ('127.0.0.1', 8888): address already in use
```

**Solutions:**

**1. Use different port:**
```bash
flash run --port 9000
```

**2. Find and kill process using port:**
```bash
# Find process
lsof -ti:8888

# Kill process
lsof -ti:8888 | xargs kill -9

# Or manually
lsof -i:8888  # Shows PID
kill <pid>
```

**3. Use environment variable:**
```bash
export FLASH_PORT=9000
flash run
```

**References:**
- [flash run command](commands.md#flash-run)
- [Workflows: Local Development](workflows.md#local-development-workflow)

### Module Not Found Error

**Problem:** Python cannot find required modules

**Symptoms:**
```bash
$ flash run
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions:**

**1. Install dependencies:**
```bash
pip install -e .
```

**2. Check virtual environment:**
```bash
# Verify venv is activated
which python  # Should point to .venv/bin/python

# If not, activate it
source .venv/bin/activate
```

**3. Install missing package:**
```bash
pip install fastapi uvicorn
```

**4. Check pyproject.toml:**
```toml
[project]
dependencies = [
    "runpod-flash>=1.0.0",
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
]
```

**References:**
- [Python Dependencies](../CLI-REFERENCE.md#configuration-files)

### Hot Reload Not Working

**Problem:** Code changes don't trigger server restart

**Symptoms:**
- Save file
- No server restart message
- Changes not reflected in API

**Solutions:**

**1. Check reload is enabled:**
```bash
# Reload is default, but verify:
flash run  # Should show "StatReload" in output
```

**2. Manually restart:**
```bash
# Press Ctrl+C to stop
# Run again
flash run
```

**3. Check file watching:**
```bash
# Ensure files aren't ignored
cat .gitignore  # Uvicorn respects .gitignore

# Move files if needed
mv ignored_dir/worker.py workers/worker.py
```

**4. Disable and re-enable reload:**
```bash
# Try without reload
flash run --no-reload

# Then with reload
flash run
```

**References:**
- [flash run command](commands.md#flash-run)

### Cannot Access from Network

**Problem:** Server not accessible from other devices on network

**Symptoms:**
- `http://localhost:8888` works on dev machine
- `http://192.168.1.100:8888` doesn't work from phone

**Solutions:**

**1. Bind to 0.0.0.0:**
```bash
flash run --host 0.0.0.0
```

**2. Check firewall:**
```bash
# macOS: System Preferences → Security & Privacy → Firewall
# Add Python to allowed apps

# Linux (ufw):
sudo ufw allow 8888

# Linux (firewalld):
sudo firewall-cmd --add-port=8888/tcp --permanent
sudo firewall-cmd --reload
```

**3. Find your IP address:**
```bash
# macOS
ifconfig | grep "inet "

# Linux
ip addr show

# Use this IP from other devices
```

**References:**
- [flash run command](commands.md#flash-run)

---

## flash build Failures

### Archive Size Exceeds Limit

**Problem:** Build archive exceeds 500MB deployment limit

**Symptoms:**
```bash
$ flash build
ERROR: Archive size (523MB) exceeds 500MB limit
Deployment will fail. Reduce archive size.
```

**Solutions:**

**1. Identify large packages:**
```bash
# After build, check package sizes
du -sh .build/lib/* | sort -h | tail -20
```

Common large packages:
```
156M    torch
89M     torchvision
45M     transformers
23M     opencv-python
18M     scipy
```

**2. Exclude packages in base image:**
```bash
flash build --exclude torch,torchvision,torchaudio
```

**Runpod base image includes:**
- `torch`, `torchvision`, `torchaudio` (PyTorch stack)
- `transformers` (Hugging Face)
- `tensorflow`, `keras` (TensorFlow stack)
- `jax`, `jaxlib` (JAX)
- `opencv-python` (OpenCV)
- `numpy`, `scipy`, `pandas` (Scientific computing)
- `pillow` (Image processing)

Check Runpod documentation for complete list.

**3. Use --no-deps:**
```bash
flash build --no-deps --exclude torch,torchvision
```

Only installs direct dependencies, not transitive ones.

**4. Remove unnecessary dependencies:**
```toml
# Edit pyproject.toml
[project]
dependencies = [
    "runpod-flash>=1.0.0",
    # Remove packages not used at runtime:
    # "pytest",        # Testing only
    # "black",         # Development only
    # "pandas",        # If not needed for inference
]
```

Then rebuild:
```bash
flash build
```

**5. Check .flashignore:**
```bash
# Add large files not needed at runtime
echo "tests/" >> .flashignore
echo "docs/" >> .flashignore
echo "*.md" >> .flashignore
echo "data/" >> .flashignore
echo "models/*.onnx" >> .flashignore  # If using PyTorch versions
```

**Verification:**
```bash
# After changes, check size
flash build
ls -lh artifact.tar.gz
```

**References:**
- [flash build command](commands.md#flash-build)
- [Build Size Optimization](commands.md#build-size-optimization)

### Dependency Installation Failed

**Problem:** pip cannot install a required package

**Symptoms:**
```bash
$ flash build
ERROR: Could not find a version that satisfies the requirement your-package>=1.0.0
```

**Solutions:**

**1. Check package name:**
```toml
# Fix typo in pyproject.toml
[project]
dependencies = [
    "scikit-learn>=1.0.0",  # Not "sklearn"
]
```

**2. Check version constraints:**
```toml
# Relax version constraint
dependencies = [
    "your-package>=0.5.0",  # Was >=1.0.0
]
```

**3. Test installation locally:**
```bash
pip install your-package>=1.0.0

# If fails locally, won't work in build either
```

**4. Check Python version compatibility:**
```toml
# Package may require newer Python
[project]
requires-python = ">=3.10"  # Check if package needs 3.11+
```

**References:**
- [flash build command](commands.md#flash-build)
- [PyPI Package Index](https://pypi.org/)

### Manylinux Compatibility Error

**Problem:** Package has no Linux-compatible wheel

**Symptoms:**
```bash
$ flash build
ERROR: Package 'your-package' has no compatible wheels for manylinux2014_x86_64
```

**Solutions:**

**1. Find alternative package:**
```bash
# Some packages have Linux alternatives
# Example: Use 'python-magic' instead of 'pymagic'
```

**2. Build from source (if build dependencies available):**
```toml
# Some packages can build from source
# May require additional system packages in base image
```

**3. Contact package maintainer:**
- Report issue on package GitHub
- Request manylinux wheels

**4. Use pure Python alternative:**
- Find package with no C extensions
- Slower but more compatible

**References:**
- [PEP 513 - manylinux](https://www.python.org/dev/peps/pep-0513/)

### Build Fails with Import Error

**Problem:** Build process fails when importing application code

**Symptoms:**
```bash
$ flash build
ERROR: Cannot import module 'main'
ImportError: No module named 'your_dependency'
```

**Solutions:**

**1. Add missing dependency:**
```toml
[project]
dependencies = [
    "your-dependency>=1.0.0",
]
```

**2. Check circular imports:**
```python
# Avoid circular imports
# Bad: module A imports B, B imports A

# Good: Restructure to avoid cycle
```

**3. Check sys.path issues:**
```python
# Don't modify sys.path in application code
# Let Flash handle paths
```

**References:**
- [Python Import System](https://docs.python.org/3/reference/import.html)

### Permission Denied Writing to .build/

**Problem:** Cannot write to build directory

**Symptoms:**
```bash
$ flash build
ERROR: Permission denied: '.build/lib'
```

**Solutions:**

**1. Remove .build directory:**
```bash
rm -rf .build
flash build
```

**2. Fix permissions:**
```bash
chmod -R u+w .build
flash build
```

**3. Don't run with sudo:**
```bash
# Wrong: Creates root-owned files
sudo flash build

# Right:
flash build
```

**References:**
- [flash build command](commands.md#flash-build)

---

## flash deploy Errors

### Missing API Key

**Problem:** Runpod API key not configured

**Symptoms:**
```bash
$ flash deploy
Error: RUNPOD_API_KEY environment variable not set
```

**Solutions:**

**1. Set environment variable:**
```bash
export RUNPOD_API_KEY=your-key-here

# Verify
echo $RUNPOD_API_KEY
```

**2. Add to .env file:**
```bash
echo "RUNPOD_API_KEY=your-key-here" >> .env

# Flash automatically loads .env
```

**3. Get API key:**
1. Visit https://runpod.io/console/user/settings
2. Click "API Keys"
3. Create new key or copy existing
4. Set environment variable

**4. Make persistent (bash/zsh):**
```bash
echo 'export RUNPOD_API_KEY=your-key-here' >> ~/.bashrc
source ~/.bashrc
```

**References:**
- [Environment Variables](../CLI-REFERENCE.md#environment-variables)
- [Getting Started Guide](getting-started.md#configure-api-key)

### Environment Not Found

**Problem:** Specified environment doesn't exist

**Symptoms:**
```bash
$ flash deploy --env production
Error: Environment 'production' not found
```

**Solutions:**

**1. List available environments:**
```bash
flash env list
```

**2. Create environment:**
```bash
flash env create production
flash deploy --env production
```

**3. Check spelling:**
```bash
# Case-sensitive
flash deploy --env Production  # Wrong
flash deploy --env production  # Right
```

**4. Deploy without --env:**
```bash
# Auto-selects if only one environment
flash deploy
```

**References:**
- [flash env command](commands.md#flash-env)
- [Multi-Environment Management](workflows.md#multi-environment-management)

### Upload Failed

**Problem:** Cannot upload artifact to Runpod

**Symptoms:**
```bash
$ flash deploy --env production
Uploading artifact...
ERROR: Upload failed: Connection timeout
```

**Solutions:**

**1. Check internet connection:**
```bash
ping runpod.io

# Test API connectivity
curl -I https://api.runpod.io
```

**2. Retry deployment:**
```bash
flash deploy --env production
```

**3. Check firewall:**
- Ensure HTTPS outbound traffic allowed
- Check corporate firewall/proxy settings

**4. Reduce archive size:**
```bash
# Smaller files upload faster
flash deploy --env production --exclude torch,torchvision
```

**5. Check file size:**
```bash
ls -lh artifact.tar.gz
# Very large files may timeout
```

**References:**
- [flash deploy command](commands.md#flash-deploy)
- [Network and Connectivity](#network-and-connectivity)

### Endpoint Creation Failed (Insufficient GPUs)

**Problem:** Runpod has no available GPUs of requested type

**Symptoms:**
```bash
$ flash deploy --env production
Creating endpoints...
ERROR: Failed to create endpoint: Insufficient GPU availability
```

**Solutions:**

**1. Use more flexible GPU type:**
```python
# Before (specific GPU)
gpu_config = LiveServerless(
    gpus=[GpuGroup.A100]
)

# After (any GPU)
gpu_config = LiveServerless(
    gpus=[GpuGroup.ANY]
)
```

Redeploy:
```bash
flash deploy --env production
```

**2. Try different GPU type:**
```python
# More common/available GPUs
gpus=[GpuGroup.RTX_4090]
# or
gpus=[GpuGroup.RTX_3090]
```

**3. Wait and retry:**
```bash
# GPUs may become available
sleep 300  # Wait 5 minutes
flash deploy --env production
```

**4. Check Runpod status:**
- Visit https://runpod.io/console/serverless
- Check GPU availability by type

**References:**
- [flash deploy command](commands.md#flash-deploy)
- [Resource Configuration](../CLI-REFERENCE.md#flash-init)

### Authentication Failed

**Problem:** API key is invalid or lacks permissions

**Symptoms:**
```bash
$ flash deploy --env production
ERROR: Authentication failed: Invalid API key
```

**Solutions:**

**1. Verify API key:**
```bash
echo $RUNPOD_API_KEY
# Should show your key (starts with a letter, contains alphanumeric)
```

**2. Generate new key:**
1. Visit https://runpod.io/console/user/settings
2. Revoke old key
3. Create new key
4. Update environment variable

**3. Check key permissions:**
- Ensure key has serverless permissions
- Some keys are read-only

**4. Update environment variable:**
```bash
export RUNPOD_API_KEY=new-key-here
flash deploy --env production
```

**References:**
- [API Key Problems](#api-key-problems)

### Deployment Succeeds But Endpoints Don't Respond

**Problem:** Endpoints created but return errors or timeouts

**Symptoms:**
```bash
# Deployment succeeds
$ flash deploy --env production
✓ Deployment successful!

# But testing fails
$ curl -X POST https://endpoint.runpod.io/run ...
ERROR: 500 Internal Server Error
```

**Solutions:**

**1. Check Runpod console logs:**
1. Visit https://runpod.io/console/serverless
2. Click on endpoint
3. View "Logs" tab
4. Look for error messages

**2. Test with preview first:**
```bash
flash deploy --preview
# Test locally before deploying
```

**3. Common runtime errors:**

**A. Import errors:**
```
ModuleNotFoundError: No module named 'your_module'
```

Fix:
```toml
# Add to pyproject.toml
dependencies = ["your-module>=1.0.0"]
```

**B. File not found:**
```
FileNotFoundError: 'models/model.pt'
```

Fix:
```bash
# Ensure file in git
git add models/model.pt

# Or check .flashignore doesn't exclude it
```

**C. GPU not available:**
```
RuntimeError: CUDA not available
```

Fix:
```python
# Ensure GPU specified in config
gpu_config = LiveServerless(
    gpus=[GpuGroup.ANY]
)
```

**4. Redeploy after fixing:**
```bash
flash deploy --env production
```

**References:**
- [Troubleshooting Deployments](workflows.md#troubleshooting-deployments)

---

## Environment Management

### Cannot Delete Environment (Has Endpoints)

**Problem:** Environment has active endpoints and cannot be deleted

**Symptoms:**
```bash
$ flash env delete staging
Error: Environment has 3 active endpoints
Delete endpoints first or use --force
```

**Solutions:**

**1. Delete endpoints first:**
```bash
# List endpoints
flash undeploy list

# Delete individually
flash undeploy staging-endpoint-1
flash undeploy staging-endpoint-2

# Or delete all
flash undeploy --all --force

# Then delete environment
flash env delete staging
```

**2. Force delete (deletes endpoints too):**
```bash
flash env delete staging --force
```

**References:**
- [flash env command](commands.md#flash-env)
- [flash undeploy command](commands.md#flash-undeploy)

### Cannot Create Environment (Name Exists)

**Problem:** Environment name already in use

**Symptoms:**
```bash
$ flash env create production
Error: Environment 'production' already exists
```

**Solutions:**

**1. Use different name:**
```bash
flash env create production-v2
```

**2. Delete existing:**
```bash
flash env delete production
flash env create production
```

**3. Check existing environments:**
```bash
flash env list
```

**References:**
- [flash env create command](commands.md#flash-env-create)

---

## API Key Problems

### API Key Not Recognized

**Problem:** Flash cannot find or read API key

**Symptoms:**
```bash
$ flash deploy
Error: RUNPOD_API_KEY not set
```

Even after setting the variable.

**Solutions:**

**1. Check variable is exported:**
```bash
# Wrong: Not exported
RUNPOD_API_KEY=your-key

# Right: Exported
export RUNPOD_API_KEY=your-key
```

**2. Check in same terminal:**
```bash
# Set variable
export RUNPOD_API_KEY=your-key

# Use in same terminal session
flash deploy
```

**3. Use .env file:**
```bash
# Create .env in project root
echo "RUNPOD_API_KEY=your-key" > .env

# Flash automatically loads .env
flash deploy
```

**4. Check for typos:**
```bash
# Variable name is case-sensitive
RUNPOD_API_KEY  # Correct
runpod_api_key  # Wrong
Runpod_Api_Key  # Wrong
```

**References:**
- [Environment Variables](../CLI-REFERENCE.md#environment-variables)

### API Key Has Expired

**Problem:** API key no longer valid

**Symptoms:**
```bash
$ flash deploy
ERROR: Authentication failed: API key expired
```

**Solutions:**

**1. Generate new key:**
1. Visit https://runpod.io/console/user/settings
2. Revoke expired key
3. Create new key
4. Update environment variable

**2. Update in all locations:**
```bash
# Update environment variable
export RUNPOD_API_KEY=new-key

# Update .env file
echo "RUNPOD_API_KEY=new-key" > .env

# Update CI/CD secrets
# GitHub: Settings → Secrets → Update RUNPOD_API_KEY
```

**References:**
- [Runpod Console](https://runpod.io/console/user/settings)

---

## Network and Connectivity

### Cannot Reach Runpod API

**Problem:** Network cannot connect to Runpod services

**Symptoms:**
```bash
$ flash deploy
ERROR: Connection failed: Network unreachable
```

**Solutions:**

**1. Check internet connection:**
```bash
ping google.com
ping runpod.io
```

**2. Test API endpoint:**
```bash
curl -I https://api.runpod.io
# Should return 200 OK or similar
```

**3. Check firewall/proxy:**
- Ensure HTTPS (443) outbound allowed
- Check corporate proxy settings
- Try from different network (mobile hotspot)

**4. Check DNS resolution:**
```bash
nslookup runpod.io
# Should return IP address
```

**5. Try again later:**
```bash
# May be temporary network issue
sleep 60
flash deploy
```

**References:**
- [Runpod Status](https://status.runpod.io/)

### Slow Upload/Download

**Problem:** Artifact upload or deployment is very slow

**Symptoms:**
- Upload progress bar stuck at low percentage
- Deployment takes > 10 minutes

**Solutions:**

**1. Check internet speed:**
```bash
# Use speedtest-cli or online speed test
speedtest-cli

# If slow, consider:
# - Wired connection instead of WiFi
# - Different network
```

**2. Reduce archive size:**
```bash
# Smaller files upload faster
flash build --exclude torch,torchvision,torchaudio

# Check size
ls -lh artifact.tar.gz
```

**3. Try at different time:**
- Network congestion varies by time
- Try off-peak hours

**References:**
- [Build Size Optimization](#archive-size-exceeds-limit)

---

## General Debugging Tips

### Enable Verbose Logging

```bash
# Some commands support -v or --verbose
# Check command help
flash <command> --help
```

### Check Version

```bash
flash --version
# Ensure you have latest version

# Update if needed
pip install --upgrade runpod-flash
```

### Clean State

```bash
# Remove build artifacts
rm -rf .build artifact.tar.gz

# Remove cache
pip cache purge

# Fresh virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install runpod-flash
```

### Get Help

**Documentation:**
- [Getting Started Guide](getting-started.md)
- [Command Reference](commands.md)
- [Workflows Guide](workflows.md)

**Command-specific help:**
```bash
flash <command> --help
```

**Community:**
- Runpod Discord: https://discord.gg/runpod
- GitHub Issues: https://github.com/runpod/flash/issues

**Support:**
- Runpod Support: https://runpod.io/support

---

## Diagnostic Checklist

When troubleshooting any issue:

- [ ] Flash installed and in PATH (`flash --version`)
- [ ] Python version >= 3.10 (`python --version`)
- [ ] Virtual environment activated (`which python`)
- [ ] Dependencies installed (`pip list`)
- [ ] API key set (`echo $RUNPOD_API_KEY`)
- [ ] Internet connectivity (`ping runpod.io`)
- [ ] Sufficient disk space (`df -h`)
- [ ] No permission issues (`ls -la`)
- [ ] Recent Flash version (`pip install --upgrade runpod-flash`)
- [ ] Checked logs and error messages
- [ ] Tested locally first (`flash run`)
- [ ] Reviewed documentation

---

## Emergency Recovery

### Broken Production Deployment

**Immediate actions:**

```bash
# 1. Undeploy broken version
flash undeploy production-endpoint --force

# 2. Checkout last known good version
git log --oneline  # Find commit hash
git checkout <good-commit-hash>

# 3. Redeploy
flash deploy --env production

# 4. Verify
curl -X POST https://production-endpoint/run ...

# 5. Return to main branch
git checkout main

# 6. Fix issue properly
# ... make changes ...
flash run  # Test locally
flash deploy --env staging  # Test in staging
flash deploy --env production  # Redeploy to production
```

### Lost Configuration

**Recover from Runpod console:**

1. Visit https://runpod.io/console/serverless
2. Note endpoint configurations
3. Recreate local configuration
4. Redeploy to sync

### Complete Reset

**Start fresh:**

```bash
# 1. Remove all deployments
flash undeploy --all --force

# 2. Delete all environments
flash env list
flash env delete dev
flash env delete staging
flash env delete production

# 3. Clean local state
rm -rf .build artifact.tar.gz .runpod/

# 4. Fresh virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install runpod-flash

# 5. Reinstall dependencies
pip install -e .

# 6. Test locally
flash run

# 7. Redeploy
flash env create production
flash deploy --env production
```

---

## Preventive Measures

**Avoid issues before they happen:**

1. **Always test locally first:**
   ```bash
   flash run
   # Test all endpoints
   ```

2. **Use preview before deploying:**
   ```bash
   flash deploy --preview
   ```

3. **Deploy to staging first:**
   ```bash
   flash deploy --env staging
   # Test thoroughly
   flash deploy --env production
   ```

4. **Monitor builds:**
   ```bash
   # Check size after build
   flash build
   ls -lh artifact.tar.gz  # Should be < 500MB
   ```

5. **Keep dependencies minimal:**
   ```toml
   # Only include runtime dependencies
   [project]
   dependencies = [
       "runpod-flash>=1.0.0",
       # ... only what you need
   ]
   ```

6. **Document working configuration:**
   - Save working pyproject.toml
   - Note GPU types that work
   - Document exclusion patterns

7. **Use version control:**
   ```bash
   git add .
   git commit -m "Working deployment"
   # Easy to rollback if needed
   ```

8. **Regular cleanup:**
   ```bash
   # Weekly
   flash undeploy --cleanup-stale
   ```

---

## Quick Reference

**Most Common Issues:**

| Issue | Quick Fix |
|-------|-----------|
| Command not found | `pip install runpod-flash` |
| Port in use | `flash run --port 9000` |
| Build too large | `flash build --exclude torch,torchvision` |
| Missing API key | `export RUNPOD_API_KEY=your-key` |
| Environment not found | `flash env create <name>` |
| Module not found | `pip install -e .` |
| Upload failed | Retry or reduce size |
| GPU unavailable | Use `gpus=[GpuGroup.ANY]` |

**Diagnostic Commands:**

```bash
flash --version              # Check Flash version
flash <command> --help       # Command-specific help
flash env list               # List environments
flash undeploy list          # List endpoints
pip list                     # Check installed packages
echo $RUNPOD_API_KEY        # Verify API key
du -sh .build/lib/* | sort -h | tail -10  # Check package sizes
```

---

For additional help:
- [CLI Reference](../CLI-REFERENCE.md)
- [Commands Guide](commands.md)
- [Workflows Guide](workflows.md)
- [Getting Started](getting-started.md)
