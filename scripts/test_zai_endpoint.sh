#!/bin/bash

# Test Z.ai GLM-4.6 coding endpoint
# This script validates that the Z.ai API endpoint is reachable and working correctly.
#
# Prerequisites:
# - ZAI_API_KEY environment variable must be set
# - curl must be installed
# - jq must be installed (for JSON parsing)
#
# Usage:
#   ./scripts/test_zai_endpoint.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

# Configuration
ENDPOINT="https://api.z.ai/api/coding/paas/v4/chat/completions"
MODEL="glm-4.6"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Z.ai GLM-4.6 Endpoint Validation${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if ZAI_API_KEY is set
if [ -z "$ZAI_API_KEY" ]; then
    echo -e "${RED}Error: ZAI_API_KEY environment variable is not set.${NC}"
    echo -e "${YELLOW}Set it with: export ZAI_API_KEY='your-api-key'${NC}"
    echo -e "${YELLOW}Or use: source ./scripts/get_api_key.sh${NC}"
    exit 1
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is not installed.${NC}"
    exit 1
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq is not installed. Response will not be pretty-printed.${NC}"
    JQ_AVAILABLE=false
else
    JQ_AVAILABLE=true
fi

echo -e "${CYAN}Configuration:${NC}"
echo -e "  Endpoint: ${ENDPOINT}"
echo -e "  Model: ${MODEL}"
echo -e "  API Key: ${ZAI_API_KEY:0:8}...${ZAI_API_KEY: -4}"
echo ""

# Test 1: Temperature 0.95 (Actor default)
echo -e "${CYAN}Test 1: Temperature 0.95 (Actor default)${NC}"
echo -e "${GRAY}----------------------------------------${NC}"

RESPONSE_1=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$ENDPOINT" \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"$MODEL"'",
    "messages": [
      {"role": "system", "content": "You are a professional programming assistant"},
      {"role": "user", "content": "Say hello in one sentence"}
    ],
    "temperature": 0.95
  }')

HTTP_STATUS_1=$(echo "$RESPONSE_1" | grep "HTTP_STATUS:" | cut -d: -f2)
RESPONSE_BODY_1=$(echo "$RESPONSE_1" | sed '/HTTP_STATUS:/d')

if [ "$HTTP_STATUS_1" = "200" ]; then
    echo -e "${GREEN}✓ HTTP Status: 200 OK${NC}"

    if [ "$JQ_AVAILABLE" = true ]; then
        COMPLETION_1=$(echo "$RESPONSE_BODY_1" | jq -r '.choices[0].message.content // empty')
        if [ -n "$COMPLETION_1" ]; then
            echo -e "${GREEN}✓ Response contains valid completion${NC}"
            echo -e "${CYAN}Response:${NC}"
            echo "$RESPONSE_BODY_1" | jq '.'
        else
            echo -e "${RED}✗ Response missing completion content${NC}"
            echo "$RESPONSE_BODY_1"
        fi
    else
        echo "$RESPONSE_BODY_1"
    fi
else
    echo -e "${RED}✗ HTTP Status: $HTTP_STATUS_1${NC}"
    echo -e "${RED}Response:${NC}"
    echo "$RESPONSE_BODY_1"
    exit 1
fi

echo ""

# Test 2: Temperature 0.7 (Reasoner setting)
echo -e "${CYAN}Test 2: Temperature 0.7 (Reasoner setting)${NC}"
echo -e "${GRAY}----------------------------------------${NC}"

RESPONSE_2=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$ENDPOINT" \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'"$MODEL"'",
    "messages": [
      {"role": "system", "content": "You are a professional programming assistant"},
      {"role": "user", "content": "Say hello in one sentence"}
    ],
    "temperature": 0.7
  }')

HTTP_STATUS_2=$(echo "$RESPONSE_2" | grep "HTTP_STATUS:" | cut -d: -f2)
RESPONSE_BODY_2=$(echo "$RESPONSE_2" | sed '/HTTP_STATUS:/d')

if [ "$HTTP_STATUS_2" = "200" ]; then
    echo -e "${GREEN}✓ HTTP Status: 200 OK${NC}"

    if [ "$JQ_AVAILABLE" = true ]; then
        COMPLETION_2=$(echo "$RESPONSE_BODY_2" | jq -r '.choices[0].message.content // empty')
        if [ -n "$COMPLETION_2" ]; then
            echo -e "${GREEN}✓ Response contains valid completion${NC}"
            echo -e "${CYAN}Response:${NC}"
            echo "$RESPONSE_BODY_2" | jq '.'
        else
            echo -e "${RED}✗ Response missing completion content${NC}"
            echo "$RESPONSE_BODY_2"
        fi
    else
        echo "$RESPONSE_BODY_2"
    fi
else
    echo -e "${RED}✗ HTTP Status: $HTTP_STATUS_2${NC}"
    echo -e "${RED}Response:${NC}"
    echo "$RESPONSE_BODY_2"
    exit 1
fi

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}✓ All endpoint validation tests passed!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Review the responses above"
echo -e "  2. Verify completions are coherent and relevant"
echo -e "  3. Document results in docs/api_validation_results.md"
echo ""

exit 0
