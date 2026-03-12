# HiFi Security Audit Scaffold

Reusable security baseline assessment toolkit for client engagements. Runs read-only checks across Linux, Windows, and macOS hosts, scores compliance, and generates prioritized remediation reports.

## Quick Start

```bash
# 1. Copy this project for a new client
cp -r hifi-security-audit/ ~/HiFi\ Solutions/<client-name>-security-audit/

# 2. Add client inventory
cp inventory/example.ini inventory/<client>.ini
# Edit with client hosts, credentials, SSH key / WinRM creds

# 3. Run audits per platform
ansible-playbook -i inventory/<client>.ini security-audit.yml           # Linux
ansible-playbook -i inventory/<client>.ini security-audit-windows.yml   # Windows
ansible-playbook -i inventory/<client>.ini security-audit-macos.yml     # macOS

# 4. Review reports
ls reports/
```

## Project Structure

```
hifi-security-audit/
├── security-audit.yml              # Linux playbook
├── security-audit-windows.yml      # Windows playbook
├── security-audit-macos.yml        # macOS playbook
├── templates/
│   ├── security-report.md.j2       # Linux report template
│   ├── security-report-windows.md.j2
│   └── security-report-macos.md.j2
├── inventory/
│   └── example.ini                 # Template inventory (all platforms)
├── vars/
│   └── defaults.yml                # Tunable thresholds and baselines
├── reports/                         # Generated reports (gitignored)
├── .gitignore
└── README.md
```

## Prerequisites

| Platform | Requirement |
|----------|-------------|
| Linux | SSH access with sudo |
| Windows | WinRM enabled; `pip install pywinrm` on control node |
| macOS | SSH (Remote Login) enabled with sudo |

## New Client Setup

### 1. Create inventory

Copy `inventory/example.ini` and fill in the client's hosts. Each playbook targets its own group:

```ini
[linux]
srv-1  ansible_host=10.0.1.10  ansible_user=deploy

[windows]
win-1  ansible_host=10.0.2.10

[windows:vars]
ansible_connection=winrm
ansible_winrm_transport=ntlm
ansible_port=5985
ansible_user=admin
ansible_password=<vault-encrypted>

[macos]
mac-1  ansible_host=10.0.3.10  ansible_user=admin
```

### 2. Customize thresholds (optional)

Edit `vars/defaults.yml` to adjust approved cipher lists, required services, or file permission expectations. Pass at runtime:

```bash
ansible-playbook -i inventory/<client>.ini security-audit.yml -e @vars/defaults.yml
```

### 3. Run audits

```bash
# Full audit per platform
ansible-playbook -i inventory/<client>.ini security-audit.yml
ansible-playbook -i inventory/<client>.ini security-audit-windows.yml
ansible-playbook -i inventory/<client>.ini security-audit-macos.yml

# Single host
ansible-playbook -i inventory/<client>.ini security-audit.yml -l srv-1

# Specific check categories only
ansible-playbook -i inventory/<client>.ini security-audit.yml --tags ssh,patches

# Skip slow SUID scan (Linux)
ansible-playbook -i inventory/<client>.ini security-audit.yml --skip-tags slow
```

## What Each Playbook Checks

### Linux (`security-audit.yml`)

| Tag | Category | Checks |
|-----|----------|--------|
| `ssh` | SSH Hardening | PermitRootLogin, PasswordAuth, EmptyPasswords, MaxAuthTries, X11, TcpForwarding, ClientAlive, Ciphers/MACs/Kex, file permissions |
| `firewall` | Firewall | UFW installed/active, default deny incoming, open ports |
| `services` | Services | Dangerous services disabled (avahi, cups, rpcbind, telnet, rsh), required services running |
| `filesystem` | File Integrity | Critical file permissions, world-writable files, SUID/SGID binaries, AIDE |
| `patches` | Patch Status | Available upgrades, unattended-upgrades, kernel updates, apt cache age, reboot required |
| `auth` | Authentication | Password quality, empty passwords, UID 0 accounts, sudo config, login banners |
| `audit` | Audit/Logging | auditd, audit rules (sudoers, time, user/group), log rotation, rsyslog |
| `network` | Network Hardening | 19 sysctl checks (ip_forward, redirects, syncookies, rp_filter, ASLR, IPv6) |
| `agents` | Security Agents | Wazuh agent, Tailscale, fail2ban + jails |
| `slow` | Slow Scans | SUID/SGID binary enumeration |

### Windows (`security-audit-windows.yml`)

