# HiFi Security Audit — User Guide

This guide walks through everything you need to run a security baseline assessment against a client environment, from initial setup through report delivery.

---

## Table of Contents

1. [Before You Start](#before-you-start)
2. [Setting Up a New Client](#setting-up-a-new-client)
3. [Running Audits](#running-audits)
4. [Reading the Output](#reading-the-output)
5. [Understanding the Report](#understanding-the-report)
6. [Common Workflows](#common-workflows)
7. [Customizing for a Client](#customizing-for-a-client)
8. [Troubleshooting](#troubleshooting)
9. [Reference](#reference)

---

## Before You Start

### What you need installed on your machine

| Requirement | Install command | Notes |
|-------------|----------------|-------|
| Ansible | `pip install ansible` or `apt install ansible` | 2.12+ recommended |
| pywinrm | `pip install pywinrm` | Only needed for Windows targets |
| SSH client | Pre-installed on Linux/macOS | Used for Linux and macOS targets |

Verify Ansible is working:

```bash
ansible --version
```

### What you need from the client

| Platform | Access needed |
|----------|---------------|
| Linux | SSH access with a user that has sudo privileges. Ideally key-based auth. |
| Windows | WinRM enabled on targets. A local admin account (or domain admin). Firewall allowing port 5985 (HTTP) or 5986 (HTTPS). |
| macOS | SSH (Remote Login) enabled on targets. A user with sudo privileges. |

### Enabling WinRM on Windows targets (if not already done)

On each Windows target, run PowerShell as Administrator:

```powershell
winrm quickconfig -q
winrm set winrm/config/service '@{AllowUnencrypted="true"}'
winrm set winrm/config/service/auth '@{Basic="true"}'
```

For domain environments, WinRM is typically enabled via GPO. For HTTPS (recommended in production), you'll also need a certificate configured on the listener.

### Enabling Remote Login on macOS targets

On each Mac, go to **System Settings > General > Sharing > Remote Login** and toggle it on. Or from Terminal:

```bash
sudo systemsetup -setremotelogin on
```

---

## Setting Up a New Client

### Step 1: Copy the scaffold

```bash
cd ~/HiFi\ Solutions/
cp -r hifi-security-audit/ <client-name>-security-audit/
cd <client-name>-security-audit/
```

### Step 2: Create the inventory file

```bash
cp inventory/example.ini inventory/<client>.ini
```

Open it in your editor and fill in the hosts. Only include the groups you need — if the client is Linux-only, you can leave `[windows]` and `[macos]` empty or remove them.

**Linux example:**

```ini
[all:vars]
ansible_ssh_private_key_file=~/.ssh/client-key

[linux]
web-1    ansible_host=10.0.1.10  ansible_user=deploy
db-1     ansible_host=10.0.1.20  ansible_user=deploy
app-1    ansible_host=10.0.1.30  ansible_user=deploy
```

**Windows example:**

```ini
[windows]
dc-1     ansible_host=10.0.2.10
file-1   ansible_host=10.0.2.20

[windows:vars]
ansible_connection=winrm
ansible_winrm_transport=ntlm
ansible_port=5985
ansible_user=Administrator
ansible_password=SecurePass123!
```

> **Security note:** Don't store passwords in plaintext. Use `ansible-vault` to encrypt:
> ```bash
> ansible-vault encrypt_string 'SecurePass123!' --name 'ansible_password'
> ```
> Then paste the encrypted block into your inventory or a vars file, and run playbooks with `--ask-vault-pass`.

**macOS example:**

```ini
[macos]
mac-1    ansible_host=10.0.3.10  ansible_user=admin
mac-2    ansible_host=10.0.3.20  ansible_user=admin

[macos:vars]
ansible_become_password=admin-sudo-password
```

**Mixed environment:**

You can have all three groups in a single inventory file. Each playbook only touches its own group.

### Step 3: Test connectivity

Before running the audit, verify you can reach every host:

```bash
# Linux
ansible -i inventory/<client>.ini linux -m ping

# Windows
ansible -i inventory/<client>.ini windows -m win_ping

# macOS
ansible -i inventory/<client>.ini macos -m ping
```

If a host fails, fix the connectivity issue before proceeding. Common problems:

- Wrong SSH key or password
- Firewall blocking SSH (22) or WinRM (5985/5986)
- User doesn't have sudo/admin privileges
- WinRM not enabled on Windows target

---

## Running Audits

### Full audit — all checks, all hosts in a group

```bash
# Linux
ansible-playbook -i inventory/<client>.ini security-audit.yml

# Windows
ansible-playbook -i inventory/<client>.ini security-audit-windows.yml

# macOS
ansible-playbook -i inventory/<client>.ini security-audit-macos.yml
```

### Audit a single host

Use `-l` (limit) to target one host by its inventory name:

```bash
ansible-playbook -i inventory/<client>.ini security-audit.yml -l web-1
```

### Audit specific categories only

Use `--tags` to run only the checks you care about. You can combine multiple tags with commas:

```bash
# Just SSH and patches on Linux
ansible-playbook -i inventory/<client>.ini security-audit.yml --tags ssh,patches

# Just firewall and RDP on Windows
ansible-playbook -i inventory/<client>.ini security-audit-windows.yml --tags firewall,rdp

# Just FileVault and patches on macOS
ansible-playbook -i inventory/<client>.ini security-audit-macos.yml --tags encryption,patches
```

### Skip slow checks

The Linux playbook's SUID/SGID binary scan (`slow` tag) can take a while on hosts with large filesystems. Skip it:

```bash
ansible-playbook -i inventory/<client>.ini security-audit.yml --skip-tags slow
```

### Use custom thresholds

If you've edited `vars/defaults.yml` for this client:

```bash
ansible-playbook -i inventory/<client>.ini security-audit.yml -e @vars/defaults.yml
```

### Increase verbosity

If something looks wrong or you want to debug:

```bash
# Show task details
ansible-playbook -i inventory/<client>.ini security-audit.yml -v

# Show connection details
ansible-playbook -i inventory/<client>.ini security-audit.yml -vvv
```

### Use vault-encrypted passwords

```bash
ansible-playbook -i inventory/<client>.ini security-audit-windows.yml --ask-vault-pass
```

---

## Reading the Output

### Live console output

As the playbook runs, each check prints a one-line result:

```
PASS [HIGH] PasswordAuthentication — Value: no
FAIL [CRITICAL] PermitRootLogin — Value: yes
WARN [MEDIUM] Tailscale — Tailscale: NeedsLogin
```

The format is: `STATUS [SEVERITY] Check Name — Detail`

| Status | Meaning |
|--------|---------|
| PASS | Check meets the baseline |
| FAIL | Check does not meet the baseline — action needed |
| WARN | Not a hard failure but worth reviewing |
| INFO | Informational only (version numbers, listings) |
| SKIP | Check could not run (file missing, tool not installed) |

### End-of-host summary

After all checks complete for a host, you'll see:

```
=========================================
  SECURITY AUDIT SUMMARY: web-1
=========================================
  PASS: 42 | FAIL: 7 | WARN: 3
  CRITICAL fails: 1
  HIGH fails:     3
  MEDIUM fails:   2
  LOW fails:      1
=========================================
```

Followed by a list of every FAIL finding.

### Report file

After all hosts finish, a markdown report is written to `reports/`. The playbook prints the exact path:

```
Security audit report written to: /home/you/HiFi Solutions/client-security-audit/reports/security-audit-2026-02-20.md
```

---

## Understanding the Report

Open the generated `.md` file in any markdown viewer (VS Code, GitHub, Obsidian, or convert to PDF).

### Executive Summary

A table showing pass/fail/warn counts for every host at a glance. Focus on hosts with high CRITICAL or HIGH fail counts first.

| Host | PASS | FAIL | WARN | Critical | High | Medium | Low |
|------|------|------|------|----------|------|--------|-----|
| web-1 | 42 | 7 | 3 | 1 | 3 | 2 | 1 |
| db-1 | 48 | 2 | 1 | 0 | 1 | 1 | 0 |

### Per-Host Detail

Every check result for each host in a table. Sorted by severity so the most important items are at the top.

### Prioritized Remediation Roadmap

This is the section to hand to the client (or work from yourself). Findings are grouped by severity:

- **CRITICAL** — Fix immediately. These are active security risks (root login open, no firewall, empty passwords, SMBv1 enabled, FileVault off).
- **HIGH** — Fix within the engagement window. Missing patches, password auth enabled, no audit logging, dangerous services running.
- **MEDIUM** — Fix as part of hardening. Weak ciphers, missing banners, stale apt cache, missing audit rules.
- **LOW** — Nice to have. Kernel tuning, optional hardening.

Each finding includes the exact fix command or the playbook to run.

### Patch Status Matrix

Shows which hosts need updates, how many, whether a reboot is pending, and how stale the package cache is. Useful for planning a patch window.

---

## Common Workflows

### Initial baseline assessment

Run all three platform audits, review reports, then present findings to the client:

```bash
ansible-playbook -i inventory/acme.ini security-audit.yml
ansible-playbook -i inventory/acme.ini security-audit-windows.yml
ansible-playbook -i inventory/acme.ini security-audit-macos.yml
```

Collect the three reports from `reports/` and consolidate for delivery.

### Post-remediation validation

After applying fixes, re-run the same audits. Compare the new report against the previous one to confirm FAIL counts have dropped:

```bash
# Before: reports/security-audit-2026-02-20.md
# After remediation:
ansible-playbook -i inventory/acme.ini security-audit.yml
# Now: reports/security-audit-2026-02-25.md
```

Tip: Use `diff` to quickly compare:

```bash
diff reports/security-audit-2026-02-20.md reports/security-audit-2026-02-25.md
```

### Patch-only check

Quick check to see which hosts need updates without running the full audit:

```bash
ansible-playbook -i inventory/acme.ini security-audit.yml --tags patches
ansible-playbook -i inventory/acme.ini security-audit-windows.yml --tags patches
ansible-playbook -i inventory/acme.ini security-audit-macos.yml --tags patches
```

### Targeted check after a change

If you just hardened SSH across all hosts, validate only that:

```bash
ansible-playbook -i inventory/acme.ini security-audit.yml --tags ssh
```

### Single-host triage

Client reports an issue on one machine — audit just that host:

```bash
ansible-playbook -i inventory/acme.ini security-audit.yml -l web-1
```

---

## Customizing for a Client

### Change which services are checked

Edit `vars/defaults.yml` in the client's project copy:

```yaml
# Example: client uses CrowdStrike instead of Wazuh
required_services:
  - sshd
  - falcon-sensor
  - auditd
  - fail2ban
```

For Windows, pass inline:

```bash
ansible-playbook -i inventory/acme.ini security-audit-windows.yml \
  -e '{"required_services_win": ["WinDefend", "EventLog", "CrowdStrike Falcon Sensor Service"]}'
```

### Change SSH cipher requirements

Edit `vars/defaults.yml`:

```yaml
approved_ciphers: "aes256-gcm@openssh.com,aes128-gcm@openssh.com"
approved_macs: "hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com"
```

### Add a new check

1. Add a shell/command task in the relevant tag section
2. Register the output
3. Add an entry to the `*_findings` list with `check`, `status`, `severity`, `detail`, `fix`

The finding automatically flows into the summary and report.

### Remove a check temporarily

Don't edit the playbook — use `--skip-tags` instead. This keeps the scaffold clean for reuse.

---

## Troubleshooting

### "Permission denied" or "Authentication failed"

- **Linux/macOS:** Check the SSH key path in inventory, and that the user can sudo (`sudo -l`)
- **Windows:** Verify WinRM is enabled (`winrm enumerate winrm/config/listener`), the user is a local admin, and the firewall allows 5985

### "Host unreachable"

- Check network connectivity: `ping <host-ip>`
- Check SSH/WinRM port is open: `nc -zv <host-ip> 22` or `nc -zv <host-ip> 5985`
- Check firewall rules on the target

### Windows: "winrm connection refused"

Run on the target as Administrator:

```powershell
winrm quickconfig -q
Set-Item WSMan:\localhost\Service\AllowUnencrypted -Value true
Set-Item WSMan:\localhost\Service\Auth\Basic -Value true
```

### macOS: "sudo requires a password"

Either:
- Add `ansible_become_password` to your inventory
- Run with `--ask-become-pass` (will prompt you)
- Configure NOPASSWD sudo for the audit user on the target

### "No hosts matched"

Your inventory doesn't have hosts in the group the playbook expects. Check:
- Linux playbook expects `[linux]` group
- Windows playbook expects `[windows]` group
- macOS playbook expects `[macos]` group

### Slow SUID/SGID scan

Skip it with `--skip-tags slow`. The scan walks the entire filesystem and can take minutes on hosts with large disk.

### Report not generated

The report play runs on `localhost` with the `always` tag. If you ran with `--tags ssh`, the report still generates because it uses the `always` tag. But if the audit play failed before aggregating findings, the report may be empty. Check the playbook output for errors.

### Stale results in report

Each run overwrites the report for that date. If you run multiple times on the same day, only the last run's results are in the report. To keep both, rename the first report before re-running.

---

## Reference

### Available tags by playbook

**Linux (`security-audit.yml`):**
`ssh`, `firewall`, `services`, `filesystem`, `patches`, `auth`, `audit`, `network`, `agents`, `slow`

**Windows (`security-audit-windows.yml`):**
`rdp`, `firewall`, `services`, `filesystem`, `patches`, `auth`, `audit`, `network`, `agents`

**macOS (`security-audit-macos.yml`):**
`ssh`, `encryption`, `firewall`, `services`, `filesystem`, `patches`, `auth`, `audit`, `network`, `agents`

### Report file naming

| Platform | File |
|----------|------|
| Linux | `reports/security-audit-YYYY-MM-DD.md` |
| Windows | `reports/security-audit-windows-YYYY-MM-DD.md` |
| macOS | `reports/security-audit-macos-YYYY-MM-DD.md` |

### Inventory group mapping

| Playbook | Inventory group |
|----------|----------------|
| `security-audit.yml` | `[linux]` |
| `security-audit-windows.yml` | `[windows]` |
| `security-audit-macos.yml` | `[macos]` |

### Severity quick reference

| Severity | Response time | Examples |
|----------|---------------|----------|
| CRITICAL | Immediate | Root login, no firewall, empty passwords, SIP disabled, SMBv1, UAC off, FileVault off, Defender off |
| HIGH | Within engagement | Missing patches, password auth, no auditd, dangerous services, no NLA, no PowerShell logging, guest account |
| MEDIUM | Scheduled hardening | Weak ciphers, missing banners, no AIDE, stale cache, missing audit rules, stealth mode off |
| LOW | Best effort | Kernel tuning, Bonjour, Wi-Fi networks, password hints |

### Useful ansible-vault commands

```bash
# Encrypt a password string
ansible-vault encrypt_string 'MyPassword' --name 'ansible_password'

# Encrypt an entire vars file
ansible-vault encrypt vars/client-secrets.yml

# Run a playbook with vault
ansible-playbook -i inventory/acme.ini security-audit-windows.yml --ask-vault-pass

# Edit an encrypted file
ansible-vault edit vars/client-secrets.yml
```
