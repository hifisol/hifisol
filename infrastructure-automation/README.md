# Infrastructure Automation

HiFi Solutions — Ansible playbooks for client infrastructure health checks, security baseline assessments, agent deployment, and ongoing management.

## Toolkits

| Toolkit | Path | Purpose |
|---------|------|---------|
| **Health Check** | `ansible/hifi-health-check/` | Multi-platform hardware & service health assessment with reports |
| **Security Audit** | `ansible/hifi-security-audit/` | CIS-aligned security baseline compliance audit with remediation roadmap |
| **Agent Management** | `ansible/` | Security agent status checks and deployment (TRMM, Wazuh, Tailscale) |

## Platform Support

| Platform | Health Check | Security Audit | Agent Deploy |
|----------|-------------|----------------|--------------|
| Linux | `health-check.yml` | `security-audit.yml` | `check-agents_v2.yml` |
| Windows | `health-check-windows.yml` | `security-audit-windows.yml` | — |
| macOS | `health-check-macos.yml` | `security-audit-macos.yml` | — |

## Quick Start

```bash
# Clone
git clone https://github.com/hifisol/hifisol.git
cd infrastructure-automation

# Copy a toolkit for a new client engagement
cp -r ansible/hifi-health-check/ ansible/<client>-health-check/

# Create client inventory
cp ansible/<client>-health-check/inventory/example.ini ansible/<client>-health-check/inventory/<client>.ini

# Run
ansible-playbook -i ansible/<client>-health-check/inventory/<client>.ini \
  ansible/<client>-health-check/health-check.yml
```

## Structure

```
infrastructure-automation/
├── ansible/
│   ├── hifi-health-check/           # Health check scaffold
│   │   ├── health-check.yml         # Linux
│   │   ├── health-check-windows.yml # Windows
│   │   ├── health-check-macos.yml   # macOS
│   │   ├── templates/               # Report templates
│   │   ├── inventory/               # Example inventory
│   │   ├── vars/                    # Tunable defaults
│   │   ├── reports/                 # Generated reports
│   │   ├── GUIDE.md                 # User guide
│   │   └── README.md
│   ├── hifi-security-audit/         # Security audit scaffold
│   │   ├── security-audit.yml       # Linux
│   │   ├── security-audit-windows.yml
│   │   ├── security-audit-macos.yml
│   │   ├── templates/
│   │   ├── inventory/
│   │   ├── vars/
│   │   ├── reports/
│   │   ├── GUIDE.md
│   │   └── README.md
│   ├── check-agents_v2.yml          # Agent status checker
│   └── install-trmm-agent.yml       # TRMM agent installer
├── docs/
│   └── deepbluecli.md               # DeepBlueCLI setup, syntax, Wazuh integration
└── README.md
```

## Threat Hunting

| Tool | Doc | Purpose |
|------|-----|---------|
| **DeepBlueCLI** | [docs/deepbluecli.md](docs/deepbluecli.md) | Windows event log analysis — password spray, mimikatz, obfuscated PowerShell, log clearing, brute force, suspicious services |

## Documentation

Each toolkit includes its own README and detailed GUIDE:

- [Health Check README](ansible/hifi-health-check/README.md)
- [Health Check Guide](ansible/hifi-health-check/GUIDE.md)
- [Security Audit README](ansible/hifi-security-audit/README.md)
- [Security Audit Guide](ansible/hifi-security-audit/GUIDE.md)
- [DeepBlueCLI Reference](docs/deepbluecli.md)

## Requirements

| Requirement | Install |
|-------------|---------|
| Ansible 2.12+ | `pip install ansible` |
| pywinrm (Windows targets) | `pip install pywinrm` |