| Tag | Category | Checks |
|-----|----------|--------|
| `rdp` | RDP Hardening | NLA required, encryption level, RDP enabled/disabled |
| `firewall` | Windows Firewall | All profiles enabled, default inbound block, open ports |
| `services` | Services | Dangerous (RemoteRegistry, Telnet, SNMP), required (Defender, EventLog, Firewall, WU, Wazuh) |
| `filesystem` | SMB & Disk | SMB signing, SMBv1 disabled, BitLocker status |
| `patches` | Windows Update | Pending updates, last install date, WU service, reboot pending, OS build |
| `auth` | Authentication | Password length, lockout threshold, guest account, admin renamed, UAC, legal notice |
| `audit` | Audit Policy | Security log size, PowerShell logging (script block + module), Sysmon, command-line auditing, 8 audit subcategories |
| `network` | Network | LLMNR disabled, SMB signing, WinRM HTTPS |
| `agents` | Security Agents | Windows Defender + real-time protection, Wazuh agent, Tailscale |

### macOS (`security-audit-macos.yml`)

| Tag | Category | Checks |
|-----|----------|--------|
| `ssh` | SSH Hardening | PermitRootLogin, PasswordAuth, EmptyPasswords, file permissions |
| `encryption` | Disk Encryption | FileVault enabled |
| `firewall` | Application Firewall | Firewall enabled, stealth mode, open ports |
| `services` | System Integrity | SIP, Gatekeeper, auto-login, AirDrop, Bluetooth sharing |
| `filesystem` | File Integrity | World-writable files, home directory permissions |
| `patches` | Software Updates | Available updates, auto-check/download/install settings, critical updates |
| `auth` | Authentication | Guest account, login window config, password hints, admin group members |
| `audit` | Logging | auditd, unified logging |
| `network` | Network | IP forwarding, Bonjour advertising, Internet Sharing, Wi-Fi saved networks |
| `agents` | Security Agents | Wazuh agent, Tailscale, MDM enrollment |

## Report Output

Each playbook generates a markdown report in `reports/`:

| Playbook | Report File |
|----------|-------------|
| Linux | `security-audit-YYYY-MM-DD.md` |
| Windows | `security-audit-windows-YYYY-MM-DD.md` |
| macOS | `security-audit-macos-YYYY-MM-DD.md` |

Reports contain:

1. **Executive Summary** -- pass/fail/warn counts per host
2. **Per-Host Detail** -- every finding with severity and current value
3. **Prioritized Remediation Roadmap** -- grouped CRITICAL > HIGH > MEDIUM > LOW with fix commands
4. **Patch Status Matrix** -- platform-specific update status per host

## Severity Levels

| Level | Examples |
|-------|----------|
| CRITICAL | Root login allowed, empty passwords, firewall disabled, SIP disabled, SMBv1 enabled, FileVault off, UAC disabled |
| HIGH | Password auth enabled, missing updates, no auditd, dangerous services, no Defender, guest account enabled, no NLA |
| MEDIUM | Weak SSH ciphers, missing banners, no AIDE, stale patches, missing audit rules, no stealth mode |
| LOW | sysctl tuning, Bonjour, Wi-Fi networks, password hints |

## Adapting for Client Environments

### Different required services

Override in `vars/defaults.yml`:

```yaml
# Linux
required_services:
  - sshd
  - crowdstrike-falcon
  - auditd
```

Or pass extra vars for Windows/macOS:

```bash
ansible-playbook -i inventory/<client>.ini security-audit-windows.yml \
  -e '{"required_services_win": ["WinDefend", "EventLog", "CrowdStrike Falcon Sensor"]}'
```

### Different SSH/crypto baselines

Override `approved_ciphers`, `approved_macs`, `approved_kex` in `vars/defaults.yml`.

### Adding checks

Add new tasks to the relevant tag section. Each finding must follow:

```yaml
{
  "check": "Description",
  "status": "PASS or FAIL",
  "severity": "CRITICAL/HIGH/MEDIUM/LOW",
  "detail": "What was found",
  "fix": "How to fix it"
}
```

Append to the appropriate `*_findings` variable so it flows into the report automatically.

### Removing checks

Use `--skip-tags` at runtime rather than editing playbooks, so the scaffold stays reusable.

## Engagement Workflow

1. **Scope** -- Confirm target hosts, credentials, access method with client
2. **Inventory** -- Create `inventory/<client>.ini` with all platforms
3. **Baseline** -- Run relevant platform audits
4. **Deliver** -- Share reports from `reports/` with client
5. **Remediate** -- Apply fixes using hardening playbooks or client-specific runbooks
6. **Validate** -- Re-run audits to confirm remediation
7. **Archive** -- Store final reports in client folder
