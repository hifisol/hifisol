# Halbert Farias

**Security Engineer & IT Consultant** | Detection Engineering | SOC Infrastructure | Network Security | Automation

Founder of an IT consulting startup focused on security monitoring, vulnerability assessment, and threat detection for small and mid-sized businesses in Northwest Indiana. I build and operate production-grade security infrastructure — from SIEM tuning and endpoint forensics to network architecture and automated hardening.

---

## What I Do

**Daily Security Operations**
- SIEM-based monitoring and alert triage using Wazuh with 100+ custom detection rules mapped to MITRE ATT&CK
- Endpoint investigation with Velociraptor EDR and network anomaly analysis with Zeek IDS
- Structured investigation reports with timelines, artifacts, and observables

**Infrastructure & Network Security**
- Segmented VLAN architectures and hardened server environments on Ubiquiti UniFi (Dream Machine Pro, managed switches, wireless APs)
- Firewall rules, security zones, and DMZ configuration to control network traffic
- Multi-node virtualized lab on Proxmox VE hosting Windows Server, Linux VMs, and containerized services

**Automation & Hardening**
- Ansible playbooks for agent deployment, CIS-aligned hardening, and infrastructure provisioning
- CVE enrichment pipeline integrating NVD API and EPSS scoring for automatic risk-scoring of vulnerability alerts
- Active Directory domain administration with security posture evaluation using PingCastle against CIS benchmarks

**Consulting Services**
- Network architecture design, hardware deployment, structured cabling, and security monitoring
- Vulnerability assessments using GVM/OpenVAS with findings mapped to MITRE ATT&CK for context-aware prioritization
- Regular security audits across client infrastructure

---

## Security Stack

| Layer | Tools |
|-------|-------|
| **SIEM & Detection** | Wazuh (100+ custom rules, MITRE ATT&CK mapped, Discord alerting) |
| **Network Monitoring** | Zeek IDS with custom decoders, RITA/AC-Hunter C2 beacon analysis |
| **Endpoint Security** | Velociraptor EDR, Wazuh FIM/SCA, Sysmon, DeepBlueCLI |
| **Vulnerability Management** | GVM/OpenVAS, CVE enrichment (NVD + EPSS), PingCastle AD audits |
| **Network Infrastructure** | Ubiquiti UniFi (UDM Pro, switches, APs), VLAN segmentation, Tailscale overlay |
| **AI-Driven Hunting** | Ares — local LLM orchestrator (Ollama) for autonomous threat hunts, CVE enrichment (NVD + EPSS), RAG knowledge base |
| **Automation** | Ansible (20+ playbooks), Bash, Python, Docker, Proxmox VE |
| **Compliance** | CIS Benchmarks, server hardening, security baseline automation |

---

## Repositories

| Repository | Description |
|-----------|-------------|
| [homelab-soc-infrastructure](https://github.com/hifisol/homelab-soc-infrastructure) | Full SOC stack — detection rules, Ansible automation, Docker services, persistence scripts, and architecture docs |
| [infrastructure-automation](infrastructure-automation/) | Ansible playbooks for agent deployment, CIS-aligned security audits, multi-platform health checks, and DeepBlueCLI integration |
| [adversarial-emulation](https://github.com/hifisol/adversarial-emulation) | Offensive security tooling — WiFi pentesting, hardware implants, Metasploit methodology, physical pentest guides |
| [ares](https://github.com/hifisol/ares) | LLM-powered threat hunting orchestrator — uses local Ollama models to coordinate Wazuh, Zeek, RITA, and Velociraptor for autonomous hunt workflows with NIST SP 800-61 reporting |
| [ares-watchtower-public](https://github.com/hifisol/ares-watchtower-public) | Real-time security dashboard — Wazuh alert browser, CVE enrichment viewer (CVSS/EPSS), RITA beacon visualization, Zeek network log explorer |

---

## Lab Infrastructure

- **Compute** — Proxmox VE cluster hosting Windows Server, Linux VMs, LXC containers, and Active Directory domain
- **Network** — Ubiquiti UniFi stack (UDM Pro, managed switches, APs) with segmented VLANs, firewall rules, and IDS/IPS
- **Storage** — TrueNAS SCALE with ZFS pools for backups, ISOs, and evidence retention
- **Monitoring** — Wazuh SIEM, Velociraptor EDR, Zeek IDS, GVM vulnerability scanning, Zabbix infrastructure monitoring
- **Purple Team** — Active Directory attack/defense lab with mapped detection rules and emulation scenarios

---

## Contact

- [LinkedIn](https://www.linkedin.com/in/halbert-farias)
