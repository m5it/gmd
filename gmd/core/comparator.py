"""
File comparator with SHA256 hashing for detecting differences.
"""

import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from gmd.core.scanner import FileEntry, ScanResult


class FileStatus(Enum):
    """Status of file comparison."""
    MISSING = auto()      # In master but not in slave
    UPDATE = auto()       # Different between master and slave
    EXISTS = auto()       # Identical in both
    EXTRA = auto()        # In slave but not in master (for reverse sync)


@dataclass
class FileComparison:
    """Result of comparing two files."""
    status: FileStatus
    master_entry: Optional[FileEntry]
    slave_entry: Optional[FileEntry]
    master_hash: Optional[str] = None
    slave_hash: Optional[str] = None
    diff_output: Optional[str] = None
    
    @property
    def relative_path(self) -> Path:
        """Get the relative path."""
        if self.master_entry:
            return self.master_entry.relative_path
        elif self.slave_entry:
            return self.slave_entry.relative_path
        return Path(".")
    
    @property
    def source_path(self) -> Optional[Path]:
        """Get source file path."""
        if self.status == FileStatus.EXTRA:
            return self.slave_entry.path if self.slave_entry else None
        return self.master_entry.path if self.master_entry else None
    
    @property
    def dest_path(self) -> Optional[Path]:
        """Get destination file path."""
        if self.status == FileStatus.EXTRA:
            return self.master_entry.path if self.master_entry else None
        return self.slave_entry.path if self.slave_entry else None


@dataclass
class ComparisonResult:
    """Result of directory comparison."""
    missing: List[FileComparison] = field(default_factory=list)
    update: List[FileComparison] = field(default_factory=list)
    exists: List[FileComparison] = field(default_factory=list)
    extra: List[FileComparison] = field(default_factory=list)
    
    @property
    def all_comparisons(self) -> List[FileComparison]:
        """Get all comparisons."""
        return self.missing + self.update + self.exists + self.extra
    
    def get_stats(self) -> dict:
        """Get statistics."""
        return {
            "missing": len(self.missing),
            "update": len(self.update),
            "exists": len(self.exists),
            "extra": len(self.extra),
            "total": len(self.all_comparisons)
        }


