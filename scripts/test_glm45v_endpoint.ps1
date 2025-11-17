# Test GLM-4.5V vision endpoint

Write-Host "Testing Z.ai GLM-4.5V endpoint..." -ForegroundColor Cyan

# Get API key
if ($env:ZAI_API_KEY) {
    $apiKey = $env:ZAI_API_KEY
    Write-Host "✓ Using ZAI_API_KEY from environment" -ForegroundColor Green
} elseif ($env:BWS_ACCESS_TOKEN) {
    Write-Host "Attempting to retrieve from Bitwarden..." -ForegroundColor Yellow
    $secretJson = bws secret get Z_AI_API_KEY 2>$null
    if ($LASTEXITCODE -eq 0) {
        $secret = $secretJson | ConvertFrom-Json
        $apiKey = $secret.value
        Write-Host "✓ Retrieved from Bitwarden" -ForegroundColor Green
        Write-Host "  Key preview: $($apiKey.Substring(0, [Math]::Min(12, $apiKey.Length)))..." -ForegroundColor Gray
    } else {
        Write-Host "✗ Failed to retrieve from Bitwarden" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✗ No API key found. Set ZAI_API_KEY or BWS_ACCESS_TOKEN" -ForegroundColor Red
    exit 1
}

# Test endpoints
$endpoint = "https://api.z.ai/api/coding/paas/v4/chat/completions"

Write-Host "`nTesting models..." -ForegroundColor Cyan

# Test 1: GLM-4.6 (text model - baseline)
Write-Host "`n[1/3] Testing glm-4.6 (text model)..." -ForegroundColor Yellow

$body1 = @{
    model = "glm-4.6"
    messages = @(
        @{
            role = "user"
            content = "Say 'text model works'"
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response1 = Invoke-RestMethod -Uri $endpoint -Method Post `
        -Headers @{
            "Authorization" = "Bearer $apiKey"
            "Content-Type" = "application/json"
        } `
        -Body $body1 `
        -ErrorAction Stop

    Write-Host "  ✓ GLM-4.6 works!" -ForegroundColor Green
    Write-Host "  Response: $($response1.choices[0].message.content)" -ForegroundColor Gray
} catch {
    Write-Host "  ✗ GLM-4.6 failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Test 2: GLM-4.5V (vision model - exact name)
Write-Host "`n[2/3] Testing glm-4.5v (vision model)..." -ForegroundColor Yellow

$body2 = @{
    model = "glm-4.5v"
    messages = @(
        @{
            role = "user"
            content = "Say 'vision model works'"
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $response2 = Invoke-RestMethod -Uri $endpoint -Method Post `
        -Headers @{
            "Authorization" = "Bearer $apiKey"
            "Content-Type" = "application/json"
        } `
        -Body $body2 `
        -ErrorAction Stop

    Write-Host "  ✓ GLM-4.5V works!" -ForegroundColor Green
    Write-Host "  Response: $($response2.choices[0].message.content)" -ForegroundColor Gray
    Write-Host "  Model confirmed: glm-4.5v" -ForegroundColor Cyan
} catch {
    $errorDetails = $_.ErrorDetails.Message | ConvertFrom-Json -ErrorAction SilentlyContinue
    Write-Host "  ✗ GLM-4.5V failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($errorDetails) {
        Write-Host "  Error details: $($errorDetails.error.message)" -ForegroundColor Red
    }
}

# Test 3: Alternative vision model names
Write-Host "`n[3/3] Testing alternative names..." -ForegroundColor Yellow

$alternativeNames = @("glm-4v", "glm-4-vision", "glm-4.5-vision")

foreach ($modelName in $alternativeNames) {
    Write-Host "  Testing: $modelName..." -ForegroundColor Gray

    $body = @{
        model = $modelName
        messages = @(
            @{
                role = "user"
                content = "test"
            }
        )
    } | ConvertTo-Json -Depth 10

    try {
        $response = Invoke-RestMethod -Uri $endpoint -Method Post `
            -Headers @{
                "Authorization" = "Bearer $apiKey"
                "Content-Type" = "application/json"
            } `
            -Body $body `
            -ErrorAction Stop

        Write-Host "    ✓ $modelName works!" -ForegroundColor Green
    } catch {
        Write-Host "    ✗ $modelName failed" -ForegroundColor Red
    }
}

Write-Host "`nTest complete!" -ForegroundColor Cyan
