#!/bin/bash

# Retrieve Z.ai API key from Bitwarden Secrets Manager
# This script uses the Bitwarden Secrets Manager CLI (bws) to securely retrieve
# the Z.ai API key and set it as an environment variable for the current session.
#
# Prerequisites:
# - Bitwarden Secrets Manager CLI (bws) must be installed
# - BWS_ACCESS_TOKEN environment variable must be set
# - Active subscription to Z.ai ($3/month)
#
# Usage:
#   source ./scripts/get_api_key.sh
#   (Note: Must use 'source' to export env var to parent shell)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Check if bws is installed
if ! command -v bws &> /dev/null; then
    echo -e "${RED}Error: Bitwarden Secrets Manager CLI (bws) is not installed.${NC}"
    echo -e "${YELLOW}Install it from: https://bitwarden.com/help/secrets-manager-cli/${NC}"
    return 1 2>/dev/null || exit 1
fi

# Check if BWS_ACCESS_TOKEN is set
if [ -z "$BWS_ACCESS_TOKEN" ]; then
    echo -e "${RED}Error: BWS_ACCESS_TOKEN environment variable is not set.${NC}"
    echo -e "${YELLOW}Set it with: export BWS_ACCESS_TOKEN='your-access-token'${NC}"
    echo -e "${YELLOW}Get your access token from: https://vault.bitwarden.com/#/settings/security/security-keys${NC}"
    return 1 2>/dev/null || exit 1
fi

echo -e "${CYAN}Retrieving Z.ai API key from Bitwarden Secrets Manager...${NC}"

# Retrieve the secret using bws CLI
SECRET_JSON=$(bws secret get Z_AI_API_KEY 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo -e "${RED}Error: Failed to retrieve secret.${NC}"
    echo -e "${YELLOW}Make sure the secret 'Z_AI_API_KEY' exists in your Bitwarden organization (MooseGoose).${NC}"
    echo -e "${GRAY}Error details: $SECRET_JSON${NC}"
    return 1 2>/dev/null || exit 1
fi

# Parse JSON and extract the value using jq
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is not installed (required for JSON parsing).${NC}"
    echo -e "${YELLOW}Install it with: sudo apt install jq (Debian/Ubuntu) or brew install jq (macOS)${NC}"
    return 1 2>/dev/null || exit 1
fi

API_KEY=$(echo "$SECRET_JSON" | jq -r '.value')

if [ -z "$API_KEY" ] || [ "$API_KEY" = "null" ]; then
    echo -e "${RED}Error: API key value is empty in Bitwarden secret.${NC}"
    return 1 2>/dev/null || exit 1
fi

# Export environment variable
export ZAI_API_KEY="$API_KEY"

echo -e "${GREEN}✓ Successfully retrieved Z.ai API key!${NC}"
echo -e "${GREEN}✓ ZAI_API_KEY environment variable set for current session${NC}"
echo ""
echo -e "${YELLOW}To make this permanent, add to your ~/.bashrc or ~/.zshrc:${NC}"
echo -e "${CYAN}  export ZAI_API_KEY='<your-api-key>'${NC}"
echo -e "${GRAY}  (Retrieve the current value with: printenv ZAI_API_KEY)${NC}"
echo ""
echo -e "${YELLOW}To verify in this shell, run:${NC}"
echo -e "${CYAN}  echo \$ZAI_API_KEY${NC}"

# Show key preview (first 8 characters only for security)
KEY_PREVIEW="${API_KEY:0:8}..."
echo ""
echo -e "${GRAY}API Key (preview): $KEY_PREVIEW${NC}"
