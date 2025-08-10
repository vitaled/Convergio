#!/usr/bin/env python3
"""
OWASP Security Testing for Convergio
Tests against OWASP Top 10 vulnerabilities
"""

import requests
import json
import time
import random
import string
from typing import Dict, List, Any
from datetime import datetime

class OWASPSecurityTester:
    def __init__(self, base_url: str = "http://localhost:9000"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "passed": 0,
            "failed": 0
        }
    
    def run_tests(self):
        """Run all OWASP security tests"""
        print("====================================")
        print("OWASP TOP 10 SECURITY TESTING")
        print("====================================\n")
        
        # A01:2021 – Broken Access Control
        self.test_broken_access_control()
        
        # A02:2021 – Cryptographic Failures
        self.test_cryptographic_failures()
        
        # A03:2021 – Injection
        self.test_injection_attacks()
        
        # A04:2021 – Insecure Design
        self.test_insecure_design()
        
        # A05:2021 – Security Misconfiguration
        self.test_security_misconfiguration()
        
        # A06:2021 – Vulnerable and Outdated Components
        self.test_vulnerable_components()
        
        # A07:2021 – Identification and Authentication Failures
        self.test_authentication_failures()
        
        # A08:2021 – Software and Data Integrity Failures
        self.test_integrity_failures()
        
        # A09:2021 – Security Logging and Monitoring Failures
        self.test_logging_monitoring()
        
        # A10:2021 – Server-Side Request Forgery
        self.test_ssrf()
        
        # Generate report
        self.generate_report()
    
    def test_broken_access_control(self):
        """Test for broken access control vulnerabilities"""
        print("A01:2021 - Broken Access Control")
        print("-" * 33)
        
        tests = []
        
        # Test 1: Direct object reference
        test = {
            "name": "Direct Object Reference",
            "description": "Attempt to access other users' data",
            "status": "PASS"
        }
        
        try:
            # Try to access user data without authentication
            response = requests.get(f"{self.base_url}/api/users/1", timeout=5)
            if response.status_code != 401 and response.status_code != 403:
                test["status"] = "FAIL"
                test["reason"] = f"Unauthorized access allowed (status: {response.status_code})"
        except:
            test["status"] = "SKIP"
            test["reason"] = "API not available"
        
        tests.append(test)
        self.print_test_result(test)
        
        # Test 2: Path traversal
        test = {
            "name": "Path Traversal",
            "description": "Attempt directory traversal attack",
            "status": "PASS"
        }
        
        try:
            payloads = ["../../etc/passwd", "../../../windows/system32/config/sam"]
            for payload in payloads:
                response = requests.get(f"{self.base_url}/api/files/{payload}", timeout=5)
                if response.status_code == 200:
                    test["status"] = "FAIL"
                    test["reason"] = "Path traversal vulnerability detected"
                    break
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        # Test 3: Privilege escalation
        test = {
            "name": "Privilege Escalation",
            "description": "Attempt to access admin functions",
            "status": "PASS"
        }
        
        try:
            # Try to access admin endpoint with regular user token
            headers = {"Authorization": "Bearer fake_user_token"}
            response = requests.get(f"{self.base_url}/api/admin/users", headers=headers, timeout=5)
            if response.status_code == 200:
                test["status"] = "FAIL"
                test["reason"] = "Admin access allowed with user token"
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        self.results["tests"].extend(tests)
        print()
    
    def test_cryptographic_failures(self):
        """Test for cryptographic failures"""
        print("A02:2021 - Cryptographic Failures")
        print("-" * 34)
        
        tests = []
        
        # Test 1: Sensitive data in transit
        test = {
            "name": "Data in Transit Encryption",
            "description": "Check for HTTPS enforcement",
            "status": "PASS"
        }
        
        # Check if HTTP redirects to HTTPS
        try:
            response = requests.get(f"http://localhost:9000/api/health", allow_redirects=False, timeout=5)
            if "location" in response.headers and "https" in response.headers["location"].lower():
                test["status"] = "PASS"
            else:
                test["status"] = "WARNING"
                test["reason"] = "HTTP not redirecting to HTTPS"
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        # Test 2: Weak encryption algorithms
        test = {
            "name": "Strong Encryption Algorithms",
            "description": "Check for weak crypto usage",
            "status": "PASS"
        }
        
        # This would require code analysis
        test["status"] = "INFO"
        test["reason"] = "Requires code review"
        
        tests.append(test)
        self.print_test_result(test)
        
        self.results["tests"].extend(tests)
        print()
    
    def test_injection_attacks(self):
        """Test for injection vulnerabilities"""
        print("A03:2021 - Injection")
        print("-" * 21)
        
        tests = []
        
        # Test 1: SQL Injection
        test = {
            "name": "SQL Injection",
            "description": "Test SQL injection payloads",
            "status": "PASS"
        }
        
        sql_payloads = [
            "' OR '1'='1",
            "1; DROP TABLE users--",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ]
        
        try:
            for payload in sql_payloads:
                response = requests.get(
                    f"{self.base_url}/api/search",
                    params={"q": payload},
                    timeout=5
                )
                # Check if error messages leak database info
                if response.text and any(word in response.text.lower() for word in ["syntax", "mysql", "postgresql", "sqlite"]):
                    test["status"] = "FAIL"
                    test["reason"] = "Database error messages exposed"
                    break
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        # Test 2: NoSQL Injection
        test = {
            "name": "NoSQL Injection",
            "description": "Test NoSQL injection payloads",
            "status": "PASS"
        }
        
        nosql_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$regex": ".*"}
        ]
        
        try:
            for payload in nosql_payloads:
                response = requests.post(
                    f"{self.base_url}/api/login",
                    json={"username": payload, "password": "test"},
                    timeout=5
                )
                if response.status_code == 200:
                    test["status"] = "FAIL"
                    test["reason"] = "NoSQL injection vulnerability detected"
                    break
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        # Test 3: Command Injection
        test = {
            "name": "Command Injection",
            "description": "Test OS command injection",
            "status": "PASS"
        }
        
        cmd_payloads = [
            "; ls -la",
            "| whoami",
            "$(cat /etc/passwd)",
            "`id`"
        ]
        
        try:
            for payload in cmd_payloads:
                response = requests.post(
                    f"{self.base_url}/api/process",
                    json={"input": payload},
                    timeout=5
                )
                # Check for command output in response
                if response.text and any(word in response.text for word in ["root:", "uid=", "total"]):
                    test["status"] = "FAIL"
                    test["reason"] = "Command injection vulnerability detected"
                    break
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        # Test 4: XSS (Cross-Site Scripting)
        test = {
            "name": "XSS Protection",
            "description": "Test XSS payloads",
            "status": "PASS"
        }
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ]
        
        try:
            for payload in xss_payloads:
                response = requests.post(
                    f"{self.base_url}/api/comments",
                    json={"comment": payload},
                    timeout=5
                )
                # Check if payload is reflected without encoding
                if response.text and payload in response.text:
                    test["status"] = "FAIL"
                    test["reason"] = "XSS vulnerability detected - payload not sanitized"
                    break
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        self.results["tests"].extend(tests)
        print()
    
    def test_insecure_design(self):
        """Test for insecure design issues"""
        print("A04:2021 - Insecure Design")
        print("-" * 27)
        
        tests = []
        
        # Test 1: Rate limiting
        test = {
            "name": "Rate Limiting",
            "description": "Check for rate limiting on sensitive endpoints",
            "status": "PASS"
        }
        
        try:
            # Try rapid requests to login endpoint
            for _ in range(20):
                response = requests.post(
                    f"{self.base_url}/api/login",
                    json={"username": "test", "password": "wrong"},
                    timeout=1
                )
            
            if response.status_code != 429:  # 429 = Too Many Requests
                test["status"] = "WARNING"
                test["reason"] = "No rate limiting detected on login endpoint"
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        # Test 2: Business logic flaws
        test = {
            "name": "Business Logic Security",
            "description": "Test for business logic vulnerabilities",
            "status": "INFO"
        }
        test["reason"] = "Requires manual testing based on business rules"
        
        tests.append(test)
        self.print_test_result(test)
        
        self.results["tests"].extend(tests)
        print()
    
    def test_security_misconfiguration(self):
        """Test for security misconfiguration"""
        print("A05:2021 - Security Misconfiguration")
        print("-" * 37)
        
        tests = []
        
        # Test 1: Default credentials
        test = {
            "name": "Default Credentials",
            "description": "Test for default usernames and passwords",
            "status": "PASS"
        }
        
        default_creds = [
            ("admin", "admin"),
            ("admin", "password"),
            ("root", "root"),
            ("test", "test")
        ]
        
        try:
            for username, password in default_creds:
                response = requests.post(
                    f"{self.base_url}/api/login",
                    json={"username": username, "password": password},
                    timeout=5
                )
                if response.status_code == 200:
                    test["status"] = "FAIL"
                    test["reason"] = f"Default credentials accepted: {username}:{password}"
                    break
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        # Test 2: Security headers
        test = {
            "name": "Security Headers",
            "description": "Check for security headers",
            "status": "PASS"
        }
        
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "Content-Security-Policy",
            "Strict-Transport-Security"
        ]
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            missing_headers = [h for h in required_headers if h not in response.headers]
            
            if missing_headers:
                test["status"] = "WARNING"
                test["reason"] = f"Missing headers: {', '.join(missing_headers)}"
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        # Test 3: Error handling
        test = {
            "name": "Error Handling",
            "description": "Check for information disclosure in errors",
            "status": "PASS"
        }
        
        try:
            # Trigger an error
            response = requests.get(f"{self.base_url}/api/nonexistent", timeout=5)
            
            # Check for stack traces or sensitive info
            if response.text and any(word in response.text.lower() for word in ["traceback", "stack trace", "at line", "file"]):
                test["status"] = "FAIL"
                test["reason"] = "Stack trace exposed in error response"
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        self.results["tests"].extend(tests)
        print()
    
    def test_vulnerable_components(self):
        """Test for vulnerable and outdated components"""
        print("A06:2021 - Vulnerable and Outdated Components")
        print("-" * 47)
        
        tests = []
        
        test = {
            "name": "Component Vulnerability Scan",
            "description": "Check for known vulnerable dependencies",
            "status": "INFO"
        }
        test["reason"] = "Run 'npm audit' and 'pip-audit' for detailed results"
        
        tests.append(test)
        self.print_test_result(test)
        
        self.results["tests"].extend(tests)
        print()
    
    def test_authentication_failures(self):
        """Test for authentication failures"""
        print("A07:2021 - Identification and Authentication Failures")
        print("-" * 54)
        
        tests = []
        
        # Test 1: Weak password policy
        test = {
            "name": "Password Policy",
            "description": "Test weak password acceptance",
            "status": "PASS"
        }
        
        weak_passwords = ["123", "password", "12345678", "qwerty"]
        
        try:
            for password in weak_passwords:
                response = requests.post(
                    f"{self.base_url}/api/register",
                    json={
                        "username": f"test_{random.randint(1000, 9999)}",
                        "password": password
                    },
                    timeout=5
                )
                if response.status_code == 200 or response.status_code == 201:
                    test["status"] = "FAIL"
                    test["reason"] = f"Weak password accepted: {password}"
                    break
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        # Test 2: Session management
        test = {
            "name": "Session Security",
            "description": "Test session fixation and hijacking",
            "status": "INFO"
        }
        test["reason"] = "Requires manual testing with valid session"
        
        tests.append(test)
        self.print_test_result(test)
        
        # Test 3: Brute force protection
        test = {
            "name": "Brute Force Protection",
            "description": "Test account lockout mechanism",
            "status": "PASS"
        }
        
        try:
            # Try multiple failed login attempts
            for i in range(10):
                response = requests.post(
                    f"{self.base_url}/api/login",
                    json={"username": "testuser", "password": f"wrong{i}"},
                    timeout=5
                )
            
            # Check if account is locked or rate limited
            if response.status_code not in [429, 423]:  # 429 = Too Many Requests, 423 = Locked
                test["status"] = "WARNING"
                test["reason"] = "No account lockout after multiple failed attempts"
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        self.results["tests"].extend(tests)
        print()
    
    def test_integrity_failures(self):
        """Test for software and data integrity failures"""
        print("A08:2021 - Software and Data Integrity Failures")
        print("-" * 48)
        
        tests = []
        
        test = {
            "name": "Integrity Verification",
            "description": "Check for data integrity controls",
            "status": "INFO"
        }
        test["reason"] = "Requires analysis of CI/CD pipeline and update mechanisms"
        
        tests.append(test)
        self.print_test_result(test)
        
        self.results["tests"].extend(tests)
        print()
    
    def test_logging_monitoring(self):
        """Test for security logging and monitoring failures"""
        print("A09:2021 - Security Logging and Monitoring Failures")
        print("-" * 52)
        
        tests = []
        
        test = {
            "name": "Security Event Logging",
            "description": "Verify security events are logged",
            "status": "INFO"
        }
        test["reason"] = "Requires access to log files to verify"
        
        tests.append(test)
        self.print_test_result(test)
        
        self.results["tests"].extend(tests)
        print()
    
    def test_ssrf(self):
        """Test for Server-Side Request Forgery"""
        print("A10:2021 - Server-Side Request Forgery (SSRF)")
        print("-" * 47)
        
        tests = []
        
        test = {
            "name": "SSRF Protection",
            "description": "Test for SSRF vulnerabilities",
            "status": "PASS"
        }
        
        ssrf_payloads = [
            "http://localhost:22",
            "http://127.0.0.1:6379",
            "file:///etc/passwd",
            "http://169.254.169.254/"  # AWS metadata endpoint
        ]
        
        try:
            for payload in ssrf_payloads:
                response = requests.post(
                    f"{self.base_url}/api/fetch",
                    json={"url": payload},
                    timeout=5
                )
                if response.status_code == 200:
                    test["status"] = "FAIL"
                    test["reason"] = f"SSRF vulnerability - accessed: {payload}"
                    break
        except:
            test["status"] = "SKIP"
        
        tests.append(test)
        self.print_test_result(test)
        
        self.results["tests"].extend(tests)
        print()
    
    def print_test_result(self, test: Dict[str, Any]):
        """Print individual test result"""
        status_symbols = {
            "PASS": "✅",
            "FAIL": "❌",
            "WARNING": "⚠️",
            "INFO": "ℹ️",
            "SKIP": "⏭️"
        }
        
        symbol = status_symbols.get(test["status"], "❓")
        print(f"  {symbol} {test['name']}: {test['status']}")
        
        if "reason" in test:
            print(f"     → {test['reason']}")
        
        if test["status"] == "PASS":
            self.results["passed"] += 1
        elif test["status"] == "FAIL":
            self.results["failed"] += 1
    
    def generate_report(self):
        """Generate final report"""
        print("=" * 50)
        print("OWASP SECURITY TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.results["tests"])
        print(f"\nTotal Tests: {total_tests}")
        print(f"✅ Passed: {self.results['passed']}")
        print(f"❌ Failed: {self.results['failed']}")
        print(f"⏭️ Skipped: {total_tests - self.results['passed'] - self.results['failed']}")
        
        # Calculate score
        if total_tests > 0:
            pass_rate = (self.results["passed"] / total_tests) * 100
            print(f"\nPass Rate: {pass_rate:.1f}%")
            
            if pass_rate >= 90:
                grade = "A"
            elif pass_rate >= 80:
                grade = "B"
            elif pass_rate >= 70:
                grade = "C"
            elif pass_rate >= 60:
                grade = "D"
            else:
                grade = "F"
            
            print(f"Security Grade: {grade}")
        
        # Save report
        report_file = f"owasp-test-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        # Print failed tests
        if self.results["failed"] > 0:
            print("\n❌ Failed Tests:")
            print("-" * 30)
            for test in self.results["tests"]:
                if test.get("status") == "FAIL":
                    print(f"• {test['name']}: {test.get('reason', 'No details')}")
        
        print("\n💡 Recommendations:")
        print("-" * 30)
        print("1. Review and fix all failed tests")
        print("2. Implement rate limiting on all sensitive endpoints")
        print("3. Add security headers to all responses")
        print("4. Regularly update dependencies")
        print("5. Implement comprehensive logging and monitoring")

def main():
    tester = OWASPSecurityTester()
    tester.run_tests()

if __name__ == "__main__":
    main()