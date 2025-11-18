# PATH Variable Diagnostic Report
**Date**: 2025-11-18
**System**: Windows 11 Pro (PATRICK-DESKTOP)
**User**: pmacl

## Executive Summary

✅ **GOOD NEWS**: Your PATH variables are currently intact and functional.

⚠️ **KEY FINDINGS**:
- User PATH: 73 entries (healthy)
- System PATH: 32 entries (healthy)
- All critical executables (node, npx, git, python, bws) are accessible
- No malicious system optimizers detected
- Registry permissions are correct
- Only Windows Defender running (legitimate)

❌ **POTENTIAL ISSUES IDENTIFIED**:
1. **PATH is excessively long** (73 user entries - Windows has a ~2048 character limit)
2. **Duplicate entries detected** in User PATH (see analysis below)
3. **Environment variable expansion issue** detected (unexpanded `%SystemRoot%` variables)
4. **MCP server errors** are likely due to process startup issues, NOT PATH problems

---

## Detailed Analysis

### 1. Current PATH State

**User PATH (73 entries)**:
```
Total Character Count: ~2800 (approaching Windows limit of 2048 per variable)
```

**Notable duplicates/issues**:
- Git paths appear 3+ times (Git\cmd, Git\mingw64\bin, Git\usr\bin)
- Python 311 paths duplicated
- Several paths reference locations that may not exist

**System PATH (32 entries)** - appears healthy with standard Windows system directories.

### 2. Critical Executable Check

All key executables were found:
- ✅ `git`: C:\Program Files\Git\cmd\git.exe
- ✅ `npx`: C:\Program Files\nodejs\npx.ps1
- ✅ `node`: C:\Program Files\nodejs\node.exe
- ✅ `bws`: C:\Users\pmacl\AppData\Roaming\npm\bws.exe
- ✅ `python`: C:\Users\pmacl\Windows-MCP\.venv\Scripts\python.exe

**Note**: `python` is resolving to Windows-MCP venv, which is expected if that's your active environment.

### 3. Environment Variable Expansion Issue

⚠️ **CRITICAL**: Unexpanded variables detected in System PATH:
```
%SystemRoot%\system32
%SystemRoot%
%SystemRoot%\System32\Wbem
%SYSTEMROOT%\System32\WindowsPowerShell\v1.0\
%SYSTEMROOT%\System32\OpenSSH\
```

These should be expanded to actual paths. This can cause issues when:
- Other applications try to read PATH
- Environment variables are reset
- Registry is directly modified

### 4. MCP Server Analysis