class FileComparator:
    """Compare files between directories using SHA256 hashing."""
    
    def __init__(
        self,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        use_quick_compare: bool = True
    ):
        self.progress_callback = progress_callback
        self.use_quick_compare = use_quick_compare  # Compare size/mtime first
        self._hash_cache: dict[Path, str] = {}
    
    def _calculate_hash(self, file_path: Path) -> Optional[str]:
        """Calculate SHA256 hash of file."""
        # Check cache
        if file_path in self._hash_cache:
            return self._hash_cache[file_path]
        
        try:
            sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    sha256.update(chunk)
            hash_value = sha256.hexdigest()
            self._hash_cache[file_path] = hash_value
            return hash_value
        except (OSError, PermissionError):
            return None
    
    def _quick_compare(
        self,
        master: FileEntry,
        slave: FileEntry
    ) -> Optional[bool]:
        """
        Quick comparison using size and mtime.
        Returns True if definitely same, False if definitely different,
        None if need to hash compare.
        """
        if master.size != slave.size:
            return False  # Different sizes = different files
        
        # Same size, check mtime
        # If mtime differs, likely different (but could be same content)
        if master.modified_time != slave.modified_time:
            return None  # Need hash compare
        
        # Same size and mtime, likely same (but hash to be sure)
        return None
    
    def compare_files(
        self,
        master_entry: FileEntry,
        slave_entry: FileEntry
    ) -> FileComparison:
        """
        Compare two files.
        
        Returns FileComparison with status and hashes.
        """
        # Quick compare first
        if self.use_quick_compare:
            quick = self._quick_compare(master_entry, slave_entry)
            if quick is True:
                # Likely same
                return FileComparison(
                    status=FileStatus.EXISTS,
                    master_entry=master_entry,
                    slave_entry=slave_entry
                )
        
        # Calculate hashes
        master_hash = self._calculate_hash(master_entry.path)
        slave_hash = self._calculate_hash(slave_entry.path)
        
        if master_hash is None or slave_hash is None:
            return FileComparison(
                status=FileStatus.UPDATE,  # Assume update if can't read
                master_entry=master_entry,
                slave_entry=slave_entry,
                master_hash=master_hash,
                slave_hash=slave_hash
            )
        
        if master_hash == slave_hash:
            return FileComparison(
                status=FileStatus.EXISTS,
                master_entry=master_entry,
                slave_entry=slave_entry,
                master_hash=master_hash,
                slave_hash=slave_hash
            )
        else:
            return FileComparison(
                status=FileStatus.UPDATE,
                master_entry=master_entry,
                slave_entry=slave_entry,
                master_hash=master_hash,
                slave_hash=slave_hash
            )
    
    def compare_directories(
        self,
        master_scan: ScanResult,
        slave_scan: ScanResult,
        categories: Optional[List[FileStatus]] = None
    ) -> ComparisonResult:
        """
        Compare two scanned directories.
        
        Args:
            master_scan: Scan of master directory
            slave_scan: Scan of slave directory
            categories: Which categories to include (default: all)
        
        Returns:
            ComparisonResult with categorized files
        """
        categories = categories or list(FileStatus)
        result = ComparisonResult()
        
        # Build lookup by relative path
        master_files = {f.relative_path: f for f in master_scan.files}
        slave_files = {f.relative_path: f for f in slave_scan.files}
        
        total = len(master_scan.files) + len(slave_scan.files)
        processed = 0
        
        # Check master files
        for rel_path, master_entry in master_files.items():
            slave_entry = slave_files.get(rel_path)
            
            if slave_entry is None:
                # Missing in slave
                if FileStatus.MISSING in categories:
                    comparison = FileComparison(
                        status=FileStatus.MISSING,
                        master_entry=master_entry,
                        slave_entry=None
                    )
                    result.missing.append(comparison)
            else:
                # Exists in both, compare
                comparison = self.compare_files(master_entry, slave_entry)
                
                if comparison.status == FileStatus.EXISTS and FileStatus.EXISTS in categories:
                    result.exists.append(comparison)
                elif comparison.status == FileStatus.UPDATE and FileStatus.UPDATE in categories:
                    result.update.append(comparison)
            
            processed += 1
            if self.progress_callback and processed % 50 == 0:
                self.progress_callback(processed, total, str(rel_path))
        
        # Check for extra files in slave (not in master)
        if FileStatus.EXTRA in categories:
            for rel_path, slave_entry in slave_files.items():
                if rel_path not in master_files:
                    comparison = FileComparison(
                        status=FileStatus.EXTRA,
                        master_entry=None,
                        slave_entry=slave_entry
                    )
                    result.extra.append(comparison)
                    
                    processed += 1
                    if self.progress_callback and processed % 50 == 0:
                        self.progress_callback(processed, total, str(rel_path))
        
        # Final progress
        if self.progress_callback:
            self.progress_callback(total, total, "complete")
        
        return result
    
    def generate_diff(
        self,
        comparison: FileComparison,
        max_lines: int = 100
    ) -> Optional[str]:
        """
        Generate diff output between two files.
        
        Args:
            comparison: FileComparison with UPDATE status
            max_lines: Maximum number of diff lines to return
        
        Returns:
            Diff output as string or None if can't diff
        """
        if comparison.status != FileStatus.UPDATE:
            return None
        
        if not comparison.master_entry or not comparison.slave_entry:
            return None
        
        try:
            import subprocess
            
            result = subprocess.run(
                ['diff', '-u', 
                 str(comparison.slave_entry.path),
                 str(comparison.master_entry.path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # diff returns 1 when files differ (expected)
            if result.returncode in (0, 1):
                lines = result.stdout.split('\n')[:max_lines]
                return '\n'.join(lines)
            
            return result.stderr if result.stderr else None
            
        except (subprocess.SubprocessError, FileNotFoundError):
            # Fallback: simple line-by-line comparison
            try:
                with open(comparison.master_entry.path, 'r') as f1, \
                     open(comparison.slave_entry.path, 'r') as f2:
                    lines1 = f1.readlines()
                    lines2 = f2.readlines()
                
                diff_lines = []
                max_len = max(len(lines1), len(lines2))
                
                for i in range(min(max_len, max_lines)):
                    line1 = lines1[i] if i < len(lines1) else None
                    line2 = lines2[i] if i < len(lines2) else None
                    
                    if line1 != line2:
                        if line2:
                            diff_lines.append(f"- {line2.rstrip()}")
                        if line1:
                            diff_lines.append(f"+ {line1.rstrip()}")
                
                return '\n'.join(diff_lines)
                
            except (OSError, PermissionError):
                return None
    
    def clear_cache(self) -> None:
        """Clear hash cache."""
        self._hash_cache.clear()
