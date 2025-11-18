# PATH Cleanup Script
# Purpose: Remove duplicate and non-existent paths from User PATH
# IMPORTANT: Creates backup before making changes

Write-Host "=== PATH Cleanup Utility ===" -ForegroundColor Cyan
Write-Host ""

# Create backup first
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$backupDir = "E:\_OneOffs\VSCodePiloter\diagnostics"
$backupFile = "$backupDir\path_backup_before_cleanup_$timestamp.txt"

$currentUserPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
$currentSystemPath = [Environment]::GetEnvironmentVariable('PATH', 'Machine')

"[USER PATH]`n$currentUserPath`n`n[SYSTEM PATH]`n$currentSystemPath" | Out-File $backupFile -Encoding UTF8

Write-Host "[1] Backup created: $backupFile" -ForegroundColor Green
Write-Host ""

# Analyze User PATH
Write-Host "[2] Analyzing User PATH..." -ForegroundColor Yellow
$pathEntries = $currentUserPath -split ';' | Where-Object { $_ }  # Remove empty entries

Write-Host "  Current entries: $($pathEntries.Count)" -ForegroundColor Gray
Write-Host "  Current length: $($currentUserPath.Length) characters" -ForegroundColor Gray

# Find duplicates
Write-Host "`n[3] Finding duplicates..." -ForegroundColor Yellow
$seen = @{}
$duplicates = @()

foreach ($entry in $pathEntries) {
    $normalized = $entry.Trim().ToLower()
    if ($seen.ContainsKey($normalized)) {
        $duplicates += $entry
        Write-Host "  [DUPLICATE] $entry" -ForegroundColor Red
    } else {
        $seen[$normalized] = $true
    }
}

if ($duplicates.Count -gt 0) {
    Write-Host "  Found $($duplicates.Count) duplicate entries" -ForegroundColor Red
} else {
    Write-Host "  No duplicates found" -ForegroundColor Green
}

# Find non-existent paths
Write-Host "`n[4] Checking for non-existent paths..." -ForegroundColor Yellow
$nonExistent = @()

foreach ($entry in $pathEntries) {
    # Expand environment variables
    $expanded = [Environment]::ExpandEnvironmentVariables($entry)

    # Skip unexpanded variables (like %SystemRoot% - these are intentional)
    if ($expanded -like '*%*%*') {
        continue
    }

    if (-not (Test-Path $expanded -ErrorAction SilentlyContinue)) {
        $nonExistent += $entry
        Write-Host "  [NOT FOUND] $entry" -ForegroundColor Yellow
    }
}

if ($nonExistent.Count -gt 0) {
    Write-Host "  Found $($nonExistent.Count) non-existent paths" -ForegroundColor Yellow
} else {
    Write-Host "  All paths exist" -ForegroundColor Green
}

# Show recommendations
Write-Host "`n[5] Recommendations:" -ForegroundColor Cyan

$shouldClean = $false

if ($duplicates.Count -gt 0) {
    Write-Host "  - Remove $($duplicates.Count) duplicate entries" -ForegroundColor Yellow
    $shouldClean = $true
}

if ($nonExistent.Count -gt 0) {
    Write-Host "  - Remove $($nonExistent.Count) non-existent paths" -ForegroundColor Yellow
    $shouldClean = $true
}

if ($currentUserPath.Length -gt 2048) {
    Write-Host "  - PATH exceeds 2048 character limit! ($($currentUserPath.Length) chars)" -ForegroundColor Red
    $shouldClean = $true
}

if (-not $shouldClean) {
    Write-Host "  ✓ Your PATH is clean! No action needed." -ForegroundColor Green
    exit 0
}

# Ask user if they want to proceed
Write-Host ""
Write-Host "=== CLEANUP OPTIONS ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script can automatically:" -ForegroundColor Yellow
Write-Host "  1. Remove duplicate entries"
Write-Host "  2. Remove non-existent paths"
Write-Host "  3. Preserve order of first occurrence"
Write-Host "  4. Create restoration script"
Write-Host ""

