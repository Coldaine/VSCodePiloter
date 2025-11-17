#!/bin/bash
# Discover Z.ai GLM models by probing the API

echo "=== Z.ai Model Discovery ==="

if [ -z "$ZAI_API_KEY" ]; then
    echo "Error: ZAI_API_KEY not set"
    echo "Run: source ./scripts/get_api_key.sh"
    exit 1
fi

BASE_URL="https://api.z.ai"

echo -e "\n[1/2] Probing for models list endpoint..."

# Try common model list endpoints
endpoints=(
    "/v1/models"
    "/api/v1/models"
    "/api/paas/v4/models"
    "/api/coding/paas/v4/models"
)

for endpoint in "${endpoints[@]}"; do
    echo -n "  Testing $endpoint ... "
    response=$(curl -s -w "\n%{http_code}" -X GET "${BASE_URL}${endpoint}" \
        -H "Authorization: Bearer $ZAI_API_KEY" 2>&1)

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        echo "✅ FOUND!"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        echo -e "\n✅ Use this endpoint to list models: ${BASE_URL}${endpoint}"
        exit 0
    elif [ "$http_code" = "404" ]; then
        echo "404 Not Found"
    else
        echo "$http_code"
    fi
done

echo -e "\n⚠️  No models list endpoint found"
echo -e "\n[2/2] Testing known model names directly..."

CHAT_ENDPOINT="${BASE_URL}/api/coding/paas/v4/chat/completions"

# Based on research: GLM-4, GLM-4V, GLM-4-AirX, etc.
models=(
    "glm-4"
    "glm-4-plus"
    "glm-4-air"
    "glm-4-airx"
    "glm-4-flash"
    "glm-4v"
    "glm-4v-plus"
    "glm-4-vision"
)

for model in "${models[@]}"; do
    printf "  %-20s" "$model:"

    response=$(curl -s -X POST "$CHAT_ENDPOINT" \
        -H "Authorization: Bearer $ZAI_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"test\"}]}" 2>&1)

    if echo "$response" | jq -e '.choices[0].message.content' &>/dev/null; then
        echo "✅ WORKS"
    else
        error=$(echo "$response" | jq -r '.error.message // .error.code // "Unknown"' 2>/dev/null)
        if [[ "$error" == *"model"* ]] || [[ "$error" == *"not found"* ]]; then
            echo "❌ Not found"
        else
            echo "⚠️  $error"
        fi
    fi
done

echo -e "\n=== Discovery Complete ==="
echo "Working models marked with ✅"
