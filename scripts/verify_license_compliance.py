#!/usr/bin/env python3
"""
📄 Convergio - License Compliance Verification
Ensures BSL 1.1 license compliance across all files
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
import datetime

class LicenseComplianceChecker:
    """Verifies BSL 1.1 license compliance"""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.license_file = self.project_root / "LICENSE"
        self.bsl_header_required = [
            "Business Source License",
            "Roberdan",
            "Convergio AI Platform"
        ]
        
    def check_license_file_exists(self) -> Tuple[bool, str]:
        """Check if LICENSE file exists and is valid"""
        if not self.license_file.exists():
            return False, "LICENSE file not found"
        
        try:
            content = self.license_file.read_text()
            
            # Check for BSL 1.1 key elements
            required_elements = [
                "Business Source License 1.1",
                "Licensor:",
                "Licensed Work:",
                "Change Date:",
                "Change License:",
                "production use"
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if missing_elements:
                return False, f"LICENSE missing elements: {', '.join(missing_elements)}"
            
            # Verify Change Date is in the future
            change_date_match = re.search(r'Change Date:\s*(\d{4}-\d{2}-\d{2})', content)
            if change_date_match:
                change_date_str = change_date_match.group(1)
                change_date = datetime.datetime.strptime(change_date_str, '%Y-%m-%d').date()
                if change_date <= datetime.date.today():
                    return False, f"Change Date {change_date_str} is in the past - license may have converted to MIT"
            
            return True, "LICENSE file is valid BSL 1.1"
            
        except Exception as e:
            return False, f"Error reading LICENSE: {e}"
    
    def get_source_files(self) -> List[Path]:
        """Get all source code files that should have license headers"""
        extensions = {'.py', '.js', '.ts', '.svelte', '.css', '.scss', '.html'}
        excluded_dirs = {
            'node_modules', '__pycache__', '.git', '.svelte-kit', 'dist', 
            'build', 'coverage', '.pytest_cache', 'htmlcov', '.env_backups'
        }
        
        source_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                if file_path.suffix in extensions and file_path.stat().st_size > 100:  # Skip tiny files
                    source_files.append(file_path)
        
        return source_files
    
    def check_file_license_header(self, file_path: Path) -> Tuple[bool, str]:
        """Check if a file has proper license header"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Look for copyright notice
            has_copyright = any(pattern in content.lower() for pattern in [
                'copyright', '(c)', '©', 'roberdan', 'roberto d\'angelo'
            ])
            
            # Look for license reference
            has_license_ref = any(pattern in content.lower() for pattern in [
                'business source license', 'bsl', 'licensed under'
            ])
            
            if has_copyright or has_license_ref:
                return True, "Has license/copyright reference"
            
            # For key files, require explicit license header
            key_files = ['main.py', 'app.py', 'index.js', 'app.js', 'app.svelte']
            if file_path.name in key_files:
                return False, "Key file missing license header"
            
            # For other files, it's a warning not an error
            return True, "No license header (acceptable for supporting files)"
            
        except Exception as e:
            return False, f"Error reading file: {e}"
    
    def check_readme_license_info(self) -> Tuple[bool, str]:
        """Check if README properly mentions the license"""
        readme_files = ['README.md', 'README.rst', 'README.txt']
        
        for readme_name in readme_files:
            readme_path = self.project_root / readme_name
            if readme_path.exists():
                try:
                    content = readme_path.read_text()
                    
                    # Should mention BSL or license
                    license_mentioned = any(pattern in content.lower() for pattern in [
                        'business source license', 'license', 'licensed under'
                    ])
                    
                    if license_mentioned:
                        return True, f"License properly mentioned in {readme_name}"
                    else:
                        return False, f"License not mentioned in {readme_name}"
                        
                except Exception as e:
                    return False, f"Error reading {readme_name}: {e}"
        
        return False, "No README file found"
    
    def check_package_json_license(self) -> Tuple[bool, str]:
        """Check package.json license field"""
        package_json_paths = [
            self.project_root / "package.json",
            self.project_root / "frontend" / "package.json"
        ]
        
        results = []
        
        for package_path in package_json_paths:
            if package_path.exists():
                try:
                    import json
                    with open(package_path) as f:
                        package_data = json.load(f)
                    
                    license_field = package_data.get('license', '')
                    
                    if 'BUSL' in license_field or 'Business Source' in license_field:
                        results.append(f"✅ {package_path.name}: {license_field}")
                    elif license_field:
                        results.append(f"⚠️ {package_path.name}: {license_field} (should be BUSL-1.1)")
                    else:
                        results.append(f"❌ {package_path.name}: No license field")
                        
                except Exception as e:
                    results.append(f"❌ {package_path.name}: Error reading - {e}")
        
        if not results:
            return True, "No package.json files found"
        
        has_issues = any('❌' in result for result in results)
        return not has_issues, '; '.join(results)
    
    def generate_compliance_report(self) -> Dict[str, any]:
        """Generate comprehensive compliance report"""
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'overall_compliant': True,
            'checks': {},
            'issues': [],
            'warnings': []
        }
        
        # Check LICENSE file
        license_valid, license_msg = self.check_license_file_exists()
        report['checks']['license_file'] = {'status': license_valid, 'message': license_msg}
        if not license_valid:
            report['overall_compliant'] = False
            report['issues'].append(f"LICENSE: {license_msg}")
        
        # Check README
        readme_valid, readme_msg = self.check_readme_license_info()
        report['checks']['readme_license'] = {'status': readme_valid, 'message': readme_msg}
        if not readme_valid:
            report['warnings'].append(f"README: {readme_msg}")
        
        # Check package.json
        package_valid, package_msg = self.check_package_json_license()
        report['checks']['package_json'] = {'status': package_valid, 'message': package_msg}
        if not package_valid:
            report['warnings'].append(f"package.json: {package_msg}")
        
        # Check source files (sample)
        source_files = self.get_source_files()
        total_files = len(source_files)
        files_with_headers = 0
        files_checked = min(20, total_files)  # Check first 20 files
        
        for file_path in source_files[:files_checked]:
            has_header, msg = self.check_file_license_header(file_path)
            if has_header:
                files_with_headers += 1
        
        header_percentage = (files_with_headers / files_checked * 100) if files_checked > 0 else 0
        report['checks']['source_file_headers'] = {
            'status': header_percentage > 50,  # At least 50% should have some reference
            'message': f"{files_with_headers}/{files_checked} files have license references ({header_percentage:.1f}%)",
            'total_source_files': total_files
        }
        
        if header_percentage < 30:
            report['warnings'].append(f"Low license header coverage: {header_percentage:.1f}%")
        
        return report
    
    def print_compliance_report(self, report: Dict = None):
        """Print human-readable compliance report"""
        if report is None:
            report = self.generate_compliance_report()
        
        print("\n" + "="*60)
        print("📄 BSL 1.1 LICENSE COMPLIANCE REPORT")
        print("="*60)
        
        if report['overall_compliant']:
            print("✅ STATUS: COMPLIANT")
        else:
            print("❌ STATUS: COMPLIANCE ISSUES FOUND")
        
        print(f"\n📊 COMPLIANCE CHECKS:")
        for check_name, check_data in report['checks'].items():
            status_emoji = "✅" if check_data['status'] else "❌"
            check_title = check_name.replace('_', ' ').title()
            print(f"  {status_emoji} {check_title}: {check_data['message']}")
        
        if report['issues']:
            print(f"\n🚨 CRITICAL ISSUES ({len(report['issues'])}):")
            for issue in report['issues']:
                print(f"  • {issue}")
        
        if report['warnings']:
            print(f"\n⚠️  WARNINGS ({len(report['warnings'])}):")
            for warning in report['warnings']:
                print(f"  • {warning}")
        
        print(f"\n📅 Generated: {report['timestamp']}")
        print("="*60 + "\n")
        
        return report['overall_compliant']


def main():
    """Main compliance check"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BSL 1.1 License Compliance Checker")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--strict", action="store_true", help="Strict mode - warnings become errors")
    
    args = parser.parse_args()
    
    checker = LicenseComplianceChecker()
    report = checker.generate_compliance_report()
    
    if args.strict and report['warnings']:
        report['overall_compliant'] = False
        report['issues'].extend(report['warnings'])
        report['warnings'] = []
    
    if args.json:
        import json
        print(json.dumps(report, indent=2))
    else:
        compliant = checker.print_compliance_report(report)
        exit(0 if compliant else 1)


if __name__ == "__main__":
    main()