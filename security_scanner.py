#!/usr/bin/env python3
"""
Security Scanner Integration for LLMdiver
Integrates multiple security scanning tools for comprehensive vulnerability detection.
"""

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class SecurityFinding:
    """Represents a security vulnerability finding"""
    severity: str  # critical, high, medium, low
    category: str  # sql_injection, xss, hardcoded_secret, etc.
    file_path: str
    line_number: int
    description: str
    cve_id: Optional[str] = None
    confidence: str = "medium"  # high, medium, low
    tool: str = "unknown"
    remediation: Optional[str] = None

@dataclass 
class SecurityScanResult:
    """Complete security scan results"""
    findings: List[SecurityFinding]
    scan_time: float
    tools_used: List[str]
    files_scanned: int
    security_score: float  # 0-100, higher is better
    summary: Dict[str, int]  # Count by severity

class PythonSecurityScanner:
    """Python-specific security scanner using Bandit"""
    
    def __init__(self):
        self.tool_name = "bandit"
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if bandit is available"""
        try:
            result = subprocess.run(['bandit', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan_async(self, repo_path: str) -> List[SecurityFinding]:
        """Scan Python files for security issues"""
        if not self.available:
            logger.warning("Bandit not available, skipping Python security scan")
            return []
        
        findings = []
        try:
            # Run bandit with JSON output
            cmd = [
                'bandit', 
                '-r', repo_path,
                '-f', 'json',
                '--skip', 'B101',  # Skip assert_used test (common in testing)
                '--exclude', '*/test*,*/venv/*,*/node_modules/*'
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 or process.returncode == 1:  # 1 means findings found
                result = json.loads(stdout.decode())
                
                for issue in result.get('results', []):
                    finding = SecurityFinding(
                        severity=self._map_bandit_severity(issue.get('issue_severity', 'MEDIUM')),
                        category=issue.get('test_id', 'unknown'),
                        file_path=issue.get('filename', ''),
                        line_number=issue.get('line_number', 0),
                        description=issue.get('issue_text', ''),
                        confidence=issue.get('issue_confidence', 'MEDIUM').lower(),
                        tool=self.tool_name,
                        remediation=self._get_remediation(issue.get('test_id', ''))
                    )
                    findings.append(finding)
            
            logger.info(f"Bandit scan completed: {len(findings)} findings")
            
        except Exception as e:
            logger.error(f"Bandit scan failed: {e}")
        
        return findings
    
    def _map_bandit_severity(self, bandit_severity: str) -> str:
        """Map Bandit severity to standard levels"""
        mapping = {
            'HIGH': 'high',
            'MEDIUM': 'medium', 
            'LOW': 'low'
        }
        return mapping.get(bandit_severity.upper(), 'medium')
    
    def _get_remediation(self, test_id: str) -> str:
        """Get remediation advice for specific Bandit test"""
        remediations = {
            'B102': 'Avoid using exec(). Use safer alternatives like importlib.',
            'B103': 'Avoid setting permissions too permissively (e.g., 0o777).',
            'B104': 'Avoid binding to all interfaces (0.0.0.0). Be specific about interfaces.',
            'B105': 'Avoid hardcoded passwords. Use environment variables or secure vaults.',
            'B106': 'Avoid hardcoded passwords in function defaults.',
            'B107': 'Avoid hardcoded passwords in function calls.',
            'B108': 'Avoid insecure temporary file creation. Use tempfile module.',
            'B110': 'Avoid try/except/pass blocks. Handle exceptions properly.',
            'B112': 'Avoid try/except/continue blocks without logging.',
            'B201': 'Use of flask with debug=True detected. Ensure debug is disabled in production.',
            'B301': 'Use of pickle detected. Consider using safer serialization formats.',
            'B302': 'Use of marshal detected. Consider using safer serialization formats.',
            'B303': 'Use of insecure MD2, MD4, or MD5 hash function.',
            'B304': 'Use of insecure cipher mode. Use AES with secure modes.',
            'B305': 'Use of insecure cipher. Upgrade to secure encryption.',
            'B306': 'Use of mktemp detected. Use mkstemp instead.',
            'B307': 'Use of eval() detected. Avoid dynamic code execution.',
            'B308': 'Use of mark_safe() may expose XSS vulnerabilities.',
            'B309': 'Use of HTTPSConnection without certificate verification.',
            'B310': 'Audit URL open for permitted schemes.',
            'B311': 'Use of random for security purposes. Use secrets module instead.',
            'B312': 'Use of telnetlib. Consider using SSH instead.',
            'B313': 'Use of xml parsing with security issues. Use defusedxml.',
            'B314': 'Use of xml parsing with security issues. Use defusedxml.',
            'B315': 'Use of xml parsing with security issues. Use defusedxml.',
            'B316': 'Use of xml parsing with security issues. Use defusedxml.',
            'B317': 'Use of xml parsing with security issues. Use defusedxml.',
            'B318': 'Use of xml parsing with security issues. Use defusedxml.',
            'B319': 'Use of xml parsing with security issues. Use defusedxml.',
            'B320': 'Use of xml parsing with security issues. Use defusedxml.',
            'B321': 'Use of FTP-related functions. Consider using SFTP.',
            'B322': 'Use of input() function. In Python 2, this is equivalent to eval().',
            'B323': 'Use of unverified HTTPS context.',
            'B324': 'Use of insecure hash function for security purposes.',
            'B325': 'Use of os.tempnam or os.tmpnam. Use tempfile module instead.',
            'B501': 'Use of SSL/TLS with weak protocol version.',
            'B502': 'Use of SSL/TLS with insecure certificate validation.',
            'B503': 'Use of SSL/TLS with insecure cipher.',
            'B504': 'Use of SSL/TLS with weak key size.',
            'B505': 'Use of weak cryptographic key.',
            'B506': 'Use of YAML load without safe loading.',
            'B507': 'Use of SSH with password authentication.',
            'B601': 'Use of shell injection vulnerable functions.',
            'B602': 'Use of subprocess with shell=True.',
            'B603': 'Use of subprocess without shell escape.',
            'B604': 'Use of function calls with shell=True.',
            'B605': 'Use of os.system or similar shell execution.',
            'B606': 'Use of os.system or similar shell execution.',
            'B607': 'Use of partial executable paths in subprocess.',
            'B608': 'Possible SQL injection via string concatenation.',
            'B609': 'Use of wildcard in Linux command execution.',
            'B610': 'Potential shell injection via Django.',
            'B611': 'Potential shell injection via Django.'
        }
        return remediations.get(test_id, 'Review the security implications of this code pattern.')

class JavaScriptSecurityScanner:
    """JavaScript/Node.js security scanner using ESLint security plugin"""
    
    def __init__(self):
        self.tool_name = "eslint-security"
        self.available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if eslint with security plugin is available"""
        try:
            # Check for npm and eslint
            result = subprocess.run(['npm', 'list', 'eslint-plugin-security'], 
                                  capture_output=True, text=True, timeout=10)
            return 'eslint-plugin-security' in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan_async(self, repo_path: str) -> List[SecurityFinding]:
        """Scan JavaScript files for security issues"""
        if not self.available:
            logger.warning("ESLint security plugin not available, using basic JS pattern scan")
            return await self._basic_js_scan(repo_path)
        
        findings = []
        try:
            # Use ESLint with security plugin
            cmd = [
                'npx', 'eslint',
                '--ext', '.js,.ts,.jsx,.tsx',
                '--format', 'json',
                '--no-eslintrc',
                '--config', self._create_security_config(),
                repo_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=repo_path
            )
            
            stdout, stderr = await process.communicate()
            
            if stdout:
                results = json.loads(stdout.decode())
                for file_result in results:
                    for message in file_result.get('messages', []):
                        finding = SecurityFinding(
                            severity=self._map_eslint_severity(message.get('severity', 1)),
                            category=message.get('ruleId', 'unknown'),
                            file_path=file_result.get('filePath', ''),
                            line_number=message.get('line', 0),
                            description=message.get('message', ''),
                            tool=self.tool_name
                        )
                        findings.append(finding)
            
            logger.info(f"ESLint security scan completed: {len(findings)} findings")
            
        except Exception as e:
            logger.error(f"ESLint security scan failed: {e}")
        
        return findings
    
    async def _basic_js_scan(self, repo_path: str) -> List[SecurityFinding]:
        """Basic JavaScript security pattern matching when ESLint is not available"""
        findings = []
        
        # Security patterns to look for
        patterns = {
            'eval': {'severity': 'high', 'description': 'Use of eval() function detected'},
            'innerHTML': {'severity': 'medium', 'description': 'Use of innerHTML may lead to XSS'},
            'document.write': {'severity': 'medium', 'description': 'Use of document.write may lead to XSS'},
            'setTimeout.*\\(.*[\'"]': {'severity': 'medium', 'description': 'setTimeout with string argument'},
            'setInterval.*\\(.*[\'"]': {'severity': 'medium', 'description': 'setInterval with string argument'},
            'crypto\\.createHash\\([\'"]md5[\'"]\\)': {'severity': 'low', 'description': 'Use of weak MD5 hash'},
            'crypto\\.createHash\\([\'"]sha1[\'"]\\)': {'severity': 'low', 'description': 'Use of weak SHA1 hash'},
        }
        
        try:
            for js_file in Path(repo_path).rglob("*.js"):
                if 'node_modules' in str(js_file):
                    continue
                
                try:
                    with open(js_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                        for pattern, info in patterns.items():
                            for line_num, line in enumerate(lines, 1):
                                if re.search(pattern, line, re.IGNORECASE):
                                    finding = SecurityFinding(
                                        severity=info['severity'],
                                        category='javascript-pattern',
                                        file_path=str(js_file),
                                        line_number=line_num,
                                        description=info['description'],
                                        tool='basic-js-scanner'
                                    )
                                    findings.append(finding)
                except Exception as e:
                    logger.warning(f"Failed to scan {js_file}: {e}")
        
        except Exception as e:
            logger.error(f"Basic JS scan failed: {e}")
        
        return findings
    
    def _create_security_config(self) -> str:
        """Create ESLint security configuration"""
        config = {
            "plugins": ["security"],
            "rules": {
                "security/detect-buffer-noassert": "error",
                "security/detect-child-process": "error", 
                "security/detect-disable-mustache-escape": "error",
                "security/detect-eval-with-expression": "error",
                "security/detect-new-buffer": "error",
                "security/detect-no-csrf-before-method-override": "error",
                "security/detect-non-literal-fs-filename": "error",
                "security/detect-non-literal-regexp": "error",
                "security/detect-non-literal-require": "error",
                "security/detect-object-injection": "error",
                "security/detect-possible-timing-attacks": "error",
                "security/detect-pseudoRandomBytes": "error",
                "security/detect-unsafe-regex": "error"
            }
        }
        
        config_path = "/tmp/eslint-security-config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        return config_path
    
    def _map_eslint_severity(self, eslint_severity: int) -> str:
        """Map ESLint severity to standard levels"""
        if eslint_severity >= 2:
            return 'high'
        elif eslint_severity == 1:
            return 'medium'
        else:
            return 'low'

class DependencySecurityScanner:
    """Scanner for known vulnerabilities in dependencies"""
    
    def __init__(self):
        self.tool_name = "dependency-scanner"
    
    async def scan_async(self, repo_path: str) -> List[SecurityFinding]:
        """Scan dependencies for known vulnerabilities"""
        findings = []
        
        # Check Python dependencies
        requirements_files = list(Path(repo_path).glob("**/requirements*.txt"))
        for req_file in requirements_files:
            python_findings = await self._scan_python_deps(req_file)
            findings.extend(python_findings)
        
        # Check Node.js dependencies
        package_files = list(Path(repo_path).glob("**/package.json"))
        for pkg_file in package_files:
            node_findings = await self._scan_node_deps(pkg_file)
            findings.extend(node_findings)
        
        return findings
    
    async def _scan_python_deps(self, requirements_file: Path) -> List[SecurityFinding]:
        """Scan Python requirements file for known vulnerabilities"""
        findings = []
        
        try:
            # Try using safety if available
            cmd = ['safety', 'check', '-r', str(requirements_file), '--json']
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # No vulnerabilities found
                return findings
            elif stdout:
                # Parse safety JSON output
                try:
                    results = json.loads(stdout.decode())
                    for vuln in results:
                        finding = SecurityFinding(
                            severity='high',  # All safety findings are considered high
                            category='dependency-vulnerability',
                            file_path=str(requirements_file),
                            line_number=0,
                            description=f"{vuln.get('package_name')}: {vuln.get('advisory')}",
                            cve_id=vuln.get('id'),
                            tool='safety'
                        )
                        findings.append(finding)
                except json.JSONDecodeError:
                    pass
        
        except FileNotFoundError:
            # Safety not available, do basic checks
            findings.extend(await self._basic_python_dep_scan(requirements_file))
        except Exception as e:
            logger.warning(f"Python dependency scan failed: {e}")
        
        return findings
    
    async def _scan_node_deps(self, package_file: Path) -> List[SecurityFinding]:
        """Scan Node.js package.json for known vulnerabilities"""
        findings = []
        
        try:
            # Try using npm audit
            cmd = ['npm', 'audit', '--json']
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=package_file.parent
            )
            
            stdout, stderr = await process.communicate()
            
            if stdout:
                try:
                    results = json.loads(stdout.decode())
                    vulnerabilities = results.get('vulnerabilities', {})
                    
                    for pkg_name, vuln_info in vulnerabilities.items():
                        finding = SecurityFinding(
                            severity=vuln_info.get('severity', 'medium'),
                            category='dependency-vulnerability',
                            file_path=str(package_file),
                            line_number=0,
                            description=f"{pkg_name}: {vuln_info.get('title', 'Security vulnerability')}",
                            cve_id=vuln_info.get('cves', [None])[0],
                            tool='npm-audit'
                        )
                        findings.append(finding)
                        
                except json.JSONDecodeError:
                    pass
        
        except Exception as e:
            logger.warning(f"Node.js dependency scan failed: {e}")
        
        return findings
    
    async def _basic_python_dep_scan(self, requirements_file: Path) -> List[SecurityFinding]:
        """Basic Python dependency vulnerability check"""
        findings = []
        
        # Known vulnerable packages/versions (simplified check)
        vulnerable_packages = {
            'django': {'versions': ['<2.2.10', '<3.0.3'], 'description': 'Django has known security vulnerabilities in older versions'},
            'flask': {'versions': ['<1.0'], 'description': 'Flask has security issues in versions before 1.0'},
            'requests': {'versions': ['<2.20.0'], 'description': 'Requests has SSL verification issues in older versions'},
            'pyyaml': {'versions': ['<5.1'], 'description': 'PyYAML has arbitrary code execution vulnerability'},
        }
        
        try:
            with open(requirements_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Simple package name extraction
                        pkg_name = re.split('[>=<~!]', line)[0].strip()
                        
                        if pkg_name.lower() in vulnerable_packages:
                            vuln_info = vulnerable_packages[pkg_name.lower()]
                            finding = SecurityFinding(
                                severity='medium',
                                category='dependency-vulnerability',
                                file_path=str(requirements_file),
                                line_number=line_num,
                                description=f"{pkg_name}: {vuln_info['description']}",
                                tool='basic-dep-scanner'
                            )
                            findings.append(finding)
        
        except Exception as e:
            logger.warning(f"Basic Python dep scan failed: {e}")
        
        return findings

class SecurityScanner:
    """Main security scanner orchestrator"""
    
    def __init__(self):
        self.scanners = {
            'python': PythonSecurityScanner(),
            'javascript': JavaScriptSecurityScanner(),
            'dependencies': DependencySecurityScanner()
        }
        logger.info("Initialized security scanner with available tools")
    
    async def comprehensive_scan(self, repo_path: str) -> SecurityScanResult:
        """Perform comprehensive security scan"""
        start_time = asyncio.get_event_loop().time()
        all_findings = []
        tools_used = []
        
        # Run all scanners in parallel
        scan_tasks = []
        for scanner_name, scanner in self.scanners.items():
            if hasattr(scanner, 'available') and not scanner.available:
                logger.info(f"Skipping {scanner_name} scanner - not available")
                continue
            
            scan_tasks.append(self._run_scanner(scanner_name, scanner, repo_path))
            tools_used.append(scanner.tool_name)
        
        # Wait for all scans to complete
        scan_results = await asyncio.gather(*scan_tasks, return_exceptions=True)
        
        # Collect findings
        for result in scan_results:
            if isinstance(result, list):
                all_findings.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Scanner failed: {result}")
        
        # Calculate metrics
        scan_time = asyncio.get_event_loop().time() - start_time
        files_scanned = self._count_files(repo_path)
        security_score = self._calculate_security_score(all_findings, files_scanned)
        summary = self._summarize_findings(all_findings)
        
        result = SecurityScanResult(
            findings=all_findings,
            scan_time=scan_time,
            tools_used=tools_used,
            files_scanned=files_scanned,
            security_score=security_score,
            summary=summary
        )
        
        logger.info(f"Security scan completed: {len(all_findings)} findings, score: {security_score:.1f}/100")
        return result
    
    async def _run_scanner(self, name: str, scanner, repo_path: str) -> List[SecurityFinding]:
        """Run individual scanner with error handling"""
        try:
            logger.info(f"Running {name} security scanner...")
            findings = await scanner.scan_async(repo_path)
            logger.info(f"{name} scanner found {len(findings)} issues")
            return findings
        except Exception as e:
            logger.error(f"{name} scanner failed: {e}")
            return []
    
    def _count_files(self, repo_path: str) -> int:
        """Count scannable files in repository"""
        extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.json'}
        count = 0
        
        try:
            for file_path in Path(repo_path).rglob("*"):
                if file_path.is_file() and file_path.suffix in extensions:
                    if 'node_modules' not in str(file_path) and '.git' not in str(file_path):
                        count += 1
        except Exception:
            pass
        
        return count
    
    def _calculate_security_score(self, findings: List[SecurityFinding], file_count: int) -> float:
        """Calculate security score (0-100, higher is better)"""
        if file_count == 0:
            return 100.0
        
        # Weight findings by severity
        severity_weights = {'critical': 10, 'high': 5, 'medium': 2, 'low': 1}
        total_penalty = sum(severity_weights.get(f.severity, 1) for f in findings)
        
        # Base score calculation
        penalty_per_file = total_penalty / file_count
        score = max(0, 100 - (penalty_per_file * 10))
        
        return round(score, 1)
    
    def _summarize_findings(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """Summarize findings by severity"""
        summary = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for finding in findings:
            severity = finding.severity.lower()
            if severity in summary:
                summary[severity] += 1
        
        return summary
    
    def get_scanner_status(self) -> Dict[str, bool]:
        """Get status of all security scanners"""
        status = {}
        for name, scanner in self.scanners.items():
            status[name] = getattr(scanner, 'available', True)
        return status

# Integration example
async def example_security_scan():
    """Example of how to use the security scanner"""
    scanner = SecurityScanner()
    result = await scanner.comprehensive_scan("/path/to/repo")
    
    print(f"Security Score: {result.security_score}/100")
    print(f"Findings Summary: {result.summary}")
    
    for finding in result.findings:
        print(f"{finding.severity.upper()}: {finding.description} ({finding.file_path}:{finding.line_number})")

if __name__ == "__main__":
    asyncio.run(example_security_scan())