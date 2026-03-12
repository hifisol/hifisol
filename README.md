# Halbert Farias

**Information Security Engineer** | Detection Engineering | SOC Infrastructure | Automation

I build and operate a production-grade Security Operations Center from my homelab, focused on real-world threat detection, network monitoring, and infrastructure automation.

---

## What I'm Building

A multi-tool SOC stack that mirrors enterprise security operations:

- **SIEM & Detection** — Wazuh manager with 100+ custom detection rules, real-time alerting to Discord, MITRE ATT&CK mapped
- **Network Monitoring** — Zeek packet capture with custom decoders feeding into Wazuh for protocol-level threat detection
- **Beacon Analysis** — RITA/AC-Hunter for C2 beacon detection, automated exports to Wazuh with tiered alerting
- **Endpoint Visibility** — Velociraptor DFIR across Linux and Windows endpoints
- **Vulnerability Management** — GVM/OpenVAS scanning and reporting
- **Infrastructure Automation** — 20+ Ansible playbooks for agent deployment, CIS hardening, and AD lab orchestration
- **Network Security** — VLAN segmentation, UDM Pro IDS/IPS, Tailscale overlay network

## Repositories

| Repository | Description |
|-----------|-------------|
| [homelab-soc-infrastructure](https://github.com/hifisol/homelab-soc-infrastructure) | Full SOC stack — detection rules, Ansible automation, Docker services, persistence scripts, and architecture docs |
| [infrastructure-automation](infrastructure-automation/) | Ansible playbooks for agent deployment, CIS-aligned security audits, multi-platform health checks, and DeepBlueCLI integration |
| [adversarial-emulation](https://github.com/hifisol/adversarial-emulation) | Offensive security tooling — WiFi pentesting, hardware implants, Metasploit methodology, physical pentest guides |

## Tools & Skills

**SIEM & Detection Engineering**
Wazuh, Zeek, RITA, AC-Hunter, Sigma Rules, MITRE ATT&CK, PCRE2 Regex

**Network Security**
Zeek NSM, RITA Beacon Analysis, Wireshark, UDM Pro IDS/IPS, VLAN Segmentation, Tailscale

**Endpoint Security & DFIR**
Velociraptor, Wazuh FIM/SCA, Sysmon, Windows Event Log Analysis

**Vulnerability Management**
GVM/OpenVAS, Nmap, Vulnerability Scanning & Remediation

**Automation & Infrastructure**
Ansible, Bash, Python, Docker, Proxmox, TrueNAS SCALE, Git

**Compliance**
CIS Benchmarks, Server Hardening, Security Baseline Automation

## Currently Working On

- Expanding Zeek detection coverage for lateral movement and credential abuse
- Building automated Active Directory attack/defense lab scenarios
- CIS benchmark automation for Linux server fleet

## Contact

- [LinkedIn](https://www.linkedin.com/in/halbert-farias)
