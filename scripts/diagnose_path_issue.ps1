# PATH Variable Diagnostic Script
# Purpose: Investigate PATH variable loss and create backup
# Created: 2025-11-18

$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$reportDir = "E:\_OneOffs\VSCodePiloter\diagnostics"
$reportFile = "$reportDir\path_diagnostic_$timestamp.txt"

# Create diagnostics directory if it doesn't exist
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
}

Write-Host "=== PATH Variable Diagnostic Report ===" -ForegroundColor Cyan
Write-Host "Generated: $timestamp" -ForegroundColor Gray
Write-Host ""

# Function to safely get registry value
function Get-SafeRegistryValue {
    param($Path, $Name)
    try {
        return (Get-ItemProperty -Path $Path -Name $Name -ErrorAction Stop).$Name
    } catch {
        return "ERROR: Unable to read - $($_.Exception.Message)"
    }
}

# Start transcript
Start-Transcript -Path $reportFile -Append

Write-Host "`n=== CURRENT PATH SNAPSHOT ===" -ForegroundColor Yellow

# 1. Capture current User PATH
Write-Host "`n[1] User PATH (Current Process):" -ForegroundColor Green
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath) {
    $userPath -split ';' | ForEach-Object { "  $_" }
    Write-Host "  Total Entries: $(($userPath -split ';').Count)" -ForegroundColor Gray
} else {
    Write-Host "  WARNING: User PATH is empty!" -ForegroundColor Red
}

# 2. Capture current System PATH
Write-Host "`n[2] System PATH (Current Process):" -ForegroundColor Green
$systemPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
if ($systemPath) {
    $systemPath -split ';' | ForEach-Object { "  $_" }
    Write-Host "  Total Entries: $(($systemPath -split ';').Count)" -ForegroundColor Gray
} else {
    Write-Host "  WARNING: System PATH is empty!" -ForegroundColor Red
}

# 3. Capture combined PATH (what the current session sees)
Write-Host "`n[3] Combined PATH (Current Session):" -ForegroundColor Green
$env:PATH -split ';' | ForEach-Object { "  $_" }
Write-Host "  Total Entries: $(($env:PATH -split ';').Count)" -ForegroundColor Gray

# 4. Check registry directly
Write-Host "`n=== REGISTRY DIRECT CHECK ===" -ForegroundColor Yellow

Write-Host "`n[4] User PATH (Registry):" -ForegroundColor Green
$regUserPath = Get-SafeRegistryValue -Path "HKCU:\Environment" -Name "Path"
if ($regUserPath -like "ERROR:*") {
    Write-Host "  $regUserPath" -ForegroundColor Red
} else {
    $regUserPath -split ';' | ForEach-Object { "  $_" }
}

Write-Host "`n[5] System PATH (Registry):" -ForegroundColor Green
$regSystemPath = Get-SafeRegistryValue -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" -Name "Path"
if ($regSystemPath -like "ERROR:*") {
    Write-Host "  $regSystemPath" -ForegroundColor Red
} else {
    $regSystemPath -split ';' | ForEach-Object { "  $_" }
}

# 5. Check for missing critical paths
Write-Host "`n=== CRITICAL PATH VERIFICATION ===" -ForegroundColor Yellow

$criticalPaths = @(
    "C:\Windows\system32",
    "C:\Windows",
    "C:\Windows\System32\Wbem",
    "C:\Windows\System32\WindowsPowerShell\v1.0\",
    "$env:USERPROFILE\.local\bin",
    "$env:USERPROFILE\AppData\Local\Programs\Microsoft VS Code\bin",
    "C:\Program Files\Git\cmd",
    "C:\Program Files\nodejs\"
)

Write-Host "`n[6] Checking for critical paths in combined PATH:" -ForegroundColor Green
foreach ($path in $criticalPaths) {
    $exists = $env:PATH -split ';' | Where-Object { $_ -eq $path }
    if ($exists) {
        Write-Host "  ✓ FOUND: $path" -ForegroundColor Green
    } else {
        Write-Host "  ✗ MISSING: $path" -ForegroundColor Red
    }
}

# 6. Check registry permissions
Write-Host "`n=== REGISTRY PERMISSIONS CHECK ===" -ForegroundColor Yellow

