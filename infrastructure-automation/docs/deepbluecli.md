# DeepBlueCLI Reference Guide

> Windows Event Log threat hunting tool by SANS (Eric Conrad)
> Repo: https://github.com/sans-blue-team/DeepBlueCLI

## Installation

**Location:** `C:\Tools\DeepBlueCLI\` (win-workstation)

```powershell
# Download (no git required)
$url = "https://github.com/sans-blue-team/DeepBlueCLI/archive/refs/heads/master.zip"
$out = "C:\Tools\DeepBlueCLI.zip"
Invoke-WebRequest -Uri $url -OutFile $out
Expand-Archive -Path "C:\Tools\DeepBlueCLI.zip" -DestinationPath "C:\Tools\"
Rename-Item "C:\Tools\DeepBlueCLI-master" "C:\Tools\DeepBlueCLI"
Remove-Item "C:\Tools\DeepBlueCLI.zip"
```

## Execution Policy

DeepBlueCLI requires script execution. Set per-session (does not persist):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Always run from the DeepBlueCLI directory** so it can find `regexes.txt` and `safelist.txt`:

```powershell
cd C:\Tools\DeepBlueCLI
```

---

## Basic Usage

### Scan Live Event Logs

```powershell
# Security log — logon attacks, account abuse, privilege escalation
.\DeepBlue.ps1 -log Security

# System log — log clears, suspicious services, interactive service warnings
.\DeepBlue.ps1 -log System

# Sysmon log — process creation, network connections, driver loads
.\DeepBlue.ps1 -log Sysmon
```

**Supported `-log` values:** `Security`, `System`, `Sysmon`

### Scan Saved/Exported EVTX Files

```powershell
# Analyze an exported .evtx file
.\DeepBlue.ps1 C:\path\to\exported-log.evtx

# Useful for offline analysis or analyzing logs from other machines
.\DeepBlue.ps1 .\evtx\new-user-security.evtx
```

### Output Formatting

```powershell
# Default output (Format-List)
.\DeepBlue.ps1 -log Security

# Table format (compact view)
.\DeepBlue.ps1 -log Security | Format-Table -AutoSize

# Grid view (interactive GUI window)
.\DeepBlue.ps1 -log Security | Out-GridView

# Export to CSV
.\DeepBlue.ps1 -log Security | Export-Csv -Path C:\Tools\deepblue-results.csv -NoTypeInformation

# Export to JSON (useful for Wazuh ingestion)
.\DeepBlue.ps1 -log Security | ConvertTo-Json | Out-File C:\Tools\deepblue-results.json

# Save plain text log
.\DeepBlue.ps1 -log Security | Out-File -Append C:\Tools\deepblue-output.log
```

---

## What DeepBlueCLI Detects

### Security Log (Event IDs)

| Event ID | Detection | ATT&CK |
|----------|-----------|--------|
| 4624 | Logon type anomalies | T1078 (Valid Accounts) |
| 4625 | Brute force / password spraying (multiple failed logons) | T1110 (Brute Force) |
| 4648 | Explicit credential use (runas, pass-the-hash) | T1550 (Use Alternate Auth Material) |
| 4672 | Multiple admin logons for one account | T1078 (Valid Accounts) |
| 4720 | New user creation | T1136 (Create Account) |
| 4732 | User added to local admin group | T1098 (Account Manipulation) |
| 4735 | Security group modification | T1098 (Account Manipulation) |
| 4738 | User account changed | T1098 (Account Manipulation) |
| 4756 | User added to security-enabled universal group | T1098 (Account Manipulation) |
| 4765/4766 | SID history added to account | T1134 (Access Token Manipulation) |
| 4794 | DSRM password change attempt | T1003 (OS Credential Dumping) |

### System Log (Event IDs)

| Event ID | Detection | ATT&CK |
|----------|-----------|--------|
| 104 | Event log cleared (anti-forensics) | T1070.001 (Indicator Removal: Clear Event Logs) |
| 7030 | Interactive service installed (malware indicator) | T1543 (Create/Modify System Process) |
| 7036 | Suspicious service state changes | T1543 (Create/Modify System Process) |
| 7045 | New service installed (persistence, lateral movement) | T1543.003 (Windows Service) |

### Sysmon Log (Event IDs)

| Event ID | Detection | ATT&CK |
|----------|-----------|--------|
| 1 | Suspicious process creation, obfuscated commands | T1059 (Command & Scripting Interpreter) |
| 3 | Suspicious network connections | T1071 (Application Layer Protocol) |
| 6 | Unsigned/suspicious driver loaded | T1014 (Rootkit) |
| 7 | Suspicious DLL loaded | T1574 (Hijack Execution Flow) |

### Specific Attack Patterns Detected

- **Password spraying** — Many accounts failing with same password
- **Password brute force** — Many failed logons to one account
- **Obfuscated PowerShell** — High % of special characters, long commands
- **PowerShell download cradles** — `IEX`, `Net.WebClient`, `DownloadString`, etc.
- **Mimikatz indicators** — Credential dumping tool signatures
- **New admin accounts** — User creation + admin group add
- **Log clearing** — Anti-forensic event log deletion

---

## Practice with Included Sample EVTX Files

DeepBlueCLI ships with test event logs in the `evtx\` directory:

```powershell
# List available sample files
Get-ChildItem .\evtx\

