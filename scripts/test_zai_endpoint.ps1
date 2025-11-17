<#
.SYNOPSIS
    Test Z.ai GLM-4.6 coding endpoint
.DESCRIPTION
    This script validates that the Z.ai API endpoint is reachable and working correctly.
    Tests both temperature 0.95 (Actor default) and 0.7 (Reasoner setting).
.NOTES
    Prerequisites:
    - ZAI_API_KEY environment variable must be set
    - PowerShell 5.1 or higher
.EXAMPLE
    .\scripts\test_zai_endpoint.ps1
#>

# Configuration
$Endpoint = "https://api.z.ai/api/coding/paas/v4/chat/completions"
$Model = "glm-4.6"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Z.ai GLM-4.6 Endpoint Validation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if ZAI_API_KEY is set
if (-not $env:ZAI_API_KEY) {
    Write-Error "ZAI_API_KEY environment variable is not set."
    Write-Host "Set it with: `$env:ZAI_API_KEY = 'your-api-key'" -ForegroundColor Yellow
    Write-Host "Or use: .\scripts\get_api_key.ps1" -ForegroundColor Yellow
    exit 1
}

$ApiKey = $env:ZAI_API_KEY
$ApiKeyPreview = $ApiKey.Substring(0, 8) + "..." + $ApiKey.Substring($ApiKey.Length - 4)

Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Endpoint: $Endpoint"
Write-Host "  Model: $Model"
Write-Host "  API Key: $ApiKeyPreview"
Write-Host ""

# Helper function to test endpoint
function Test-ZaiEndpoint {
    param(
        [string]$Temperature,
        [string]$TestName
    )

    Write-Host $TestName -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor DarkGray

    $headers = @{
        "Authorization" = "Bearer $ApiKey"
        "Content-Type"  = "application/json"
    }

    $body = @{
        model       = $Model
        messages    = @(
            @{
                role    = "system"
                content = "You are a professional programming assistant"
            },
            @{
                role    = "user"
                content = "Say hello in one sentence"
            }
        )
        temperature = [double]$Temperature
    } | ConvertTo-Json -Depth 10

    try {
        $response = Invoke-RestMethod -Uri $Endpoint -Method Post -Headers $headers -Body $body -ErrorAction Stop

        Write-Host "✓ HTTP Status: 200 OK" -ForegroundColor Green

        if ($response.choices -and $response.choices[0].message.content) {
            Write-Host "✓ Response contains valid completion" -ForegroundColor Green
            Write-Host "Response:" -ForegroundColor Cyan
            $response | ConvertTo-Json -Depth 10 | Write-Host
        }
        else {
            Write-Host "✗ Response missing completion content" -ForegroundColor Red
            $response | ConvertTo-Json -Depth 10 | Write-Host
            return $false
        }

        return $true
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "✗ HTTP Status: $statusCode" -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red

        if ($_.ErrorDetails.Message) {
            Write-Host "Response:" -ForegroundColor Red
            Write-Host $_.ErrorDetails.Message
        }

        return $false
    }
}

# Test 1: Temperature 0.95 (Actor default)
$test1Success = Test-ZaiEndpoint -Temperature "0.95" -TestName "Test 1: Temperature 0.95 (Actor default)"
Write-Host ""

# Test 2: Temperature 0.7 (Reasoner setting)
$test2Success = Test-ZaiEndpoint -Temperature "0.7" -TestName "Test 2: Temperature 0.7 (Reasoner setting)"
Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
if ($test1Success -and $test2Success) {
    Write-Host "✓ All endpoint validation tests passed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Review the responses above"
    Write-Host "  2. Verify completions are coherent and relevant"
    Write-Host "  3. Document results in docs/api_validation_results.md"
    Write-Host ""
    exit 0
}
else {
    Write-Host "✗ Some tests failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "  - Verify your Z.ai subscription is active ($3/month)"
    Write-Host "  - Check that API key is correct"
    Write-Host "  - Ensure endpoint is: $Endpoint"
    Write-Host "  - Ensure model is: $Model (exact lowercase)"
    Write-Host ""
    exit 1
}
