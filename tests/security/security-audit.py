#!/usr/bin/env python3
"""
Convergio Security Audit Script
Comprehensive security testing for the application
"""

import os
import re
import json
import subprocess
import requests
from typing import Dict, List, Any
from datetime import datetime
import hashlib
import base64
from pathlib import Path

class SecurityAuditor:
    def __init__(self):
        self.vulnerabilities = []
        self.base_url = "http://localhost:9000"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "vulnerabilities": [],
            "passed_checks": [],
            "warnings": []
        }
    
    def run_audit(self):
        """Run complete security audit"""
        print("====================================")
        print("CONVERGIO SECURITY AUDIT")
        print("====================================\n")
        
        # Run all security checks
        self.check_dependencies()
        self.check_sql_injection()
        self.check_xss_protection()
        self.check_cors_configuration()
        self.check_authentication()
        self.check_authorization()
        self.check_input_validation()
        self.check_secure_headers()
        self.check_sensitive_data()
        self.check_rate_limiting()
        self.check_file_permissions()
        self.check_encryption()
        
        # Generate report
        self.generate_report()
        
    def check_dependencies(self):
        """Check for vulnerable dependencies"""
        print("1. Checking Dependencies for Vulnerabilities")
        print("=" * 45)
        
        # Check Python dependencies
        try:
            result = subprocess.run(
                ["pip", "list", "--format=json"],
                capture_output=True,
                text=True
            )
            packages = json.loads(result.stdout)
            print(f"  ✓ Found {len(packages)} Python packages")
            
            # Check for known vulnerable versions
            vulnerable_packages = {
                "requests": ["2.5.0", "2.5.1", "2.5.2"],  # Example vulnerable versions
                "flask": ["0.12.2", "0.12.3"],
                "django": ["1.11.0", "1.11.1", "1.11.2"]
            }
            
            for package in packages:
                pkg_name = package.get("name", "").lower()
                pkg_version = package.get("version", "")
                
                if pkg_name in vulnerable_packages:
                    if pkg_version in vulnerable_packages[pkg_name]:
                        self.add_vulnerability(
                            "HIGH",
                            f"Vulnerable package: {pkg_name}=={pkg_version}",
                            f"Update {pkg_name} to latest secure version"
                        )
            
            self.results["passed_checks"].append("Dependency scanning completed")
            
        except Exception as e:
            self.add_warning(f"Could not check Python dependencies: {e}")
        
        print()
    
    def check_sql_injection(self):
        """Check for SQL injection vulnerabilities"""
        print("2. Checking SQL Injection Protection")
        print("=" * 37)
        
        # Check source code for SQL injection patterns
        dangerous_patterns = [
            r'f"SELECT.*{.*}"',  # F-string in SQL
            r'"SELECT.*\+.*"',   # String concatenation in SQL
            r'%\s*s.*SELECT',    # Improper parameterization
            r'execute\([^,]*\+',  # Dynamic SQL execution
        ]
        
        code_files = []
        for root, dirs, files in os.walk("backend/src"):
            for file in files:
                if file.endswith(".py"):
                    code_files.append(os.path.join(root, file))
        
        vulnerabilities_found = False
        for file_path in code_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                for pattern in dangerous_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        self.add_vulnerability(
                            "CRITICAL",
                            f"Potential SQL injection in {file_path}",
                            "Use parameterized queries or ORM methods"
                        )
                        vulnerabilities_found = True
            except:
                pass
        
        if not vulnerabilities_found:
            print("  ✓ No SQL injection patterns detected")
            self.results["passed_checks"].append("SQL injection protection verified")
        
        print()
    
    def check_xss_protection(self):
        """Check for XSS protection"""
        print("3. Checking XSS Protection")
        print("=" * 27)
        
        # Check for Content Security Policy
        headers_to_check = {
            "Content-Security-Policy": "default-src 'self'",
            "X-XSS-Protection": "1; mode=block",
            "X-Content-Type-Options": "nosniff"
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            
            for header, expected in headers_to_check.items():
                if header in response.headers:
                    print(f"  ✓ {header} is set")
                    self.results["passed_checks"].append(f"{header} header present")
                else:
                    self.add_vulnerability(
                        "MEDIUM",
                        f"Missing security header: {header}",
                        f"Add {header}: {expected} to responses"
                    )
        except:
            self.add_warning("Could not connect to API to check XSS headers")
        
        # Check for unsafe HTML rendering in frontend
        frontend_files = []
        for root, dirs, files in os.walk("frontend/src"):
            for file in files:
                if file.endswith((".svelte", ".tsx", ".jsx")):
                    frontend_files.append(os.path.join(root, file))
        
        unsafe_patterns = [
            r'dangerouslySetInnerHTML',
            r'v-html=',
            r'{@html',
            r'innerHTML\s*='
        ]
        
        for file_path in frontend_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                for pattern in unsafe_patterns:
                    if re.search(pattern, content):
                        self.add_vulnerability(
                            "HIGH",
                            f"Unsafe HTML rendering in {file_path}",
                            "Sanitize user input before rendering HTML"
                        )
            except:
                pass
        
        print()
    
    def check_cors_configuration(self):
        """Check CORS configuration"""
        print("4. Checking CORS Configuration")
        print("=" * 31)
        
        # Check backend CORS settings
        config_file = "backend/src/main.py"
        try:
            with open(config_file, 'r') as f:
                content = f.read()
                
            if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
                self.add_vulnerability(
                    "HIGH",
                    "CORS allows all origins (*)",
                    "Restrict CORS to specific trusted origins"
                )
            else:
                print("  ✓ CORS configuration appears restricted")
                self.results["passed_checks"].append("CORS properly configured")
                
        except:
            self.add_warning("Could not check CORS configuration")
        
        print()
    
    def check_authentication(self):
        """Check authentication security"""
        print("5. Checking Authentication Security")
        print("=" * 36)
        
        # Check for JWT secret key security
        env_files = [".env", ".env.production", ".env.development"]
        
        for env_file in env_files:
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    content = f.read()
                    
                # Check for weak JWT secrets
                if re.search(r'JWT_SECRET=["\']*secret["\']*', content, re.IGNORECASE):
                    self.add_vulnerability(
                        "CRITICAL",
                        f"Weak JWT secret in {env_file}",
                        "Use a strong, randomly generated JWT secret"
                    )
                
                # Check for default passwords
                if re.search(r'PASSWORD=["\']*admin["\']*', content, re.IGNORECASE):
                    self.add_vulnerability(
                        "CRITICAL",
                        f"Default password found in {env_file}",
                        "Remove default passwords from configuration"
                    )
        
        # Check password hashing
        auth_files = ["backend/src/api/auth.py", "backend/src/core/auth.py"]
        for auth_file in auth_files:
            if os.path.exists(auth_file):
                with open(auth_file, 'r') as f:
                    content = f.read()
                    
                if "bcrypt" in content or "argon2" in content:
                    print("  ✓ Secure password hashing detected")
                    self.results["passed_checks"].append("Password hashing secure")
                elif "md5" in content or "sha1" in content:
                    self.add_vulnerability(
                        "CRITICAL",
                        f"Weak password hashing in {auth_file}",
                        "Use bcrypt or argon2 for password hashing"
                    )
        
        print()
    
    def check_authorization(self):
        """Check authorization implementation"""
        print("6. Checking Authorization")
        print("=" * 26)
        
        # Check for proper role-based access control
        api_files = []
        for root, dirs, files in os.walk("backend/src/api"):
            for file in files:
                if file.endswith(".py"):
                    api_files.append(os.path.join(root, file))
        
        protected_endpoints = 0
        unprotected_endpoints = []
        
        for file_path in api_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Check for authorization decorators/dependencies
                if "@require_auth" in content or "Depends(get_current_user)" in content:
                    protected_endpoints += 1
                else:
                    # Check if file has endpoints
                    if "@router." in content or "@app." in content:
                        unprotected_endpoints.append(file_path)
            except:
                pass
        
        if protected_endpoints > 0:
            print(f"  ✓ Found {protected_endpoints} protected endpoints")
            self.results["passed_checks"].append("Authorization checks present")
        
        if unprotected_endpoints:
            for endpoint in unprotected_endpoints:
                self.add_warning(f"Potentially unprotected endpoints in {endpoint}")
        
        print()
    
    def check_input_validation(self):
        """Check input validation"""
        print("7. Checking Input Validation")
        print("=" * 29)
        
        # Check for Pydantic models (Python)
        model_files = []
        for root, dirs, files in os.walk("backend/src"):
            for file in files:
                if file.endswith(".py"):
                    model_files.append(os.path.join(root, file))
        
        validation_found = False
        for file_path in model_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                if "from pydantic import" in content or "BaseModel" in content:
                    validation_found = True
                    break
            except:
                pass
        
        if validation_found:
            print("  ✓ Pydantic validation models detected")
            self.results["passed_checks"].append("Input validation framework present")
        else:
            self.add_warning("No structured input validation detected")
        
        # Check for file upload validation
        upload_patterns = [
            r'upload.*file',
            r'multipart/form-data',
            r'FileUpload'
        ]
        
        for file_path in model_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                for pattern in upload_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        if not re.search(r'(allowed_extensions|max_size|file_type)', content):
                            self.add_vulnerability(
                                "MEDIUM",
                                f"File upload without validation in {file_path}",
                                "Add file type and size validation"
                            )
            except:
                pass
        
        print()
    
    def check_secure_headers(self):
        """Check security headers"""
        print("8. Checking Security Headers")
        print("=" * 29)
        
        required_headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=5)
            
            for header, expected in required_headers.items():
                if header in response.headers:
                    print(f"  ✓ {header}: {response.headers[header]}")
                    self.results["passed_checks"].append(f"{header} configured")
                else:
                    self.add_vulnerability(
                        "MEDIUM",
                        f"Missing security header: {header}",
                        f"Add {header}: {expected}"
                    )
        except:
            self.add_warning("Could not check security headers (API not available)")
        
        print()
    
    def check_sensitive_data(self):
        """Check for exposed sensitive data"""
        print("9. Checking for Exposed Sensitive Data")
        print("=" * 39)
        
        # Check for sensitive data in code
        sensitive_patterns = [
            (r'api[_-]?key\s*=\s*["\'][^"\']+["\']', "API key"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Password"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Token"),
            (r'private[_-]?key\s*=\s*["\'][^"\']+["\']', "Private key")
        ]
        
        exclude_dirs = {"node_modules", "venv", ".git", "__pycache__"}
        
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                    file_path = os.path.join(root, file)
                    
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            
                        for pattern, data_type in sensitive_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                # Check if it's not a placeholder
                                if not re.search(r'(process\.env|os\.environ|getenv)', content):
                                    self.add_vulnerability(
                                        "HIGH",
                                        f"Hardcoded {data_type} in {file_path}",
                                        f"Move {data_type} to environment variables"
                                    )
                    except:
                        pass
        
        # Check for .env in git
        if os.path.exists(".git"):
            result = subprocess.run(
                ["git", "ls-files", ".env"],
                capture_output=True,
                text=True
            )
            if result.stdout:
                self.add_vulnerability(
                    "CRITICAL",
                    ".env file tracked in git",
                    "Remove .env from git and add to .gitignore"
                )
        
        print("  ✓ Sensitive data scan completed")
        print()
    
    def check_rate_limiting(self):
        """Check rate limiting implementation"""
        print("10. Checking Rate Limiting")
        print("=" * 27)
        
        # Check for rate limiting in backend
        main_file = "backend/src/main.py"
        try:
            with open(main_file, 'r') as f:
                content = f.read()
                
            if "slowapi" in content or "ratelimit" in content.lower():
                print("  ✓ Rate limiting detected")
                self.results["passed_checks"].append("Rate limiting implemented")
            else:
                self.add_vulnerability(
                    "MEDIUM",
                    "No rate limiting detected",
                    "Implement rate limiting to prevent abuse"
                )
        except:
            self.add_warning("Could not check rate limiting")
        
        print()
    
    def check_file_permissions(self):
        """Check file permissions"""
        print("11. Checking File Permissions")
        print("=" * 30)
        
        sensitive_files = [
            ".env",
            "backend/secrets/jwt/key_active.pem",
            "backend/secrets/signatures/agent_signing_key.pem"
        ]
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                stat_info = os.stat(file_path)
                mode = oct(stat_info.st_mode)[-3:]
                
                if mode != "600" and mode != "400":
                    self.add_vulnerability(
                        "HIGH",
                        f"Insecure file permissions on {file_path} ({mode})",
                        f"Set permissions to 600 or 400: chmod 600 {file_path}"
                    )
                else:
                    print(f"  ✓ {file_path}: {mode} (secure)")
                    self.results["passed_checks"].append(f"{file_path} permissions secure")
        
        print()
    
    def check_encryption(self):
        """Check encryption implementation"""
        print("12. Checking Encryption")
        print("=" * 24)
        
        # Check for HTTPS enforcement
        if os.path.exists("frontend/src/hooks.server.ts"):
            with open("frontend/src/hooks.server.ts", 'r') as f:
                content = f.read()
                
            if "https" in content.lower() or "ssl" in content.lower():
                print("  ✓ HTTPS enforcement detected")
                self.results["passed_checks"].append("HTTPS enforcement present")
        
        # Check for encryption at rest
        db_config_files = [
            "backend/src/core/database.py",
            "backend/src/core/config.py"
        ]
        
        encryption_at_rest = False
        for config_file in db_config_files:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                    
                if "sslmode" in content or "encrypt" in content.lower():
                    encryption_at_rest = True
                    break
        
        if encryption_at_rest:
            print("  ✓ Database encryption configuration detected")
            self.results["passed_checks"].append("Database encryption configured")
        else:
            self.add_warning("No database encryption configuration detected")
        
        print()
    
    def add_vulnerability(self, severity: str, description: str, recommendation: str):
        """Add vulnerability to results"""
        vuln = {
            "severity": severity,
            "description": description,
            "recommendation": recommendation
        }
        self.results["vulnerabilities"].append(vuln)
        
        color = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
        print(f"  {color.get(severity, '⚪')} {severity}: {description}")
    
    def add_warning(self, message: str):
        """Add warning to results"""
        self.results["warnings"].append(message)
        print(f"  ⚠️  {message}")
    
    def generate_report(self):
        """Generate security audit report"""
        print("\n" + "=" * 50)
        print("SECURITY AUDIT SUMMARY")
        print("=" * 50)
        
        # Count vulnerabilities by severity
        severity_counts = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }
        
        for vuln in self.results["vulnerabilities"]:
            severity_counts[vuln["severity"]] += 1
        
        print("\nVulnerabilities Found:")
        print(f"  🔴 CRITICAL: {severity_counts['CRITICAL']}")
        print(f"  🟠 HIGH: {severity_counts['HIGH']}")
        print(f"  🟡 MEDIUM: {severity_counts['MEDIUM']}")
        print(f"  🟢 LOW: {severity_counts['LOW']}")
        
        print(f"\n✅ Passed Checks: {len(self.results['passed_checks'])}")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        
        # Overall score
        total_vulns = sum(severity_counts.values())
        if total_vulns == 0:
            score = "A+"
            status = "EXCELLENT"
        elif severity_counts["CRITICAL"] > 0:
            score = "F"
            status = "CRITICAL"
        elif severity_counts["HIGH"] > 0:
            score = "D"
            status = "POOR"
        elif severity_counts["MEDIUM"] > 2:
            score = "C"
            status = "FAIR"
        elif severity_counts["MEDIUM"] > 0:
            score = "B"
            status = "GOOD"
        else:
            score = "A"
            status = "VERY GOOD"
        
        print(f"\nSecurity Score: {score} ({status})")
        
        # Save detailed report (to logs directory at repo root)
        repo_root = Path(__file__).resolve().parents[2]
        logs_dir = Path(os.getenv("LOG_DIR") or (repo_root / "logs"))
        logs_dir.mkdir(parents=True, exist_ok=True)
        report_file = logs_dir / f"security-audit-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        # Print recommendations
        if self.results["vulnerabilities"]:
            print("\nTop Priority Recommendations:")
            print("-" * 30)
            
            # Sort by severity
            sorted_vulns = sorted(
                self.results["vulnerabilities"],
                key=lambda x: ["LOW", "MEDIUM", "HIGH", "CRITICAL"].index(x["severity"]),
                reverse=True
            )
            
            for i, vuln in enumerate(sorted_vulns[:5], 1):
                print(f"{i}. [{vuln['severity']}] {vuln['recommendation']}")

def main():
    auditor = SecurityAuditor()
    auditor.run_audit()

if __name__ == "__main__":
    main()
