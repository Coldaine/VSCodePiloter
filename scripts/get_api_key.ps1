<#
.SYNOPSIS
    Retrieve Z.ai API key from Bitwarden Secrets Manager
.DESCRIPTION
    This script uses the Bitwarden Secrets Manager CLI (bws) to securely retrieve
    the Z.ai API key and set it as an environment variable for the current session.
.NOTES
    Prerequisites:
    - Bitwarden Secrets Manager CLI (bws) must be installed
    - BWS_ACCESS_TOKEN environment variable must be set
    - Active subscription to Z.ai ($3/month)
.EXAMPLE
    .\scripts\get_api_key.ps1
#>

# Check if bws is installed
if (-not (Get-Command bws -ErrorAction SilentlyContinue)) {
    Write-Error "Bitwarden Secrets Manager CLI (bws) is not installed."
    Write-Host "Install it from: https://bitwarden.com/help/secrets-manager-cli/" -ForegroundColor Yellow
    exit 1
}

# Check if BWS_ACCESS_TOKEN is set
if (-not $env:BWS_ACCESS_TOKEN) {
    Write-Error "BWS_ACCESS_TOKEN environment variable is not set."
    Write-Host "Set it with: `$env:BWS_ACCESS_TOKEN = 'your-access-token'" -ForegroundColor Yellow
    Write-Host "Get your access token from: https://vault.bitwarden.com/#/settings/security/security-keys" -ForegroundColor Yellow
    exit 1
}

Write-Host "Retrieving Z.ai API key from Bitwarden Secrets Manager..." -ForegroundColor Cyan

try {
    # Retrieve the secret using bws CLI
    $secretJson = bws secret get Z_AI_API_KEY 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to retrieve secret. Error: $secretJson"
        Write-Host "Make sure the secret 'Z_AI_API_KEY' exists in your Bitwarden organization (MooseGoose)." -ForegroundColor Yellow
        exit 1
    }

    # Parse JSON and extract the value
    $secret = $secretJson | ConvertFrom-Json
    $apiKey = $secret.value

    if (-not $apiKey) {
        Write-Error "API key value is empty in Bitwarden secret."
        exit 1
    }

    # Set environment variable for current session
    $env:ZAI_API_KEY = $apiKey

    Write-Host "✓ Successfully retrieved Z.ai API key!" -ForegroundColor Green
    Write-Host "✓ ZAI_API_KEY environment variable set for current session" -ForegroundColor Green
    Write-Host ""
    Write-Host "To make this permanent, run:" -ForegroundColor Yellow
    Write-Host "  [System.Environment]::SetEnvironmentVariable('ZAI_API_KEY', '$apiKey', 'User')" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "To verify, run:" -ForegroundColor Yellow
    Write-Host "  echo `$env:ZAI_API_KEY" -ForegroundColor Cyan

    # Verify the API key works (first few characters only for security)
    $keyPreview = $apiKey.Substring(0, [Math]::Min(8, $apiKey.Length)) + "..."
    Write-Host ""
    Write-Host "API Key (preview): $keyPreview" -ForegroundColor DarkGray

} catch {
    Write-Error "An error occurred: $_"
    exit 1
}
