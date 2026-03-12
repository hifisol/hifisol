# HiFi Health Check — User Guide

This guide covers running system health checks against client environments across Linux, Windows, and macOS.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setting Up](#setting-up)
3. [Running Health Checks](#running-health-checks)
4. [Reading the Output](#reading-the-output)
5. [Understanding Findings](#understanding-findings)
6. [Common Workflows](#common-workflows)
7. [Customizing Thresholds](#customizing-thresholds)
8. [Troubleshooting](#troubleshooting)
9. [Tag Reference](#tag-reference)

---

## Prerequisites

**On your control machine:**

| Requirement | Install | When needed |
|-------------|---------|-------------|
| Ansible 2.12+ | `pip install ansible` | Always |
| pywinrm | `pip install pywinrm` | Windows targets |

**On target machines:**

| Platform | Requirement |
|----------|-------------|
| Linux | SSH with sudo access |
| Windows | WinRM enabled (port 5985 or 5986) |
| macOS | Remote Login enabled (SSH) with sudo |

---

## Setting Up

### 1. Copy the scaffold for a new client

```bash
cp -r hifi-health-check/ <client>-health-check/
cd <client>-health-check/
```

### 2. Create the inventory

```bash
cp inventory/example.ini inventory/acme.ini
```

Fill in the client's hosts. You only need the groups that apply — if a client is Windows-only, just fill in `[windows]`.

### 3. Test connectivity

```bash
# Linux
ansible -i inventory/acme.ini linux -m ping

# Windows
ansible -i inventory/acme.ini windows -m win_ping

# macOS
ansible -i inventory/acme.ini macos -m ping
```

All hosts should return `pong`. Fix any connection issues before running health checks.

---

## Running Health Checks

### Full check — all categories

```bash
# Linux
ansible-playbook -i inventory/acme.ini health-check.yml

# Windows
ansible-playbook -i inventory/acme.ini health-check-windows.yml

# macOS
ansible-playbook -i inventory/acme.ini health-check-macos.yml
```

### Single host

```bash
ansible-playbook -i inventory/acme.ini health-check.yml -l srv-1
```

### Specific categories

```bash
# Just disk and SMART on Linux
ansible-playbook -i inventory/acme.ini health-check.yml --tags disk,smart

# Just disk and event logs on Windows
ansible-playbook -i inventory/acme.ini health-check-windows.yml --tags disk,eventlog

# Just battery and disk on macOS
ansible-playbook -i inventory/acme.ini health-check-macos.yml --tags battery,disk
```

### Skip slow checks

The Linux SMART deep scan can take a while. Skip it:

```bash
ansible-playbook -i inventory/acme.ini health-check.yml --skip-tags slow
```

### Custom thresholds

```bash
# Lower disk warning to 70%
ansible-playbook -i inventory/acme.ini health-check.yml -e "disk_usage_warn=70"

# Use a custom vars file
ansible-playbook -i inventory/acme.ini health-check.yml -e @vars/defaults.yml
```

---

## Reading the Output

### Console output during the run

Each check prints a one-line result:

```
PASS [LOW]      Uptime — 14d 6h (OK)
WARN [HIGH]     Disk usage: /var — /var at 89% (threshold: 85%)
FAIL [CRITICAL] SMART health: /dev/sda — /dev/sda (WDC WD40EFRX) SMART FAILED
INFO [LOW]      Hostname — srv-1
SKIP [LOW]      ECC memory — EDAC not available (no ECC or driver not loaded)
```

| Status | Meaning |
|--------|---------|
| PASS | Within healthy thresholds |
| FAIL | Outside acceptable range — action needed |
| WARN | Approaching threshold or notable condition |
| INFO | Informational (versions, hardware details) |
| SKIP | Check could not run (tool not installed, feature absent) |

### End-of-host summary

```
=========================================
  HEALTH CHECK SUMMARY: srv-1
=========================================
  PASS: 12 | FAIL: 1 | WARN: 2
  CRITICAL issues: 1
=========================================
```

### Report

A markdown report is generated in `reports/` after all hosts finish. Open it in any markdown viewer.

---

## Understanding Findings

### What "CRITICAL" means in a health check

Unlike security audits (where CRITICAL = vulnerability), in health checks CRITICAL means **imminent hardware failure or data loss risk**:

- SMART FAILED on a drive
- ECC uncorrectable memory errors
- ZFS pool degraded
- Disk at 95%+ capacity

These need immediate attention.

### What "HIGH" means

Operational issues that will cause problems soon:

- Disk usage above threshold
- DNS not resolving
- No default gateway
- ECC correctable errors above threshold
- Key services stopped

### What "MEDIUM" and "LOW" mean

- **MEDIUM**: Pagefile high, NTP not synced, stopped auto-start services, event log errors
- **LOW**: Uptime high (needs reboot for patches), informational items

---

## Common Workflows

### Routine health check

Run weekly or monthly against all client hosts:

```bash
ansible-playbook -i inventory/acme.ini health-check.yml
ansible-playbook -i inventory/acme.ini health-check-windows.yml
ansible-playbook -i inventory/acme.ini health-check-macos.yml
```

Collect reports from `reports/` and compare against previous runs.

### Pre-maintenance check

Before applying patches or making changes, run a health check to establish baseline:

```bash
ansible-playbook -i inventory/acme.ini health-check.yml
# Save as pre-maintenance baseline
cp reports/health-check-2026-02-21.md reports/health-check-2026-02-21-pre.md
```

### Post-incident check

After an outage or incident, run a targeted check:

```bash
# Check disk and SMART on the affected host
ansible-playbook -i inventory/acme.ini health-check.yml -l srv-1 --tags disk,smart,dmesg
```

### Pair with security audit

Run both health check and security audit together for a complete assessment:

```bash
# Health first
ansible-playbook -i inventory/acme.ini ~/HiFi\ Solutions/Ansible/hifi-health-check/health-check.yml
# Then security
ansible-playbook -i inventory/acme.ini ~/HiFi\ Solutions/Ansible/hifi-security-audit/security-audit.yml
```

---

## Customizing Thresholds

### Edit defaults for a client

Copy and edit `vars/defaults.yml`:

```yaml
# Lower thresholds for production servers
disk_usage_warn: 70
cpu_temp_warn: 65
uptime_warn_days: 30

# Raise thresholds for dev/test
# disk_usage_warn: 90
# uptime_warn_days: 365
```

### Override at runtime

```bash
ansible-playbook -i inventory/acme.ini health-check.yml \
  -e "disk_usage_warn=70" \
  -e "uptime_warn_days=30"
```

---

## Troubleshooting

### Linux: "sensors" or "smartctl" not found

Checks that depend on these tools will show SKIP. Install if needed:

```bash
# On the target
sudo apt install lm-sensors smartmontools
sudo sensors-detect
```

### Windows: WinRM connection errors

On the target, run as Administrator:

```powershell
winrm quickconfig -q
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value true
Set-Item WSMan:\localhost\Service\Auth\Basic -Value true
```

### macOS: "sudo requires a password"

Either add `ansible_become_password` to inventory, or run with `--ask-become-pass`.

### Report file is empty

If the audit play fails before the summary task runs, `all_findings` will be empty. Check the playbook output for errors and fix the underlying issue.

### Comparing reports over time

Reports are date-stamped. Use `diff` to spot changes:

```bash
diff reports/health-check-2026-02-14.md reports/health-check-2026-02-21.md
```

---

## Tag Reference

### Linux

| Tag | What it checks |
|-----|---------------|
| `overview` | OS, kernel, uptime, CPU, RAM, load |
| `disk` | Filesystem and swap usage |
| `zfs` | ZFS pool health and capacity |
| `memory` | ECC/EDAC errors |
| `thermal` | CPU temperatures |
| `smart` | Drive SMART health |
| `dmesg` | Kernel hardware errors |
| `network` | Interfaces, bonds, DNS, gateway |
| `services` | Failed units, sshd, cron |
| `time` | NTP sync |
| `slow` | Deep SMART scan (use with `--skip-tags slow` to exclude) |

### Windows

| Tag | What it checks |
|-----|---------------|
| `overview` | OS, build, uptime, CPU, RAM |
| `disk` | Volume and physical disk health |
| `memory` | Pagefile usage |
| `network` | Adapters, DNS, gateway |
| `services` | Stopped auto-start services |
| `time` | W32Time NTP |
| `eventlog` | System/Application critical+error events (24h) |

### macOS

| Tag | What it checks |
|-----|---------------|
| `overview` | macOS version, hardware, CPU, RAM, uptime |
| `disk` | Root volume usage |
| `smart` | Disk SMART via diskutil |
| `battery` | Battery condition and cycles (laptops only) |
| `network` | Interfaces, DNS, gateway, Wi-Fi |
| `services` | Key launchd services |
| `time` | Network time sync |