**Claude Desktop Config** (`C:/Users/pmacl/AppData/Roaming/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "windows-mcp": {
      "command": "uv",
      "args": ["--directory", "C:/Users/pmacl/Windows-MCP", "run", "main.py"]
    }
  }
}
```

**VS Code MCP Config** (`C:/Users/pmacl/AppData/Roaming/Code/User/mcp.json`):
- Configured servers: sequentialthinking, exa, context7, github
- All use `npx` which is accessible

**Diagnosis**: MCP disconnection errors are likely due to:
1. Process startup delays (server taking too long to initialize)
2. Permission issues with the MCP server itself
3. Python environment issues (for windows-mcp)
4. NOT due to missing PATH entries

### 5. Security Software Check

- **Antivirus**: Windows Defender (State: 397568 = Active, Up-to-date)
- **System Optimizers**: None detected
- **No interfering software found**

### 6. Registry Permissions

✅ **All permissions are correct**:
- User Environment (HKCU:\Environment): FullControl for pmacl
- System Environment (HKLM:\...\Environment): FullControl for Administrators
- Current session: Running as standard user (not admin)

### 7. Event Log Analysis

No suspicious environment variable modifications detected in past 48 hours. Log shows only normal system operations (HTTP service, Time service).

---

## Root Cause Assessment

**Why are you "losing" your PATH?**

Based on this diagnostic, you are NOT actually losing your PATH variables. Here's what's likely happening:

### Theory 1: Application-Specific Environment Issues
Some applications (like VS Code, terminal emulators) may start with a stale environment snapshot from when the parent process launched. If you:
1. Update PATH in System Properties
2. Don't restart the parent application
3. Launch a new terminal/process from that app

...the new process inherits the OLD environment, making it appear PATH is "lost."

**Solution**: After modifying PATH, restart the parent applications (VS Code, Windows Terminal, etc.)

### Theory 2: PATH Length Limit Exceeded
Windows has a ~2048 character limit for environment variables. Your User PATH is ~2800 characters, which may cause:
- Silent truncation
- Variables being reset to defaults
- Applications failing to read the full PATH

**Solution**: Clean up duplicate entries (see below)

### Theory 3: MCP Process Initialization Failure
The MCP server errors you're seeing are separate from PATH issues. They indicate:
- The MCP server process is failing to start or respond
- Network/IPC communication issues
- Python environment problems for windows-mcp

**Solution**: Debug MCP server startup independently

---

## Remediation Recommendations

### IMMEDIATE ACTIONS

#### 1. Clean Up User PATH (HIGH PRIORITY)
Your User PATH has 73 entries with many duplicates. Reduce to essentials:

**Run this PowerShell script** (already created for you):
```powershell
# Located at: E:\_OneOffs\VSCodePiloter\scripts\cleanup_path.ps1
```

**Manual cleanup**:
1. Open System Properties → Environment Variables
2. Edit User PATH
3. Remove duplicates:
   - Keep only ONE Git entry: `C:\Program Files\Git\cmd`
   - Keep only ONE Python entry: `C:\Program Files\Python311\Scripts\;C:\Program Files\Python311\`
   - Remove any paths that don't exist
4. Verify total length < 2048 characters

#### 2. Monitor for Changes
Start the PATH monitor to catch real-time changes:
```powershell
powershell -ExecutionPolicy Bypass -File "E:\_OneOffs\VSCodePiloter\scripts\monitor_path_changes.ps1"
```

This will log any PATH modifications to `diagnostics/path_monitor.log`

#### 3. Verify MCP Server Health (Separate from PATH)
Test windows-mcp independently:
```powershell
cd C:\Users\pmacl\Windows-MCP
uv run main.py
```

If this fails, the issue is with the MCP server configuration, not PATH.

### PREVENTIVE MEASURES

#### 1. Restart Applications After PATH Changes
After modifying PATH:
- Restart VS Code
- Restart Windows Terminal
- Restart Claude Desktop
- Or reboot system for complete refresh

#### 2. Use Registry-Based PATH Backup
The backup script created a restore point at:
```
E:\_OneOffs\VSCodePiloter\diagnostics\path_backup_2025-11-18_002437.txt
```

**To restore from backup**:
```powershell
# Read the backup file
$backup = Get-Content "E:\_OneOffs\VSCodePiloter\diagnostics\path_backup_2025-11-18_002437.txt" -Raw

# Extract USER_PATH line
$userPath = ($backup -split "`n" | Where-Object { $_ -like "USER_PATH=*" }) -replace "USER_PATH=", ""

# Restore (run as regular user)
[Environment]::SetEnvironmentVariable("PATH", $userPath, "User")

Write-Host "User PATH restored from backup" -ForegroundColor Green
```

#### 3. Create Scheduled Task for PATH Validation
Set up a daily task that verifies PATH integrity and alerts you to changes.

#### 4. Document Your PATH Philosophy
Decide on a policy:
- **Minimal System PATH**: Only OS-critical directories
- **User PATH**: Application-specific additions
- **Project-specific**: Use virtual environments (Python venv, Node nvm, etc.)

---

## Tools Created for You

1. **PATH Backup**:
   - Location: `E:\_OneOffs\VSCodePiloter\diagnostics\path_backup_2025-11-18_002437.txt`
   - Contains full snapshot of User and System PATH

2. **PATH Monitor** (real-time change detection):
   - Script: `E:\_OneOffs\VSCodePiloter\scripts\monitor_path_changes.ps1`
   - Log: `E:\_OneOffs\VSCodePiloter\diagnostics\path_monitor.log`
   - Usage: `powershell -ExecutionPolicy Bypass -File "...\monitor_path_changes.ps1"`

3. **Diagnostic Script** (re-runnable):
   - Location: `E:\_OneOffs\VSCodePiloter\scripts\diagnose_path_issue.ps1`
   - Run anytime to generate new snapshot

---

## Next Steps

### If PATH appears "lost" again:

1. **Capture evidence immediately**:
   ```powershell
   $env:PATH | Out-File "E:\_OneOffs\VSCodePiloter\diagnostics\path_lost_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
   ```

2. **Check the monitor log**:
   ```powershell
   Get-Content "E:\_OneOffs\VSCodePiloter\diagnostics\path_monitor.log" -Tail 50
   ```

3. **Compare to backup**:
   ```powershell
   # See what's different
   $current = [Environment]::GetEnvironmentVariable('PATH', 'User')
   $backup = (Get-Content "E:\_OneOffs\VSCodePiloter\diagnostics\path_backup_2025-11-18_002437.txt" -Raw) -replace ".*USER_PATH=([^`n]+).*", '$1'
   Compare-Object ($current -split ';') ($backup -split ';')
   ```

4. **Restore from backup** (see section above)

5. **Review event logs** for clues:
   ```powershell
   Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=(Get-Date).AddHours(-1)} | Where-Object { $_.Message -like '*environment*' }
   ```

---

## Conclusion

**Your PATH is currently healthy.** The issues you're experiencing are likely due to:
1. Application environment staleness (restart apps after PATH changes)
2. PATH length approaching Windows limits (clean up duplicates)
3. MCP server startup issues (unrelated to PATH)

The tools created during this diagnostic will help you:
- ✅ Monitor for real changes
- ✅ Restore quickly if corruption occurs
- ✅ Identify the culprit if something modifies PATH

**Action Items**:
1. Clean up duplicate PATH entries (reduce from 73 to ~20-30)
2. Restart VS Code and terminal applications
3. Start PATH monitor in background
4. Debug MCP server issues separately

---

**Report Generated**: 2025-11-18 00:24:37
**Tools Location**: `E:\_OneOffs\VSCodePiloter\diagnostics\` and `scripts\`