# Run against samples to see what attacks look like
.\DeepBlue.ps1 .\evtx\new-user-security.evtx
.\DeepBlue.ps1 .\evtx\password-spray.evtx
.\DeepBlue.ps1 .\evtx\powershell-execution-policy-bypass.evtx
.\DeepBlue.ps1 .\evtx\Powershell-Invoke-Obfuscation-encoding-security.evtx
.\DeepBlue.ps1 .\evtx\psattack-security.evtx
.\DeepBlue.ps1 .\evtx\mimikatz-privesc-hashdump.evtx
```

### Practice Workflow

1. Run DeepBlueCLI against a sample evtx
2. Read the output — note the Event ID, message, and decoded command
3. Map the finding to MITRE ATT&CK technique
4. Think about what Wazuh rule would catch this in production
5. Check if your Wazuh rules on the manager cover that detection

---

## Investigating Findings

When DeepBlueCLI flags something, dig deeper with native PowerShell:

```powershell
# Get full details of a specific Event ID
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4672} -MaxEvents 10 | Format-List *

# Search events in a time range
$start = (Get-Date).AddHours(-24)
Get-WinEvent -FilterHashtable @{LogName='Security'; StartTime=$start} -MaxEvents 50

# Find who cleared the logs (Event 104)
Get-WinEvent -FilterHashtable @{LogName='System'; Id=104} -MaxEvents 5 | Format-List *

# Search for specific user activity
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624} -MaxEvents 100 |
  Where-Object { $_.Message -match "lexingtonpass" } | Format-List TimeCreated, Message

# Export events around a suspicious timestamp for offline analysis
$start = [datetime]"2/25/2026 8:00 AM"
$end = [datetime]"2/25/2026 9:00 AM"
Get-WinEvent -FilterHashtable @{LogName='Security'; StartTime=$start; EndTime=$end} |
  Export-Csv C:\Tools\investigation.csv -NoTypeInformation
```

---

## Automation — Scheduled Task + Wazuh Integration

### Create Scheduled Task (runs every 15 minutes)

```powershell
$action = New-ScheduledTaskAction `
  -Execute "powershell.exe" `
  -Argument "-ExecutionPolicy Bypass -Command `"Set-Location C:\Tools\DeepBlueCLI; .\DeepBlue.ps1 -log Security | Out-File -Append C:\Tools\DeepBlueCLI\deepblue-output.log; .\DeepBlue.ps1 -log System | Out-File -Append C:\Tools\DeepBlueCLI\deepblue-output.log`""

$trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 15) -Once -At (Get-Date)

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "DeepBlueCLI-Scan" -Action $action -Trigger $trigger -Principal $principal -Description "Automated DeepBlueCLI threat hunting scan"
```

### Verify Scheduled Task

```powershell
Get-ScheduledTask -TaskName "DeepBlueCLI-Scan" | Format-List
Get-ScheduledTaskInfo -TaskName "DeepBlueCLI-Scan"
```

### Remove Scheduled Task (if needed)

```powershell
Unregister-ScheduledTask -TaskName "DeepBlueCLI-Scan" -Confirm:$false
```

