#!/usr/bin/env python3
"""
🔧 Convergio - Environment Configuration Backup System
Automated backup and validation for .env files to prevent data loss
"""

import os
import shutil
import hashlib
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import structlog

logger = structlog.get_logger()

class EnvBackupManager:
    """Manages automated backup of .env files with versioning"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.backup_dir = self.project_root / ".env_backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.config_file = self.backup_dir / "backup_config.json"
        self.load_config()
    
    def load_config(self):
        """Load backup configuration"""
        default_config = {
            "max_backups": 30,
            "auto_backup_enabled": True,
            "backup_on_change": True,
            "last_backup": None,
            "file_hashes": {}
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = {**default_config, **json.load(f)}
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
                self.config = default_config
        else:
            self.config = default_config
        
        self.save_config()
    
    def save_config(self):
        """Save backup configuration"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def find_env_files(self) -> List[Path]:
        """Find all .env files in the project"""
        env_files = []
        
        # Common .env file locations
        search_patterns = [
            ".env",
            ".env.local", 
            ".env.example",
            "backend/.env",
            "backend/.env.example",
            "frontend/.env",
            "frontend/.env.example"
        ]
        
        for pattern in search_patterns:
            file_path = self.project_root / pattern
            if file_path.exists():
                env_files.append(file_path)
        
        return env_files
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.error(f"Failed to hash {file_path}: {e}")
            return ""
    
    def has_file_changed(self, file_path: Path) -> bool:
        """Check if file has changed since last backup"""
        current_hash = self.calculate_file_hash(file_path)
        stored_hash = self.config["file_hashes"].get(str(file_path), "")
        return current_hash != stored_hash
    
    def create_backup(self, file_path: Path) -> Optional[Path]:
        """Create timestamped backup of a .env file"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            relative_path = file_path.relative_to(self.project_root)
            backup_name = f"{relative_path.as_posix().replace('/', '_')}_{timestamp}.backup"
            backup_path = self.backup_dir / backup_name
            
            # Create backup
            shutil.copy2(file_path, backup_path)
            
            # Update hash
            current_hash = self.calculate_file_hash(file_path)
            self.config["file_hashes"][str(file_path)] = current_hash
            
            logger.info(f"✅ Backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Failed to backup {file_path}: {e}")
            return None
    
    def backup_all_env_files(self, force: bool = False) -> Dict[str, str]:
        """Backup all .env files if changed or forced"""
        results = {}
        env_files = self.find_env_files()
        
        logger.info(f"🔍 Found {len(env_files)} .env files to check")
        
        for file_path in env_files:
            if force or self.has_file_changed(file_path):
                backup_path = self.create_backup(file_path)
                results[str(file_path)] = str(backup_path) if backup_path else "Failed"
            else:
                results[str(file_path)] = "No changes"
        
        self.config["last_backup"] = datetime.datetime.now().isoformat()
        self.save_config()
        self.cleanup_old_backups()
        
        return results
    
    def cleanup_old_backups(self):
        """Remove old backup files beyond max_backups limit"""
        try:
            backup_files = list(self.backup_dir.glob("*.backup"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            files_to_remove = backup_files[self.config["max_backups"]:]
            for file_path in files_to_remove:
                file_path.unlink()
                logger.info(f"🗑️ Removed old backup: {file_path.name}")
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old backups: {e}")
    
    def list_backups(self) -> List[Dict[str, str]]:
        """List all available backups with metadata"""
        backups = []
        
        try:
            for backup_file in sorted(self.backup_dir.glob("*.backup")):
                stat = backup_file.stat()
                backups.append({
                    "file": backup_file.name,
                    "path": str(backup_file),
                    "size": stat.st_size,
                    "created": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "original_file": backup_file.name.split("_")[0].replace("_", "/")
                })
        except Exception as e:
            logger.error(f"❌ Failed to list backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_file: str, target_path: Optional[Path] = None) -> bool:
        """Restore a backup file"""
        try:
            backup_path = self.backup_dir / backup_file
            if not backup_path.exists():
                logger.error(f"❌ Backup file not found: {backup_file}")
                return False
            
            if not target_path:
                # Auto-detect target path from backup filename
                original_name = backup_file.split("_")[0].replace("_", "/")
                target_path = self.project_root / original_name
            
            # Create backup of current file before restore
            if target_path.exists():
                self.create_backup(target_path)
            
            # Restore
            shutil.copy2(backup_path, target_path)
            logger.info(f"✅ Restored {backup_file} to {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to restore {backup_file}: {e}")
            return False
    
    def validate_env_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate .env file format and required keys"""
        issues = []
        
        try:
            if not file_path.exists():
                return False, ["File does not exist"]
            
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Check for basic format issues
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' not in line:
                    issues.append(f"Line {i}: Missing '=' separator")
                    continue
                
                key, value = line.split('=', 1)
                if not key.strip():
                    issues.append(f"Line {i}: Empty variable name")
            
            # Check for critical environment variables
            content = file_path.read_text()
            critical_vars = ['POSTGRES_PASSWORD', 'OPENAI_API_KEY', 'JWT_PRIVATE_KEY_PATH']
            
            for var in critical_vars:
                if var not in content:
                    issues.append(f"Missing critical variable: {var}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            return False, [f"Validation error: {e}"]


def main():
    """Main backup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Convergio .env Backup Manager")
    parser.add_argument("--backup", action="store_true", help="Create backups")
    parser.add_argument("--list", action="store_true", help="List all backups") 
    parser.add_argument("--restore", type=str, help="Restore specific backup file")
    parser.add_argument("--validate", action="store_true", help="Validate all .env files")
    parser.add_argument("--force", action="store_true", help="Force backup even if unchanged")
    
    args = parser.parse_args()
    
    manager = EnvBackupManager()
    
    if args.backup:
        results = manager.backup_all_env_files(force=args.force)
        print("📋 Backup Results:")
        for file, status in results.items():
            print(f"  {file}: {status}")
    
    elif args.list:
        backups = manager.list_backups()
        print("📋 Available Backups:")
        for backup in backups[-10:]:  # Show last 10
            print(f"  {backup['file']} ({backup['created']})")
    
    elif args.restore:
        success = manager.restore_backup(args.restore)
        print(f"✅ Restore {'successful' if success else 'failed'}")
    
    elif args.validate:
        env_files = manager.find_env_files()
        print("🔍 Validation Results:")
        for file_path in env_files:
            valid, issues = manager.validate_env_file(file_path)
            status = "✅ Valid" if valid else f"❌ Issues: {', '.join(issues)}"
            print(f"  {file_path}: {status}")
    
    else:
        # Auto backup if enabled
        if manager.config["auto_backup_enabled"]:
            results = manager.backup_all_env_files()
            changed_files = [f for f, s in results.items() if s != "No changes"]
            if changed_files:
                print(f"🔄 Auto-backup: {len(changed_files)} files backed up")


if __name__ == "__main__":
    main()