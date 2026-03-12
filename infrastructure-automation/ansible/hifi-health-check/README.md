# HiFi Health Check Scaffold

Multi-platform hardware and service health check toolkit for client engagements. Runs read-only checks across Linux, Windows, and macOS hosts and generates a health report with actionable findings.

## Quick Start

```bash
# 1. Copy for a new client
cp -r hifi-health-check/ ~/HiFi\ Solutions/Ansible/<client>-health-check/

# 2. Create client inventory
cp inventory/example.ini inventory/<client>.ini
# Fill in hosts

# 3. Run health checks
ansible-playbook -i inventory/<client>.ini health-check.yml           # Linux
ansible-playbook -i inventory/<client>.ini health-check-windows.yml   # Windows
ansible-playbook -i inventory/<client>.ini health-check-macos.yml     # macOS

# 4. Review reports
ls reports/
```

## What Each Playbook Checks

### Linux (`health-check.yml`)

| Tag | Checks |
|-----|--------|
| `overview` | OS, kernel, uptime, CPU count, RAM usage, load average |
| `disk` | Filesystem usage (threshold warnings), swap usage |
| `zfs` | ZFS pool health and capacity (skipped if no ZFS) |
| `memory` | ECC/EDAC correctable and uncorrectable errors |
| `thermal` | CPU core temperatures via lm-sensors |
| `smart` | SMART health for all /dev/sd* and /dev/nvme* drives |
| `dmesg` | Kernel hardware error messages |
| `network` | Interface status, bond health, DNS, default gateway |
| `services` | Failed systemd units, sshd, cron |
| `time` | NTP synchronization |
| `slow` | Deep SMART scan (skip with `--skip-tags slow`) |

### Windows (`health-check-windows.yml`)

| Tag | Checks |
|-----|--------|
| `overview` | OS, build, uptime, CPU model/load, RAM usage |
| `disk` | Volume usage, physical disk health status |
| `memory` | Pagefile usage |
| `network` | Adapter status, DNS resolution, default gateway |
| `services` | Stopped auto-start services |
| `time` | W32Time NTP synchronization |
| `eventlog` | Critical/error events in System and Application logs (last 24h) |

### macOS (`health-check-macos.yml`)

| Tag | Checks |
|-----|--------|
| `overview` | macOS version, hardware model, CPU, RAM, uptime |
| `disk` | Root volume usage |
| `smart` | Disk SMART status via diskutil |
| `battery` | Battery condition and cycle count (laptops) |
| `network` | Interface status, DNS, gateway, Wi-Fi info |
| `services` | Key launchd services (auditd, syslogd, opendirectoryd) |
| `time` | Network time synchronization |

## Reports

Reports are generated in `reports/`:

| Platform | File |
|----------|------|
| Linux | `health-check-YYYY-MM-DD.md` |
| Windows | `health-check-windows-YYYY-MM-DD.md` |
| macOS | `health-check-macos-YYYY-MM-DD.md` |

## Tunable Thresholds

Edit `vars/defaults.yml` or pass at runtime with `-e @vars/defaults.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `disk_usage_warn` | 85 | Disk % before warning |
| `cpu_temp_warn` | 75 | CPU temp (C) before warning |
| `ecc_ce_warn` | 100 | ECC correctable errors before warning |
| `smart_reallocated_warn` | 50 | SMART reallocated sectors before warning |
| `load_warn_multiplier` | 2 | Load avg threshold = cores * this |
| `swap_usage_warn` | 50 | Swap % before warning |
| `uptime_warn_days` | 180 | Days without reboot before warning |
| `event_log_hours` | 24 | Windows event log lookback window |
