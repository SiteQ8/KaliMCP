<div align="center">

# KaliMCP

### Automate Kali Linux Pentesting with MCP

[![Tools](https://img.shields.io/badge/27-MCP_Tools-00ff88?style=flat-square)]()
[![Categories](https://img.shields.io/badge/8-Categories-00d4ff?style=flat-square)]()
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square)]()
[![Docker](https://img.shields.io/badge/Docker-Test_Mode-2496ED?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-gold?style=flat-square)]()

**Live Demo:** [siteq8.github.io/KaliMCP](https://siteq8.github.io/KaliMCP) · **Repo:** [github.com/SiteQ8/KaliMCP](https://github.com/SiteQ8/KaliMCP)

Programmatic access to 27 Kali Linux tools via Model Context Protocol.
SSH and reverse shell management, file operations, Docker test labs.
Perfect for CTFs, security research, and automated reporting.

</div>

---

## Quick Start

```bash
git clone https://github.com/SiteQ8/KaliMCP.git
cd KaliMCP
python3 scripts/kalimcp_server.py --port 7070
```

### Call a Tool

```bash
# Nmap scan with vuln scripts
curl -X POST http://localhost:7070 \
  -d '{"method":"tools/call","params":{"name":"nmap_scan","arguments":{"target":"10.10.10.1","scan_type":"vuln"}}}'

# Search for exploits
curl -X POST http://localhost:7070 \
  -d '{"method":"tools/call","params":{"name":"searchsploit","arguments":{"query":"Apache 2.4.49"}}}'

# Generate reverse shell payloads
curl -X POST http://localhost:7070 \
  -d '{"method":"tools/call","params":{"name":"reverse_shell_listener","arguments":{"port":4444}}}'
```

---

## 27 Tools in 8 Categories

### Reconnaissance (5)
| Tool | Description |
|------|-------------|
| `nmap_scan` | 8 scan profiles: quick, default, full, udp, stealth, vuln, os, aggressive |
| `masscan_scan` | Ultra-fast full port scan (65535 ports) |
| `dns_enum` | DNS enumeration via dnsenum, dnsrecon, or fierce |
| `whois_lookup` | WHOIS domain/IP lookup |
| `theharvester` | Email, subdomain, IP harvesting from OSINT sources |

### Web Application (6)
| Tool | Description |
|------|-------------|
| `nikto_scan` | Web vulnerability scanner (6700+ tests) |
| `dirb_scan` | Directory brute-force |
| `gobuster_scan` | Dir/DNS/vhost enumeration (50 threads) |
| `sqlmap_scan` | Automated SQL injection detection |
| `whatweb_scan` | Technology fingerprinting |
| `wfuzz_scan` | Web application fuzzer |

### Exploitation (3)
| Tool | Description |
|------|-------------|
| `searchsploit` | Search Exploit-DB (JSON output with exploit details) |
| `hydra_attack` | Network brute-force (SSH, FTP, HTTP, SMB, RDP, MySQL) |
| `msf_search` | Metasploit module search |

### Password (2)
| Tool | Description |
|------|-------------|
| `john_crack` | John the Ripper with wordlist + format support |
| `hashid` | Hash type identification |

### OSINT (2)
| Tool | Description |
|------|-------------|
| `subfinder_scan` | Fast passive subdomain discovery |
| `amass_enum` | Comprehensive DNS intelligence |

### Post-Exploitation (2)
| Tool | Description |
|------|-------------|
| `enumerate_system` | Local privesc recon (users, SUID, cron, kernel, network) |
| `linpeas` | Download latest LinPEAS scanner |

### Shell Management (4)
| Tool | Description |
|------|-------------|
| `ssh_connect` | SSH session with password/key auth |
| `ssh_exec` | Execute commands on SSH sessions |
| `reverse_shell_listener` | 6 payload types (bash, python, nc, php, powershell, perl) + listener |
| `list_sessions` | List active sessions |

### Files + Reporting (4)
| Tool | Description |
|------|-------------|
| `file_upload` | Stage file with transfer methods (HTTP, nc, base64, scp) |
| `file_download` | Download from URL |
| `generate_report` | JSON pentest report with severity stats |
| `docker_lab_setup` | 5 Docker vulnerable labs |

---

## Docker Test Mode

Safe practice environments:

```bash
# DVWA
docker run -d -p 8081:80 --name dvwa vulnerables/web-dvwa

# OWASP Juice Shop
docker run -d -p 3000:3000 --name juice bkimminich/juice-shop

# Metasploitable
docker run -d -p 8082:80 -p 2222:22 --name meta tleemcjr/metasploitable2

# WebGoat
docker run -d -p 8083:8080 --name webgoat webgoat/webgoat
```

---

## Pentest Workflow

```
1. RECON     → nmap_scan → dns_enum → whois_lookup → theharvester
2. WEB       → whatweb_scan → gobuster_scan → nikto_scan
3. VULN      → sqlmap_scan → searchsploit
4. EXPLOIT   → hydra_attack → ssh_connect
5. POST      → enumerate_system → linpeas
6. REPORT    → generate_report
```

---

## Legal Disclaimer

This tool is for **authorized security testing only**. Always obtain written permission before testing any system you do not own. Unauthorized access to computer systems is illegal.

---

## Author

**Ali AlEnezi** · [@SiteQ8](https://github.com/SiteQ8) · [3li.info](https://3li.info)

Security Architecture Principal · National Bank of Kuwait (NBK Group) 🇰🇼

GPEN · GWEB · GDSA · GICSP · GCCC · PCI DSS Professional
