# Caldera Configuration Guide

## Overview

Caldera v5+ uses a secure configuration system based on environment variables to prevent sensitive credentials from being committed to version control.

## Quick Start

### 1. Set Up Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Generate secure secrets
python3 -m app.utility.config_security
```

### 2. Edit Configuration

Edit `.env` with your secure values:

```bash
# Open in your preferred editor
nano .env
```

### 3. Create Local Configuration

```bash
# Copy configuration template
cp conf/default.yml.example conf/local.yml
```

### 4. Start Caldera

```bash
# The application will automatically load .env and validate configuration
python3 server.py --insecure --build
```

## Environment Variables Reference

### Required Variables

These must be set for production deployments:

| Variable | Description | Example | Generation Command |
|----------|-------------|---------|-------------------|
| `CALDERA_API_KEY_RED` | Red team API key | `a1b2c3...` | `python3 -c "import secrets; print(secrets.token_hex(16))"` |
| `CALDERA_API_KEY_BLUE` | Blue team API key | `d4e5f6...` | `python3 -c "import secrets; print(secrets.token_hex(16))"` |
| `CALDERA_CRYPT_SALT` | Cryptographic salt | `abc123...` | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `CALDERA_ENCRYPTION_KEY` | Encryption key | `xyz789...` | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `CALDERA_RED_ADMIN_PASSWORD` | Red admin password | `StrongP@ss` | Use password manager |
| `CALDERA_RED_PASSWORD` | Red user password | `StrongP@ss` | Use password manager |
| `CALDERA_BLUE_PASSWORD` | Blue user password | `StrongP@ss` | Use password manager |

### Optional Variables

These are optional and depend on which features you're using:

| Variable | Description | Default |
|----------|-------------|---------|
| `CALDERA_GIST_API_KEY` | GitHub Gist API key | None |
| `CALDERA_SLACK_API_KEY` | Slack API token | None |
| `CALDERA_SLACK_BOT_ID` | Slack bot ID | None |
| `CALDERA_SLACK_CHANNEL_ID` | Slack channel ID | None |
| `CALDERA_SSH_KEY_FILE` | SSH host key file path | None |
| `CALDERA_SSH_KEY_PASSPHRASE` | SSH key passphrase | None |
| `CALDERA_SSH_USERNAME` | SSH username | `sandcat` |
| `CALDERA_SSH_PASSWORD` | SSH password | None |
| `CALDERA_FTP_USER` | FTP username | `caldera_user` |
| `CALDERA_FTP_PASSWORD` | FTP password | None |

### System Variables

| Variable | Description | Values | Default |
|----------|-------------|--------|---------|
| `CALDERA_ENVIRONMENT` | Deployment environment | `development`, `staging`, `production` | `development` |
| `CALDERA_DEV_MODE` | Development mode (disables security checks) | `true`, `false` | `false` |

## Configuration Validation

Caldera performs automatic validation on startup:

### Security Checks

1. **Default Credential Detection**: Prevents use of hardcoded defaults like `ADMIN123`
2. **Encryption Key Strength**: Ensures keys are at least 32 characters
3. **Password Strength**: Validates minimum 8 character passwords
4. **Environment Detection**: Enforces security in production mode

### Bypassing Validation (Development Only)

```bash
# Only for local development
export CALDERA_DEV_MODE=true
```

⚠️ **WARNING**: Never set `CALDERA_DEV_MODE=true` in production!

## Migration from Old Configuration

If you're upgrading from an older version that used `conf/default.yml` directly:

### Step 1: Backup Existing Configuration

```bash
cp conf/default.yml conf/default.yml.backup
```

### Step 2: Extract Secrets

Extract your custom values from `conf/default.yml.backup`:

```yaml
# Your old values
api_key_red: YOUR_OLD_RED_KEY
api_key_blue: YOUR_OLD_BLUE_KEY
encryption_key: YOUR_OLD_ENCRYPTION_KEY
# etc...
```

### Step 3: Move to Environment Variables

Create `.env` and add your values:

```bash
CALDERA_API_KEY_RED=YOUR_OLD_RED_KEY
CALDERA_API_KEY_BLUE=YOUR_OLD_BLUE_KEY
CALDERA_ENCRYPTION_KEY=YOUR_OLD_ENCRYPTION_KEY
```

### Step 4: Update Configuration File

```bash
cp conf/default.yml.example conf/local.yml
```

The new `local.yml` uses `${VAR_NAME}` syntax which automatically reads from environment.

## Docker Configuration

### Using Docker Compose

Create a `.env` file in your project root:

```bash
# .env
CALDERA_API_KEY_RED=your-key-here
CALDERA_ENCRYPTION_KEY=your-key-here
# etc...
```

Update `docker-compose.yml`:

```yaml
services:
  caldera:
    image: caldera:latest
    env_file:
      - .env
    environment:
      - CALDERA_ENVIRONMENT=production
    volumes:
      - ./conf/local.yml:/usr/src/app/conf/local.yml:ro
