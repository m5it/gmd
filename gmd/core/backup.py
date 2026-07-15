"""
Backup manager with timestamped directories and retention policy.
"""

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from gmd.config.schema import BackupConfig


@dataclass
class BackupEntry:
    """Represents a backup."""
    timestamp: datetime
    source_path: Path
    backup_path: Path
    size_bytes: int
    file_count: int
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "source_path": str(self.source_path),
            "backup_path": str(self.backup_path),
            "size_bytes": self.size_bytes,
            "file_count": self.file_count
        }


@dataclass
class BackupReport:
    """Report of backup operations."""
    entries: List[BackupEntry] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def total_size(self) -> int:
        return sum(e.size_bytes for e in self.entries)
    
    def get_stats(self) -> dict:
        return {
            "backups_created": len(self.entries),
            "total_size_bytes": self.total_size,
            "errors": len(self.errors)
        }


class BackupManager:
    """Manage backups with retention policy."""
    
    BACKUP_PREFIX = "backup_"
    MANIFEST_FILE = "manifest.json"
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.backup_dir = config.directory.expanduser().resolve()
        self._ensure_backup_dir()
    
    def _ensure_backup_dir(self) -> None:
        """Ensure backup directory exists."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_backup_path(self, source_name: str) -> Path:
        """Generate unique backup path with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.BACKUP_PREFIX}{source_name}_{timestamp}"
        return self.backup_dir / backup_name
    
    def _get_backup_size(self, path: Path) -> Tuple[int, int]:
        """
        Calculate total size and file count of a path.
        
        Returns (size_bytes, file_count).
        """
        if path.is_file():
            return path.stat().st_size, 1
        
        total_size = 0
        file_count = 0
        
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                    file_count += 1
                except (OSError, PermissionError):
                    pass
        
        return total_size, file_count
    
    def create_backup(
        self,
        source_path: Path,
        specific_files: Optional[List[Path]] = None
    ) -> Optional[BackupEntry]:
        """
        Create a backup of source path.
        
        Args:
            source_path: Path to backup
            specific_files: If provided, only backup these files
        
        Returns:
            BackupEntry or None if failed
        """
        if not self.config.enabled:
            return None
        
        if not source_path.exists():
            return None
        
        source_name = source_path.name or "root"
        backup_path = self._generate_backup_path(source_name)
        
        try:
            if specific_files:
                # Backup specific files
                backup_path.mkdir(parents=True, exist_ok=True)
                file_count = 0
                total_size = 0
                
                for file_path in specific_files:
                    if file_path.exists():
                        rel_path = file_path.relative_to(source_path) if source_path in file_path.parents else file_path.name
                        dest_path = backup_path / rel_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        if file_path.is_file():
                            shutil.copy2(file_path, dest_path)
                            file_count += 1
                            total_size += file_path.stat().st_size
            else:
                # Backup entire directory
                if source_path.is_file():
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, backup_path)
                    total_size, file_count = source_path.stat().st_size, 1
                else:
                    shutil.copytree(source_path, backup_path)
                    total_size, file_count = self._get_backup_size(backup_path)
            
            entry = BackupEntry(
                timestamp=datetime.now(),
                source_path=source_path,
                backup_path=backup_path,
                size_bytes=total_size,
                file_count=file_count
            )
            
            self._update_manifest(entry)
            self._enforce_retention()
            
            return entry
            
        except (OSError, PermissionError, shutil.Error) as e:
            # Clean up partial backup
            if backup_path.exists():
                if backup_path.is_file():
                    backup_path.unlink(missing_ok=True)
                else:
                    shutil.rmtree(backup_path, ignore_errors=True)
            return None
    
    def _update_manifest(self, entry: BackupEntry) -> None:
        """Update manifest with new backup entry."""
        manifest_path = self.backup_dir / self.MANIFEST_FILE
        
        manifest = []
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        
        manifest.append(entry.to_dict())
        
        # Sort by timestamp descending
        manifest.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Keep only last 100 entries
        manifest = manifest[:100]
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def _enforce_retention(self) -> None:
        """Remove old backups exceeding retention limit."""
        if self.config.keep <= 0:
            return
        
        # Get all backup directories
        backups = []
        for item in self.backup_dir.iterdir():
            if item.is_dir() and item.name.startswith(self.BACKUP_PREFIX):
                try:
                    mtime = item.stat().st_mtime
                    backups.append((mtime, item))
                except OSError:
                    pass
        
        # Sort by modification time (oldest first)
        backups.sort(key=lambda x: x[0])
        
        # Remove oldest if exceeding keep limit
        while len(backups) >= self.config.keep:
            _, old_backup = backups.pop(0)
            try:
                shutil.rmtree(old_backup, ignore_errors=True)
            except Exception:
                pass
    
    def list_backups(self) -> List[BackupEntry]:
        """List all available backups."""
        manifest_path = self.backup_dir / self.MANIFEST_FILE
        
        if not manifest_path.exists():
            return []
        
        try:
            with open(manifest_path, 'r') as f:
                data = json.load(f)
            
            entries = []
            for item in data:
                try:
                    entry = BackupEntry(
                        timestamp=datetime.fromisoformat(item["timestamp"]),
                        source_path=Path(item["source_path"]),
                        backup_path=Path(item["backup_path"]),
                        size_bytes=item["size_bytes"],
                        file_count=item["file_count"]
                    )
                    entries.append(entry)
                except (KeyError, ValueError):
                    continue
            
            return entries
            
        except (json.JSONDecodeError, OSError):
            return []
    
    def restore_backup(
        self,
        backup_entry: BackupEntry,
        restore_path: Optional[Path] = None
    ) -> bool:
        """
        Restore a backup.
        
        Args:
            backup_entry: BackupEntry to restore
            restore_path: Where to restore (defaults to original source)
        
        Returns:
            True if successful
        """
        if not backup_entry.backup_path.exists():
            return False
        
        target_path = restore_path or backup_entry.source_path
        
        try:
            if backup_entry.backup_path.is_file():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_entry.backup_path, target_path)
            else:
                if target_path.exists():
                    if target_path.is_file():
                        target_path.unlink()
                    else:
                        shutil.rmtree(target_path, ignore_errors=True)
                shutil.copytree(backup_entry.backup_path, target_path)
            
            return True
            
        except (OSError, PermissionError, shutil.Error):
            return False
    
    def cleanup(self) -> int:
        """
        Remove all backups.
        
        Returns:
            Number of backups removed
        """
        count = 0
        for item in self.backup_dir.iterdir():
            if item.is_dir() and item.name.startswith(self.BACKUP_PREFIX):
                try:
                    shutil.rmtree(item, ignore_errors=True)
                    count += 1
                except Exception:
                    pass
        
        # Clear manifest
        manifest_path = self.backup_dir / self.MANIFEST_FILE
        if manifest_path.exists():
            manifest_path.unlink(missing_ok=True)
        
        return count
