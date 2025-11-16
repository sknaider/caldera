# Caldera Security Upgrade Guide

## Overview

This guide helps you upgrade your Caldera installation to use the new secure configuration system with environment variables and enhanced security features.

## What's New

### Security Improvements

1. **Environment Variable Configuration**: All secrets now use environment variables
2. **Configuration Validation**: Automatic security checks prevent weak credentials
3. **Type Checking**: mypy integration for better code quality
4. **Enhanced Testing**: New security test suite
5. **Code Quality Tools**: black, isort, and stricter flake8 rules
6. **Better Coverage**: Coverage reporting with minimum thresholds

### Breaking Changes

⚠️ **Important**: The configuration system has changed. You must migrate your existing configuration.

## Quick Upgrade (Automated)

### For New Installations

```bash
# Run the automated setup script
./scripts/setup_secure_config.sh
```

This will:
- Generate secure random keys
- Create .env file with all required variables
- Set up conf/local.yml
- Configure proper file permissions

### For Existing Installations

#### Step 1: Backup Your Current Configuration

```bash
# Backup existing config
cp conf/default.yml conf/default.yml.backup
cp conf/local.yml conf/local.yml.backup 2>/dev/null || true
```

#### Step 2: Extract Your Current Secrets

Open `conf/default.yml.backup` and note your current values:
- api_key_red
- api_key_blue
- encryption_key
- crypt_salt
- User passwords

#### Step 3: Run Migration

```bash
# Create .env from example
cp .env.example .env

# Edit .env and add your existing values
nano .env
```

Add your backed-up values:

```bash
CALDERA_API_KEY_RED=<your_existing_red_key>
CALDERA_API_KEY_BLUE=<your_existing_blue_key>
CALDERA_ENCRYPTION_KEY=<your_existing_encryption_key>
CALDERA_CRYPT_SALT=<your_existing_crypt_salt>
CALDERA_RED_ADMIN_PASSWORD=<your_existing_admin_password>
CALDERA_RED_PASSWORD=<your_existing_red_password>
CALDERA_BLUE_PASSWORD=<your_existing_blue_password>
CALDERA_ENVIRONMENT=production
CALDERA_DEV_MODE=false
```

#### Step 4: Update Configuration Files

```bash
# Create new local.yml from example
cp conf/default.yml.example conf/local.yml
```

#### Step 5: Set Proper Permissions

```bash
chmod 600 .env
```

#### Step 6: Test Configuration

```bash
# Test that configuration loads correctly
python3 -c "from app.utility.config_security import load_env_file; load_env_file('.env'); print('✓ .env loaded successfully')"

# Run a quick validation
python3 -m app.utility.config_security
```

## Manual Upgrade (Step by Step)

### 1. Update Dependencies

```bash
# Update development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 2. Generate New Secrets (If Needed)

If you need to generate new secrets:

```bash
python3 -m app.utility.config_security
```

This outputs secure random values you can use.

### 3. Configure Environment

Create `.env` file:

```bash
# Required - Security Critical
CALDERA_API_KEY_RED=<generate-with-secrets.token_hex(16)>
CALDERA_API_KEY_BLUE=<generate-with-secrets.token_hex(16)>
CALDERA_CRYPT_SALT=<generate-with-secrets.token_hex(32)>
CALDERA_ENCRYPTION_KEY=<generate-with-secrets.token_hex(32)>

# Required - User Credentials
CALDERA_RED_ADMIN_PASSWORD=<strong-password>
CALDERA_RED_PASSWORD=<strong-password>
CALDERA_BLUE_PASSWORD=<strong-password>

# Environment Settings
CALDERA_ENVIRONMENT=production
CALDERA_DEV_MODE=false
```

### 4. Update Pre-commit Hooks

```bash
# Update pre-commit to latest versions
pre-commit autoupdate

# Run on all files to check
pre-commit run --all-files
```

### 5. Run Tests

```bash
# Run new security tests
pytest tests/security/ -v

# Run full test suite
tox -e py310

# Check coverage
tox -e coverage
```

### 6. Code Quality Checks

```bash
# Run type checking
tox -e mypy

# Run style checks
tox -e style

# Run security checks
tox -e bandit
tox -e safety
```

## Verification Checklist

After upgrading, verify everything works:

- [ ] `.env` file exists and has proper permissions (600)
- [ ] `conf/local.yml` exists
- [ ] No secrets in `conf/local.yml` (only `${VAR}` references)
- [ ] Can start server: `python3 server.py --build`
- [ ] Can login with new credentials
- [ ] All tests pass: `pytest tests/`
- [ ] No security warnings on startup
- [ ] Pre-commit hooks installed: `pre-commit run --all-files`

## Rollback (If Needed)

If you encounter issues:

### Option 1: Use Backup Configuration

```bash
# Restore old configuration
cp conf/default.yml.backup conf/default.yml
cp conf/local.yml.backup conf/local.yml

