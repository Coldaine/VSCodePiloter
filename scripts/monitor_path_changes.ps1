# PATH Change Monitor
# Purpose: Monitor and log PATH variable changes in real-time
# Usage: Run this script in a background PowerShell window to track changes

param(
    [int]$IntervalSeconds = 60,  # Check every 60 seconds
    [string]$LogFile = "E:\_OneOffs\VSCodePiloter\diagnostics\path_monitor.log"
)

Write-Host "=== PATH Change Monitor ===" -ForegroundColor Cyan
Write-Host "Checking every $IntervalSeconds seconds" -ForegroundColor Gray
Write-Host "Logging to: $LogFile" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Yellow

# Initialize baseline
$lastUserPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
$lastSystemPath = [Environment]::GetEnvironmentVariable('PATH', 'Machine')
$lastUserCount = if ($lastUserPath) { ($lastUserPath -split ';').Count } else { 0 }
$lastSystemCount = if ($lastSystemPath) { ($lastSystemPath -split ';').Count } else { 0 }

Write-Host "Baseline captured:" -ForegroundColor Green
Write-Host "  User PATH: $lastUserCount entries" -ForegroundColor Gray
Write-Host "  System PATH: $lastSystemCount entries`n" -ForegroundColor Gray

# Log initial state
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $LogFile -Value "[$timestamp] Monitor started - User:$lastUserCount | System:$lastSystemCount"

try {
    while ($true) {
        Start-Sleep -Seconds $IntervalSeconds

        # Check current state
        $currentUserPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
        $currentSystemPath = [Environment]::GetEnvironmentVariable('PATH', 'Machine')
        $currentUserCount = if ($currentUserPath) { ($currentUserPath -split ';').Count } else { 0 }
        $currentSystemCount = if ($currentSystemPath) { ($currentSystemPath -split ';').Count } else { 0 }

        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $changed = $false

        # Detect User PATH changes
        if ($currentUserPath -ne $lastUserPath) {
            $changed = $true
            $diff = $currentUserCount - $lastUserCount
            $message = "[$timestamp] USER PATH CHANGED! Entries: $lastUserCount -> $currentUserCount (diff: $diff)"

            Write-Host $message -ForegroundColor Red
            Add-Content -Path $LogFile -Value $message

            # Log what changed
            if ($diff -lt 0) {
                Write-Host "  PATHS REMOVED:" -ForegroundColor Yellow
                $removed = ($lastUserPath -split ';') | Where-Object { $_ -and $currentUserPath -notlike "*$_*" }
                foreach ($r in $removed) {
                    $msg = "    - $r"
                    Write-Host $msg -ForegroundColor Yellow
                    Add-Content -Path $LogFile -Value $msg
                }
            } elseif ($diff -gt 0) {
                Write-Host "  PATHS ADDED:" -ForegroundColor Green
                $added = ($currentUserPath -split ';') | Where-Object { $_ -and $lastUserPath -notlike "*$_*" }
                foreach ($a in $added) {
                    $msg = "    + $a"
                    Write-Host $msg -ForegroundColor Green
                    Add-Content -Path $LogFile -Value $msg
                }
            }

            # Check for running processes that might have caused the change
            $recentProcs = Get-Process | Where-Object {
                $_.ProcessName -like '*setup*' -or
                $_.ProcessName -like '*install*' -or
                $_.ProcessName -like '*update*' -or
                $_.ProcessName -like '*clean*' -or
                $_.ProcessName -like '*optimizer*' -or
                $_.ProcessName -like '*registry*'
            } | Select-Object -First 5

            if ($recentProcs) {
                Write-Host "  Suspicious processes running:" -ForegroundColor Yellow
                Add-Content -Path $LogFile -Value "  Suspicious processes:"
                foreach ($p in $recentProcs) {
                    $msg = "    - $($p.ProcessName) (PID: $($p.Id))"
                    Write-Host $msg -ForegroundColor Yellow
                    Add-Content -Path $LogFile -Value $msg
                }
            }

            $lastUserPath = $currentUserPath
            $lastUserCount = $currentUserCount
        }

        # Detect System PATH changes
        if ($currentSystemPath -ne $lastSystemPath) {
            $changed = $true
            $diff = $currentSystemCount - $lastSystemCount
            $message = "[$timestamp] SYSTEM PATH CHANGED! Entries: $lastSystemCount -> $currentSystemCount (diff: $diff)"

            Write-Host $message -ForegroundColor Red
            Add-Content -Path $LogFile -Value $message

            if ($diff -lt 0) {
                Write-Host "  PATHS REMOVED:" -ForegroundColor Yellow
                $removed = ($lastSystemPath -split ';') | Where-Object { $_ -and $currentSystemPath -notlike "*$_*" }
                foreach ($r in $removed) {
                    $msg = "    - $r"
                    Write-Host $msg -ForegroundColor Yellow
                    Add-Content -Path $LogFile -Value $msg
                }
            } elseif ($diff -gt 0) {
                Write-Host "  PATHS ADDED:" -ForegroundColor Green
                $added = ($currentSystemPath -split ';') | Where-Object { $_ -and $lastSystemPath -notlike "*$_*" }
                foreach ($a in $added) {
                    $msg = "    + $a"
                    Write-Host $msg -ForegroundColor Green
                    Add-Content -Path $LogFile -Value $msg
                }
            }

            $lastSystemPath = $currentSystemPath
            $lastSystemCount = $currentSystemCount
        }

        # Periodic heartbeat (every 10 checks)
        if (-not $changed -and ((Get-Date).Minute % 10 -eq 0)) {
            Write-Host "." -NoNewline -ForegroundColor DarkGray
        }
    }
} catch {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "`n[$timestamp] Monitor stopped: $_" -ForegroundColor Yellow
    Add-Content -Path $LogFile -Value "[$timestamp] Monitor stopped: $_"
}
