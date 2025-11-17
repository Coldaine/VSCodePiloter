#!/bin/bash
# Test GLM-4.5V vision endpoint

echo "Testing Z.ai GLM-4.5V endpoint..."

# Get API key
if [ -z "$ZAI_API_KEY" ]; then
    echo "Error: ZAI_API_KEY not set"
    echo "Please run: export ZAI_API_KEY='your-key' or source ./scripts/get_api_key.sh"
    exit 1
fi

echo "API Key found (starts with: ${ZAI_API_KEY:0:12}...)"

ENDPOINT="https://api.z.ai/api/coding/paas/v4/chat/completions"

echo -e "\n[1/3] Testing glm-4.6 (text model - baseline)..."
curl -s -X POST "$ENDPOINT" \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.6",
    "messages": [{"role": "user", "content": "Say: text model works"}]
  }' | jq -r '.choices[0].message.content // .error.message // "Error: No response"'

echo -e "\n[2/3] Testing glm-4.5v (vision model)..."
curl -s -X POST "$ENDPOINT" \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.5v",
    "messages": [{"role": "user", "content": "Say: vision model works"}]
  }' | jq -r '.choices[0].message.content // .error.message // "Error: No response"'

echo -e "\n[3/3] Testing alternative vision model names..."
for model in "glm-4v" "glm-4-vision" "glm-4.5-vision"; do
    echo "  Testing: $model"
    response=$(curl -s -X POST "$ENDPOINT" \
      -H "Authorization: Bearer $ZAI_API_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"test\"}]}" \
      | jq -r '.choices[0].message.content // .error.message // "failed"')
    if [ "$response" != "failed" ]; then
        echo "    ✓ $model works!"
    else
        echo "    ✗ $model failed"
    fi
done

echo -e "\nTest complete!"