```

### Using Docker Secrets

For Docker Swarm:

```bash
# Create secrets
echo "your-api-key" | docker secret create caldera_api_key_red -

# docker-compose.yml
services:
  caldera:
    secrets:
      - caldera_api_key_red
    environment:
      - CALDERA_API_KEY_RED_FILE=/run/secrets/caldera_api_key_red

secrets:
  caldera_api_key_red:
    external: true
```

## Kubernetes Configuration

### Using ConfigMaps and Secrets

```bash
# Create secret
kubectl create secret generic caldera-secrets \
  --from-literal=api-key-red='your-api-key' \
  --from-literal=encryption-key='your-encryption-key'

# Create configmap
kubectl create configmap caldera-config \
  --from-file=local.yml=conf/local.yml
```

Deployment manifest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: caldera
spec:
  template:
    spec:
      containers:
      - name: caldera
        image: caldera:latest
        env:
        - name: CALDERA_API_KEY_RED
          valueFrom:
            secretKeyRef:
              name: caldera-secrets
              key: api-key-red
        - name: CALDERA_ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: caldera-secrets
              key: encryption-key
        - name: CALDERA_ENVIRONMENT
          value: "production"
        volumeMounts:
        - name: config
          mountPath: /usr/src/app/conf/local.yml
          subPath: local.yml
      volumes:
      - name: config
        configMap:
          name: caldera-config
```

## Troubleshooting

### Error: "Required environment variable X is not set"

**Solution**: Set the required variable in `.env` or your environment.

```bash
export CALDERA_API_KEY_RED="your-key-here"
```

### Error: "Production deployment detected with insecure default value"

**Solution**: You're using a default credential in production. Generate a secure value:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Error: "crypt_salt must be at least 32 characters long"

**Solution**: Generate a longer salt:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Configuration Not Loading

**Check**:
1. `.env` file exists and is readable
2. `.env` file is in the working directory
3. No syntax errors in `.env` (no spaces around `=`)
4. `conf/local.yml` exists and references variables correctly

## Best Practices

### Security

1. ✅ **Never commit `.env` to version control**
2. ✅ **Use different secrets for dev/staging/prod**
3. ✅ **Rotate secrets regularly** (every 90 days for API keys)
4. ✅ **Use strong, random values** generated cryptographically
5. ✅ **Restrict file permissions**: `chmod 600 .env`
6. ✅ **Use secret management systems** for production (Vault, etc.)

### Development

1. ✅ **Keep `.env.example` updated** with new variables
2. ✅ **Document all variables** in this guide
3. ✅ **Use `CALDERA_DEV_MODE=true`** for local development only
4. ✅ **Don't use production secrets** in development

### Operations

1. ✅ **Back up encryption keys** securely
2. ✅ **Monitor configuration changes** with audit logs
3. ✅ **Test configuration** in staging before production
4. ✅ **Have a rollback plan** for configuration changes

## Examples

### Local Development

```bash
# .env
CALDERA_ENVIRONMENT=development
CALDERA_DEV_MODE=true
CALDERA_API_KEY_RED=dev_red_key_123
CALDERA_API_KEY_BLUE=dev_blue_key_456
CALDERA_ENCRYPTION_KEY=dev_encryption_key_789
CALDERA_CRYPT_SALT=dev_crypt_salt_abc
CALDERA_RED_ADMIN_PASSWORD=admin
CALDERA_RED_PASSWORD=red
CALDERA_BLUE_PASSWORD=blue
```

### Staging Environment

```bash
# .env
CALDERA_ENVIRONMENT=staging
CALDERA_DEV_MODE=false
CALDERA_API_KEY_RED=<strong-random-key>
CALDERA_API_KEY_BLUE=<strong-random-key>
CALDERA_ENCRYPTION_KEY=<strong-random-key>
CALDERA_CRYPT_SALT=<strong-random-salt>
CALDERA_RED_ADMIN_PASSWORD=<strong-password>
CALDERA_RED_PASSWORD=<strong-password>
CALDERA_BLUE_PASSWORD=<strong-password>
```

### Production Environment

```bash
# .env
CALDERA_ENVIRONMENT=production
# CALDERA_DEV_MODE is not set (defaults to false)
CALDERA_API_KEY_RED=<strong-random-key>
CALDERA_API_KEY_BLUE=<strong-random-key>
CALDERA_ENCRYPTION_KEY=<strong-random-key>
CALDERA_CRYPT_SALT=<strong-random-salt>
CALDERA_RED_ADMIN_PASSWORD=<strong-password>
CALDERA_RED_PASSWORD=<strong-password>
CALDERA_BLUE_PASSWORD=<strong-password>

# Optional integrations
CALDERA_SLACK_API_KEY=xoxb-your-slack-token
CALDERA_SLACK_CHANNEL_ID=C0123456789
```

## Additional Resources

- [Security Deployment Guide](./SECURITY_DEPLOYMENT.md)
- [Docker Deployment](https://caldera.readthedocs.io/en/latest/Docker-deployment.html)
- [Main Documentation](https://caldera.readthedocs.io/)
