# Secure Deployment Guide for Caldera

## Table of Contents
1. [Pre-Deployment Security Checklist](#pre-deployment-security-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Secret Management](#secret-management)
4. [Network Security](#network-security)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Incident Response](#incident-response)

---

## Pre-Deployment Security Checklist

Before deploying Caldera to production, ensure all these security measures are in place:

### Critical Security Requirements

- [ ] **All default credentials have been changed**
  - No default API keys (`ADMIN123`, `BLUEADMIN123`)
  - No default passwords (`admin`, `caldera`)
  - No placeholder values (`REPLACE_WITH_RANDOM_VALUE`)

- [ ] **Strong encryption keys generated**
  - `CALDERA_CRYPT_SALT` at least 64 characters
  - `CALDERA_ENCRYPTION_KEY` at least 64 characters
  - Keys generated using cryptographically secure random number generator

- [ ] **Environment properly configured**
  - `CALDERA_ENVIRONMENT=production` set
  - `CALDERA_DEV_MODE=false` or unset
  - `.env` file contains no default values

- [ ] **Network security configured**
  - Caldera not exposed directly to internet
  - Reverse proxy (nginx/Apache) in place with SSL/TLS
  - Firewall rules restrict access to authorized networks only

- [ ] **Monitoring enabled**
  - Log aggregation configured
  - Security event monitoring active
  - Anomaly detection in place

---

## Environment Configuration

### Setting Up Environment Variables

Caldera now uses environment variables for all sensitive configuration. This prevents credentials from being committed to version control.

#### Step 1: Copy the Example Environment File

```bash
cp .env.example .env
```

#### Step 2: Generate Secure Secrets

Use the provided utility to generate cryptographically secure keys:

```bash
python3 -m app.utility.config_security
```

This will output secure values like:

```
CALDERA_CRYPT_SALT=a1b2c3d4e5f6...
CALDERA_ENCRYPTION_KEY=f6e5d4c3b2a1...
CALDERA_API_KEY_RED=9876543210...
CALDERA_API_KEY_BLUE=0123456789...
```

Or generate them manually:

```bash
# Generate encryption keys (64 characters)
python3 -c "import secrets; print('CALDERA_CRYPT_SALT=' + secrets.token_hex(32))"
python3 -c "import secrets; print('CALDERA_ENCRYPTION_KEY=' + secrets.token_hex(32))"

# Generate API keys (32 characters)
python3 -c "import secrets; print('CALDERA_API_KEY_RED=' + secrets.token_hex(16))"
python3 -c "import secrets; print('CALDERA_API_KEY_BLUE=' + secrets.token_hex(16))"

# Generate strong passwords
python3 -c "import secrets; import string; chars = string.ascii_letters + string.digits + string.punctuation; print('CALDERA_RED_ADMIN_PASSWORD=' + ''.join(secrets.choice(chars) for _ in range(20)))"
```

#### Step 3: Edit .env File

Edit `.env` and fill in all the generated values:

```bash
# CRITICAL - Use values from Step 2
CALDERA_API_KEY_BLUE=<your-generated-blue-key>
CALDERA_API_KEY_RED=<your-generated-red-key>
CALDERA_CRYPT_SALT=<your-generated-salt>
CALDERA_ENCRYPTION_KEY=<your-generated-key>

# User passwords
CALDERA_BLUE_PASSWORD=<strong-password-here>
CALDERA_RED_ADMIN_PASSWORD=<strong-password-here>
CALDERA_RED_PASSWORD=<strong-password-here>

# Environment
CALDERA_ENVIRONMENT=production
CALDERA_DEV_MODE=false
```

#### Step 4: Set Correct Permissions

```bash
# Ensure .env is only readable by the caldera user
chmod 600 .env
chown caldera:caldera .env
```

#### Step 5: Create Configuration File

Copy the example configuration:

```bash
cp conf/default.yml.example conf/local.yml
```

The `local.yml` file will automatically use environment variables. Do not modify `local.yml` with actual secrets - keep them in `.env`.

---

## Secret Management

### Production Secret Management Options

For production deployments, consider these secret management solutions:

#### Option 1: Environment Variables (Basic)

Suitable for small deployments or development:

```bash
export CALDERA_API_KEY_RED="your-secret-key"
export CALDERA_ENCRYPTION_KEY="your-encryption-key"
```

#### Option 2: Docker Secrets (Docker Swarm)

For Docker Swarm deployments:

```bash
# Create secrets
echo "your-api-key" | docker secret create caldera_api_key_red -
echo "your-encryption-key" | docker secret create caldera_encryption_key -

# Use in docker-compose.yml
secrets:
  caldera_api_key_red:
    external: true
  caldera_encryption_key:
    external: true
```

#### Option 3: Kubernetes Secrets

For Kubernetes deployments:

```bash
# Create secret
kubectl create secret generic caldera-secrets \
  --from-literal=api-key-red='your-api-key' \
  --from-literal=encryption-key='your-encryption-key'

# Reference in pod spec
env:
  - name: CALDERA_API_KEY_RED
    valueFrom:
      secretKeyRef:
        name: caldera-secrets
        key: api-key-red
```

#### Option 4: HashiCorp Vault (Enterprise)

For enterprise deployments:

```bash
# Store secrets in Vault
vault kv put secret/caldera \
  api_key_red="your-api-key" \
  encryption_key="your-encryption-key"

# Retrieve at runtime
export CALDERA_API_KEY_RED=$(vault kv get -field=api_key_red secret/caldera)
```

### Secret Rotation

Rotate secrets regularly:

1. **API Keys**: Rotate every 90 days
2. **Encryption Keys**: Rotate annually (requires data re-encryption)
3. **User Passwords**: Rotate every 60 days or after any security incident

---

## Network Security

### Recommended Network Architecture

```
Internet
    |
    v
[Firewall/WAF]
    |
    v
[Reverse Proxy - nginx/Apache with TLS]
    |
    v
[Caldera Server - Internal Network Only]
```

### Nginx Reverse Proxy Configuration

Example nginx configuration for Caldera:

```nginx
# /etc/nginx/sites-available/caldera

upstream caldera_backend {
    server 127.0.0.1:8888;
}

server {
    listen 443 ssl http2;
    server_name caldera.example.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/caldera.crt;
    ssl_certificate_key /etc/ssl/private/caldera.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256...';
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=caldera_limit:10m rate=10r/s;
    limit_req zone=caldera_limit burst=20 nodelay;

    # Logging
    access_log /var/log/nginx/caldera_access.log;
    error_log /var/log/nginx/caldera_error.log;

    location / {
        proxy_pass http://caldera_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name caldera.example.com;
    return 301 https://$server_name$request_uri;
}
```

### Firewall Rules (iptables)

```bash
# Allow SSH (change 22 if using non-standard port)
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTPS
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow from specific management network
iptables -A INPUT -s 10.0.0.0/24 -j ACCEPT

# Drop all other incoming
iptables -A INPUT -j DROP

# Allow outgoing
iptables -A OUTPUT -j ACCEPT

# Save rules
iptables-save > /etc/iptables/rules.v4
```

---

## Monitoring and Logging

### Application Logging

Configure structured logging in production:

```yaml
# conf/local.yml
logging:
  level: INFO
  format: json
  output: /var/log/caldera/app.log
  max_size: 100MB
  backup_count: 10
```

### Security Events to Monitor

Monitor these events for security incidents:

1. **Authentication Events**
   - Failed login attempts (trigger alert after 5 failures)
   - Successful logins from new IPs
   - API key usage from unexpected sources

2. **Authorization Events**
   - Permission denied errors
   - Privilege escalation attempts
   - Access to sensitive operations

3. **File Operations**
   - Unusual file uploads
   - Large file downloads
   - Path traversal attempts

4. **System Events**
   - Configuration changes
   - User creation/deletion
   - Service restarts

### Log Aggregation with ELK Stack

Example Filebeat configuration:

```yaml
# /etc/filebeat/filebeat.yml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /var/log/caldera/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "caldera-logs-%{+yyyy.MM.dd}"

setup.kibana:
  host: "localhost:5601"
```

### Alerting Rules

Example alerting with ElastAlert:

```yaml
# rules/failed_logins.yaml
name: Failed Login Attempts
type: frequency
index: caldera-logs-*
num_events: 5
timeframe:
  minutes: 5
filter:
- term:
    event_type: "authentication_failed"
alert:
- email:
    email: "security@example.com"
```

---

## Incident Response

### Incident Response Checklist

If you detect a security incident:

1. **Immediate Response**
   - [ ] Isolate affected systems
   - [ ] Disable compromised accounts
   - [ ] Rotate all API keys and passwords
   - [ ] Review access logs for timeline

2. **Investigation**
   - [ ] Identify attack vector
   - [ ] Determine scope of compromise
   - [ ] Collect forensic evidence
   - [ ] Document all findings

3. **Remediation**
   - [ ] Patch vulnerabilities
   - [ ] Remove unauthorized access
   - [ ] Restore from clean backup if needed
   - [ ] Implement additional security controls

4. **Post-Incident**
   - [ ] Conduct post-mortem
   - [ ] Update security procedures
   - [ ] Notify affected parties if required
   - [ ] Implement preventive measures

### Emergency Contacts

Document your security team contacts:

```
Security Team Lead: [NAME] - [EMAIL] - [PHONE]
On-Call Engineer: [ROTATION] - [EMAIL] - [PHONE]
Management: [NAME] - [EMAIL] - [PHONE]
Legal/Compliance: [NAME] - [EMAIL] - [PHONE]
```

### Backup and Recovery

Regular backup schedule:

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backup/caldera/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup database
sqlite3 /opt/caldera/data/core.db ".backup '$BACKUP_DIR/core.db'"

# Backup configuration
tar -czf "$BACKUP_DIR/config.tar.gz" /opt/caldera/conf/

# Backup data directory
tar -czf "$BACKUP_DIR/data.tar.gz" /opt/caldera/data/

# Encrypt backups
gpg --encrypt --recipient backup@example.com "$BACKUP_DIR/"*

# Upload to remote storage
aws s3 sync "$BACKUP_DIR" "s3://caldera-backups/$(date +%Y%m%d)/"

# Cleanup old backups (keep 30 days)
find /backup/caldera -type d -mtime +30 -exec rm -rf {} \;
```

---

## Security Best Practices Summary

1. **Never use default credentials** in production
2. **Generate strong, random secrets** for all keys and passwords
3. **Use environment variables** for secret management
4. **Enable HTTPS/TLS** for all connections
5. **Implement network segmentation** and firewall rules
6. **Monitor and log** all security-relevant events
7. **Rotate secrets** regularly
8. **Keep software updated** with security patches
9. **Perform regular security audits** and penetration tests
10. **Have an incident response plan** ready

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Caldera Official Documentation](https://caldera.readthedocs.io/)

---

**Last Updated**: 2025-11-16
**Review Schedule**: Quarterly
**Next Review**: 2025-02-16