$response = Read-Host "Proceed with cleanup? (yes/no)"

if ($response -ne 'yes') {
    Write-Host "`nCleanup cancelled. Backup saved at: $backupFile" -ForegroundColor Yellow
    exit 0
}

# Perform cleanup
Write-Host "`n[6] Cleaning PATH..." -ForegroundColor Green

$cleaned = @()
$seenClean = @{}
$removedCount = 0

foreach ($entry in $pathEntries) {
    $normalized = $entry.Trim().ToLower()
    $expanded = [Environment]::ExpandEnvironmentVariables($entry)

    # Skip if duplicate
    if ($seenClean.ContainsKey($normalized)) {
        Write-Host "  Removing duplicate: $entry" -ForegroundColor Red
        $removedCount++
        continue
    }

    # Skip if non-existent (unless it's an unexpanded variable)
    if ($expanded -notlike '*%*%*' -and -not (Test-Path $expanded -ErrorAction SilentlyContinue)) {
        Write-Host "  Removing non-existent: $entry" -ForegroundColor Yellow
        $removedCount++
        continue
    }

    # Keep this entry
    $cleaned += $entry
    $seenClean[$normalized] = $true
}

$newUserPath = $cleaned -join ';'

Write-Host ""
Write-Host "[7] Cleanup Summary:" -ForegroundColor Cyan
Write-Host "  Original entries: $($pathEntries.Count)" -ForegroundColor Gray
Write-Host "  Cleaned entries: $($cleaned.Count)" -ForegroundColor Green
Write-Host "  Removed: $removedCount" -ForegroundColor Red
Write-Host "  Original length: $($currentUserPath.Length) chars" -ForegroundColor Gray
Write-Host "  New length: $($newUserPath.Length) chars" -ForegroundColor Green
Write-Host ""

# Create restoration script
$restoreScript = "$backupDir\restore_path_$timestamp.ps1"
@"
# PATH Restoration Script
# Created: $timestamp
# Restores PATH to state before cleanup

[Environment]::SetEnvironmentVariable("PATH", "$currentUserPath", "User")
Write-Host "PATH restored to pre-cleanup state" -ForegroundColor Green
Write-Host "Please restart your terminal/IDE for changes to take effect" -ForegroundColor Yellow
"@ | Out-File $restoreScript -Encoding UTF8

Write-Host "[8] Restoration script created: $restoreScript" -ForegroundColor Green
Write-Host ""

# Apply changes
$confirm = Read-Host "Apply these changes to your User PATH? (yes/no)"

if ($confirm -eq 'yes') {
    try {
        [Environment]::SetEnvironmentVariable("PATH", $newUserPath, "User")

        Write-Host ""
        Write-Host "✓ PATH updated successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "IMPORTANT: You must restart your applications for changes to take effect:" -ForegroundColor Yellow
        Write-Host "  - VS Code: Close and reopen"
        Write-Host "  - Terminal: Close and reopen"
        Write-Host "  - Or run: refreshenv (if using Chocolatey)"
        Write-Host ""
        Write-Host "To verify changes:" -ForegroundColor Cyan
        Write-Host "  [Environment]::GetEnvironmentVariable('PATH', 'User') -split ';' | Measure-Object"
        Write-Host ""
        Write-Host "To restore (if needed):" -ForegroundColor Cyan
        Write-Host "  powershell -ExecutionPolicy Bypass -File `"$restoreScript`""
        Write-Host ""

    } catch {
        Write-Host ""
        Write-Host "ERROR: Failed to update PATH: $_" -ForegroundColor Red
        Write-Host "Your PATH was not modified. Backup preserved at: $backupFile" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "Changes not applied. Backup saved at: $backupFile" -ForegroundColor Yellow
}