### Wazuh Agent Config (ossec.conf on win-workstation)

Add to `C:\Program Files (x86)\ossec-agent\ossec.conf`:

```xml
<localfile>
  <log_format>full_command</log_format>
  <command>powershell.exe -ExecutionPolicy Bypass -Command "Set-Location C:\Tools\DeepBlueCLI; .\DeepBlue.ps1 -log Security; .\DeepBlue.ps1 -log System"</command>
  <frequency>900</frequency>
  <alias>deepbluecli</alias>
</localfile>
```

Then restart the Wazuh agent:

```powershell
Restart-Service WazuhSvc
```

### Wazuh Custom Rules (on Wazuh Manager)

Add to `/var/ossec/etc/rules/local_rules.xml`:

```xml
<!-- DeepBlueCLI Detections -->
<group name="deepbluecli,">
  <rule id="100150" level="12">
    <match>Password spray</match>
    <hostname>win-workstation</hostname>
    <description>DeepBlueCLI: Password spray attack detected</description>
    <mitre>
      <id>T1110.003</id>
    </mitre>
  </rule>

  <rule id="100151" level="14">
    <match>Mimikatz</match>
    <hostname>win-workstation</hostname>
    <description>DeepBlueCLI: Mimikatz credential dumping detected</description>
    <mitre>
      <id>T1003</id>
    </mitre>
  </rule>

  <rule id="100152" level="10">
    <match>New user</match>
    <hostname>win-workstation</hostname>
    <description>DeepBlueCLI: New user account created</description>
    <mitre>
      <id>T1136</id>
    </mitre>
  </rule>

  <rule id="100153" level="10">
    <match>Log Clear</match>
    <hostname>win-workstation</hostname>
    <description>DeepBlueCLI: Event log cleared (anti-forensics)</description>
    <mitre>
      <id>T1070.001</id>
    </mitre>
  </rule>

  <rule id="100154" level="12">
    <match type="pcre2">obfuscat|encoded|-enc </match>
    <hostname>win-workstation</hostname>
    <description>DeepBlueCLI: Obfuscated or encoded PowerShell detected</description>
    <mitre>
      <id>T1059.001</id>
      <id>T1027</id>
    </mitre>
  </rule>

  <rule id="100155" level="10">
    <match>Suspicious service</match>
    <hostname>win-workstation</hostname>
    <description>DeepBlueCLI: Suspicious service installed</description>
    <mitre>
      <id>T1543.003</id>
    </mitre>
  </rule>

  <rule id="100156" level="12">
    <match>Multiple admin logons</match>
    <hostname>win-workstation</hostname>
    <description>DeepBlueCLI: Multiple admin logons detected for single account</description>
    <mitre>
      <id>T1078</id>
    </mitre>
  </rule>

  <rule id="100157" level="12">
    <match>Password brute</match>
    <hostname>win-workstation</hostname>
    <description>DeepBlueCLI: Password brute force attack detected</description>
    <mitre>
      <id>T1110.001</id>
    </mitre>
  </rule>
</group>
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `DeepBlue.ps1` | Main script |
| `regexes.txt` | Regex patterns for suspicious command detection |
| `safelist.txt` | Whitelist — add known-good hashes/processes here |
| `evtx\` | Sample attack event logs for practice |

## Customization

### Whitelist known-good entries in `safelist.txt`

Add one entry per line to suppress false positives:

```
# Add process names or hashes to whitelist
<ms-account-email>
```

---

## Deployment Status

| Host | Status | Notes |
|------|--------|-------|
| workstation-1 | Installed | `C:\Tools\DeepBlueCLI\` |
| workstation-2 | Pending | Install when machine is back online |

---

## Known Benign Findings on win-workstation

| Finding | Event ID | Explanation |
|---------|----------|-------------|
| Multiple admin logons - <ms-account-email> | 4672 | Microsoft account sync (OneDrive) |
| System Log Clear (frequent Event 104) | 104 | **False positive** — ProviderName is `WudfUsbccidDriver` (USB smartcard reader), NOT `Microsoft-Windows-Eventlog`. Same Event ID, different source. Benign. |
| Interactive service warning - Printer Extensions | 7030 | Normal Windows printer service |