Write-Host "`n[7] User Environment Registry Permissions:" -ForegroundColor Green
try {
    $acl = Get-Acl "HKCU:\Environment"
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    $userAccess = $acl.Access | Where-Object { $_.IdentityReference -eq $currentUser }

    if ($userAccess) {
        Write-Host "  Current User: $currentUser" -ForegroundColor Gray
        Write-Host "  Rights: $($userAccess.RegistryRights)" -ForegroundColor Gray
        Write-Host "  Access Control Type: $($userAccess.AccessControlType)" -ForegroundColor Gray
    } else {
        Write-Host "  WARNING: No explicit permissions for current user!" -ForegroundColor Red
    }
} catch {
    Write-Host "  ERROR: Cannot read ACL - $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n[8] System Environment Registry Permissions:" -ForegroundColor Green
try {
    $acl = Get-Acl "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    $adminGroup = "BUILTIN\Administrators"
    $adminAccess = $acl.Access | Where-Object { $_.IdentityReference -like "*Administrators*" }

    if ($adminAccess) {
        Write-Host "  Administrators Group Rights: $($adminAccess.RegistryRights)" -ForegroundColor Gray
        Write-Host "  Access Control Type: $($adminAccess.AccessControlType)" -ForegroundColor Gray
    } else {
        Write-Host "  WARNING: No administrator permissions found!" -ForegroundColor Red
    }

    # Check if current user is admin
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    Write-Host "  Current session is Administrator: $isAdmin" -ForegroundColor $(if ($isAdmin) { "Green" } else { "Yellow" })
} catch {
    Write-Host "  ERROR: Cannot read ACL - $($_.Exception.Message)" -ForegroundColor Red
}

# 7. Check for recent system events related to environment changes
Write-Host "`n=== SYSTEM EVENT LOG CHECK ===" -ForegroundColor Yellow

Write-Host "`n[9] Recent System Events (last 24 hours):" -ForegroundColor Green
try {
    $yesterday = (Get-Date).AddDays(-1)
    $events = Get-WinEvent -FilterHashtable @{
        LogName = 'System'
        StartTime = $yesterday
    } -MaxEvents 50 -ErrorAction Stop | Where-Object {
        $_.Message -like "*environment*" -or
        $_.Message -like "*registry*" -or
        $_.Message -like "*group policy*"
    }

    if ($events) {
        foreach ($event in $events) {
            Write-Host "  [$($event.TimeCreated)] $($event.ProviderName): $($event.Message.Substring(0, [Math]::Min(100, $event.Message.Length)))..." -ForegroundColor Gray
        }
    } else {
        Write-Host "  No relevant events found in last 24 hours" -ForegroundColor Gray
    }
} catch {
    Write-Host "  WARNING: Cannot read event log - $($_.Exception.Message)" -ForegroundColor Yellow
}

# 8. Check for interfering software
Write-Host "`n=== INTERFERING SOFTWARE CHECK ===" -ForegroundColor Yellow

Write-Host "`n[10] Checking for antivirus/security software:" -ForegroundColor Green
Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct -ErrorAction SilentlyContinue |
    ForEach-Object {
        Write-Host "  Found: $($_.displayName) (State: $($_.productState))" -ForegroundColor Gray
    }

Write-Host "`n[11] Checking for system optimizers/cleaners:" -ForegroundColor Green
$suspectApps = @(
    "CCleaner",
    "Advanced SystemCare",
    "PC Optimizer",
    "Registry Cleaner",
    "System Mechanic"
)

$installedApps = Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* |
    Select-Object DisplayName, Publisher, InstallDate

foreach ($app in $suspectApps) {
    $found = $installedApps | Where-Object { $_.DisplayName -like "*$app*" }
    if ($found) {
        Write-Host "  ⚠ FOUND: $($found.DisplayName) (Installed: $($found.InstallDate))" -ForegroundColor Yellow
    }
}

# 9. Check MCP server status
Write-Host "`n=== MCP SERVER STATUS ===" -ForegroundColor Yellow

Write-Host "`n[12] Checking for MCP-related executables:" -ForegroundColor Green

$mcpExecutables = @{
    "npx" = "C:\Program Files\nodejs\npx.cmd"
    "node" = "C:\Program Files\nodejs\node.exe"
    "python" = "C:\Users\pmacl\AppData\Local\Programs\Python\Python312\python.exe"
    "bws" = "$env:USERPROFILE\.local\bin\bws.exe"
}

foreach ($exe in $mcpExecutables.GetEnumerator()) {
    if (Test-Path $exe.Value) {
        Write-Host "  ✓ FOUND: $($exe.Key) at $($exe.Value)" -ForegroundColor Green
    } else {
        # Try to find in PATH
        $found = Get-Command $exe.Key -ErrorAction SilentlyContinue
        if ($found) {
            Write-Host "  ✓ FOUND in PATH: $($exe.Key) at $($found.Source)" -ForegroundColor Green
        } else {
            Write-Host "  ✗ MISSING: $($exe.Key) (expected at $($exe.Value))" -ForegroundColor Red
        }
    }
}

# 10. Create backup
Write-Host "`n=== CREATING BACKUP ===" -ForegroundColor Yellow

$backupFile = "$reportDir\path_backup_$timestamp.ps1"
Write-Host "`n[13] Saving PATH restoration script to: $backupFile" -ForegroundColor Green

$backupScript = @"
# PATH Restoration Script
# Generated: $timestamp
# Use this script to restore PATH if it gets reset

# Restore User PATH
[Environment]::SetEnvironmentVariable("PATH", "$userPath", "User")

# Restore System PATH (requires Administrator)
# Uncomment and run as Administrator if needed:
# [Environment]::SetEnvironmentVariable("PATH", "$systemPath", "Machine")

Write-Host "PATH restored from backup created at $timestamp" -ForegroundColor Green
Write-Host "Please restart your terminal or run 'refreshenv' to apply changes" -ForegroundColor Yellow
"@

$backupScript | Out-File -FilePath $backupFile -Encoding UTF8

Write-Host "  ✓ Backup saved to: $backupFile" -ForegroundColor Green

# Summary
Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Full diagnostic report: $reportFile" -ForegroundColor Gray
Write-Host "PATH backup script: $backupFile" -ForegroundColor Gray
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review the diagnostic report above" -ForegroundColor Gray
Write-Host "  2. Check for any missing critical paths (marked with ✗)" -ForegroundColor Gray
Write-Host "  3. Review interfering software warnings (marked with ⚠)" -ForegroundColor Gray
Write-Host "  4. Keep the backup script for emergency restoration" -ForegroundColor Gray
Write-Host ""

Stop-Transcript

Write-Host "Diagnostic complete!" -ForegroundColor Green
