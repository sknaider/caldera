#!/bin/bash
# Secure Configuration Setup Script for Caldera
# This script helps you set up secure configuration for a new Caldera installation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Caldera Secure Configuration Setup  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if running in Caldera root directory
if [ ! -f "server.py" ]; then
    echo -e "${RED}Error: This script must be run from the Caldera root directory${NC}"
    exit 1
fi

# Step 1: Check if .env already exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file already exists${NC}"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Keeping existing .env file${NC}"
        exit 0
    fi
    mv .env .env.backup.$(date +%Y%m%d_%H%M%S)
    echo -e "${GREEN}Backed up existing .env file${NC}"
fi

# Step 2: Copy .env.example to .env
if [ ! -f ".env.example" ]; then
    echo -e "${RED}Error: .env.example not found${NC}"
    exit 1
fi

cp .env.example .env
echo -e "${GREEN}Created .env from template${NC}"

# Step 3: Generate secure keys
echo ""
echo -e "${BLUE}Generating secure keys...${NC}"

CRYPT_SALT=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
API_KEY_RED=$(python3 -c "import secrets; print(secrets.token_hex(16))")
API_KEY_BLUE=$(python3 -c "import secrets; print(secrets.token_hex(16))")

echo -e "${GREEN}✓ Generated encryption keys${NC}"

# Step 4: Prompt for environment
echo ""
echo -e "${BLUE}Select environment:${NC}"
echo "1) development"
echo "2) staging"
echo "3) production"
read -p "Enter choice [1-3] (default: 1): " env_choice

case $env_choice in
    2)
        ENVIRONMENT="staging"
        DEV_MODE="false"
        ;;
    3)
        ENVIRONMENT="production"
        DEV_MODE="false"
        ;;
    *)
        ENVIRONMENT="development"
        DEV_MODE="true"
        ;;
esac

echo -e "${GREEN}✓ Environment: $ENVIRONMENT${NC}"

# Step 5: Update .env with generated values
sed -i.bak "s/CALDERA_CRYPT_SALT=.*/CALDERA_CRYPT_SALT=$CRYPT_SALT/" .env
sed -i.bak "s/CALDERA_ENCRYPTION_KEY=.*/CALDERA_ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
sed -i.bak "s/CALDERA_API_KEY_RED=.*/CALDERA_API_KEY_RED=$API_KEY_RED/" .env
sed -i.bak "s/CALDERA_API_KEY_BLUE=.*/CALDERA_API_KEY_BLUE=$API_KEY_BLUE/" .env
sed -i.bak "s/CALDERA_ENVIRONMENT=.*/CALDERA_ENVIRONMENT=$ENVIRONMENT/" .env
sed -i.bak "s/CALDERA_DEV_MODE=.*/CALDERA_DEV_MODE=$DEV_MODE/" .env
rm .env.bak

echo -e "${GREEN}✓ Updated .env with generated keys${NC}"

# Step 6: Prompt for passwords
echo ""
echo -e "${BLUE}Set user passwords:${NC}"
echo -e "${YELLOW}(Press Enter to generate random passwords)${NC}"
echo ""

read -sp "Red team admin password: " RED_ADMIN_PWD
echo
if [ -z "$RED_ADMIN_PWD" ]; then
    RED_ADMIN_PWD=$(python3 -c "import secrets, string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for _ in range(20)))")
    echo -e "${GREEN}Generated random password${NC}"
fi

read -sp "Red team user password: " RED_PWD
echo
if [ -z "$RED_PWD" ]; then
    RED_PWD=$(python3 -c "import secrets, string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for _ in range(20)))")
    echo -e "${GREEN}Generated random password${NC}"
fi

read -sp "Blue team password: " BLUE_PWD
echo
if [ -z "$BLUE_PWD" ]; then
    BLUE_PWD=$(python3 -c "import secrets, string; chars = string.ascii_letters + string.digits + string.punctuation; print(''.join(secrets.choice(chars) for _ in range(20)))")
    echo -e "${GREEN}Generated random password${NC}"
fi

# Update passwords in .env
sed -i.bak "s|CALDERA_RED_ADMIN_PASSWORD=.*|CALDERA_RED_ADMIN_PASSWORD=$RED_ADMIN_PWD|" .env
sed -i.bak "s|CALDERA_RED_PASSWORD=.*|CALDERA_RED_PASSWORD=$RED_PWD|" .env
sed -i.bak "s|CALDERA_BLUE_PASSWORD=.*|CALDERA_BLUE_PASSWORD=$BLUE_PWD|" .env
rm .env.bak

echo -e "${GREEN}✓ Updated user passwords${NC}"

# Step 7: Set proper permissions
chmod 600 .env
echo -e "${GREEN}✓ Set .env file permissions (600)${NC}"

# Step 8: Create local.yml from example
if [ ! -f "conf/local.yml" ]; then
    if [ -f "conf/default.yml.example" ]; then
        cp conf/default.yml.example conf/local.yml
        echo -e "${GREEN}✓ Created conf/local.yml${NC}"
    fi
fi

# Step 9: Display summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT: Save these credentials securely!${NC}"
echo ""
echo "Environment: $ENVIRONMENT"
echo "API Key (Red): $API_KEY_RED"
echo "API Key (Blue): $API_KEY_BLUE"
echo ""
echo "Red Admin User: admin"
echo "Red Admin Password: $RED_ADMIN_PWD"
echo ""
echo "Red User: red"
echo "Red Password: $RED_PWD"
echo ""
echo "Blue User: blue"
echo "Blue Password: $BLUE_PWD"
echo ""
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Review and customize conf/local.yml if needed"
echo "2. Start Caldera with: python3 server.py --build"
echo "3. Access at: http://localhost:8888"
echo ""
echo -e "${YELLOW}Note: .env file is excluded from git by default${NC}"
echo -e "${YELLOW}Always use environment-specific secrets for production!${NC}"
echo ""

# Optional: Save credentials to a secure file
read -p "Save credentials to a secure file? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    CREDS_FILE="caldera_credentials_$(date +%Y%m%d_%H%M%S).txt"
    cat > $CREDS_FILE <<EOF
Caldera Credentials
Generated: $(date)
Environment: $ENVIRONMENT

API Keys:
- Red: $API_KEY_RED
- Blue: $API_KEY_BLUE

User Accounts:
- admin: $RED_ADMIN_PWD
- red: $RED_PWD
- blue: $BLUE_PWD

Encryption Keys:
- Crypt Salt: $CRYPT_SALT
- Encryption Key: $ENCRYPTION_KEY

KEEP THIS FILE SECURE!
EOF
    chmod 600 $CREDS_FILE
    echo -e "${GREEN}Credentials saved to: $CREDS_FILE${NC}"
    echo -e "${YELLOW}Store this file in a secure location and delete after saving elsewhere!${NC}"
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