# Start with insecure flag temporarily
python3 server.py --insecure --build
```

### Option 2: Use Development Mode

```bash
# In .env, set:
CALDERA_DEV_MODE=true

# This disables security validation temporarily
```

## Common Issues and Solutions

### Issue: "Required environment variable X is not set"

**Solution**: Add the missing variable to your `.env` file.

```bash
# Check which variables are missing
grep "CALDERA_" .env.example | grep -v "^#"
```

### Issue: "Production deployment detected with insecure default value"

**Solution**: You're using a default credential. Generate a secure one:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Issue: "ModuleNotFoundError: No module named 'app.utility.config_security'"

**Solution**: You may have an import issue. Ensure you're in the Caldera root directory:

```bash
cd /path/to/caldera
python3 server.py --build
```

### Issue: Tests failing after upgrade

**Solution**: Clear old test artifacts:

```bash
# Remove old coverage data
rm -rf .coverage .coverage.* htmlcov/

# Remove pytest cache
rm -rf .pytest_cache/

# Run tests fresh
pytest tests/ -v
```

### Issue: Import errors from circular dependencies

**Solution**: The config_security module needs to be imported in a specific order. If you see import errors, try:

```bash
# Restart Python environment
deactivate  # if using venv
source .venv/bin/activate  # reactivate
pip install -r requirements.txt  # reinstall
```

## Advanced Configuration

### Using Different Environments

Create environment-specific .env files:

```bash
# .env.development
CALDERA_ENVIRONMENT=development
CALDERA_DEV_MODE=true
# ... dev secrets ...

# .env.production
CALDERA_ENVIRONMENT=production
CALDERA_DEV_MODE=false
# ... production secrets ...
```

Load specific environment:

```bash
# Development
cp .env.development .env
python3 server.py --build

# Production
cp .env.production .env
python3 server.py
```

### Docker Deployment

Update your `docker-compose.yml`:

```yaml
services:
  caldera:
    image: caldera:latest
    env_file:
      - .env
    volumes:
      - ./conf/local.yml:/usr/src/app/conf/local.yml:ro
      - ./data:/usr/src/app/data
```

### Kubernetes Deployment

Create secrets:

```bash
kubectl create secret generic caldera-secrets \
  --from-env-file=.env
```

Reference in deployment:

```yaml
envFrom:
  - secretRef:
      name: caldera-secrets
```

## New Development Workflow

### Code Formatting

Before committing, code is automatically formatted:

```bash
# Manual formatting
black app/ tests/
isort app/ tests/

# Pre-commit does this automatically
git commit -m "your message"
```

### Type Checking

Add type hints to new code:

```python
from typing import Optional, Dict, List

def get_operation(operation_id: str) -> Optional[Operation]:
    return self.operations.get(operation_id)
```

Run type checker:

```bash
mypy app/
```

### Testing

Write security tests for new features:

```python
# tests/security/test_my_feature.py
async def test_my_feature_requires_auth():
    """Verify feature requires authentication"""
    # test code
```

Run with coverage:

```bash
pytest tests/ --cov=app --cov-report=html
```

## Additional Resources

- [Configuration Guide](docs/CONFIGURATION_GUIDE.md)
- [Security Deployment Guide](docs/SECURITY_DEPLOYMENT.md)
- [Improvement Recommendations](MEJORAS_RECOMENDADAS.md)

## Getting Help

If you encounter issues during upgrade:

1. Check the logs: `logs/caldera.log`
2. Review [Configuration Guide](docs/CONFIGURATION_GUIDE.md)
3. Open an issue on GitHub with:
   - Error message
   - Steps to reproduce
   - Environment details (OS, Python version)

## Summary of Changes

| Component | Old Behavior | New Behavior |
|-----------|-------------|--------------|
| Secrets | In `conf/default.yml` | In `.env` file |
| Config Loading | Direct YAML | Env var substitution + validation |
| Security Checks | None | Automatic on startup |
| Code Style | Line length 180 | Line length 120 + black |
| Type Checking | None | mypy configured |
| Testing | Basic | Security test suite |
| Pre-commit | Basic | Comprehensive hooks |

---

**Last Updated**: 2025-11-16
**Applies to**: Caldera v5.1.0+
