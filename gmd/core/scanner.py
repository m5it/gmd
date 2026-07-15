"""
Directory scanner with exclude pattern support.
"""

import fnmatch
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator, List, Optional, Set, Tuple


@dataclass
class FileEntry:
    """Represents a file found during scanning."""
    path: Path
    relative_path: Path
    size: int
    modified_time: float
    
    def __hash__(self) -> int:
        return hash(self.path)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FileEntry):
            return NotImplemented
        return self.path == other.path


@dataclass
class ScanResult:
    """Result of directory scanning."""
    files: List[FileEntry] = field(default_factory=list)
    directories: List[Path] = field(default_factory=list)
    scanned_count: int = 0
    excluded_count: int = 0
    
    def get_by_relative_path(self, rel_path: Path) -> Optional[FileEntry]:
        """Find file by relative path."""
        for entry in self.files:
            if entry.relative_path == rel_path:
                return entry
        return None


class DirectoryScanner:
    """Recursive directory scanner with exclude support."""
    
    def __init__(
        self,
        excludes: Optional[List[str]] = None,
        follow_symlinks: bool = False,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ):
        self.excludes = excludes or []
        self.follow_symlinks = follow_symlinks
        self.progress_callback = progress_callback
        self._compiled_patterns: List[re.Pattern] = []
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Compile exclude patterns for efficient matching."""
        for pattern in self.excludes:
            # Convert glob to regex if it contains wildcards
            if '*' in pattern or '?' in pattern:
                regex = fnmatch.translate(pattern)
                self._compiled_patterns.append(re.compile(regex))
            else:
                # Exact match or contains pattern
                escaped = re.escape(pattern)
                self._compiled_patterns.append(re.compile(f".*{escaped}.*"))
    
    def _is_excluded(self, path: Path, relative_to: Path) -> bool:
        """Check if path matches any exclude pattern."""
        # Check absolute path
        path_str = str(path)
        rel_path_str = str(relative_to)
        
        for pattern in self.excludes:
            # Direct match in path components
            if pattern in path_str:
                return True
            # Match against relative path
            if pattern in rel_path_str:
                return True
        
        # Check compiled regex patterns
        for compiled in self._compiled_patterns:
            if compiled.search(path_str) or compiled.search(rel_path_str):
                return True
        
        return False
    
    def scan(
        self,
        directory: Path,
        base_path: Optional[Path] = None
    ) -> ScanResult:
        """
        Recursively scan directory.
        
        Args:
            directory: Directory to scan
            base_path: Base path for calculating relative paths (defaults to directory)
        
        Returns:
            ScanResult with found files and directories
        """
        directory = Path(directory).resolve()
        base_path = base_path or directory
        
        result = ScanResult()
        scanned = 0
        
        for root, dirs, files in os.walk(directory, followlinks=self.follow_symlinks):
            root_path = Path(root)
            rel_root = root_path.relative_to(base_path)
            
            # Filter excluded directories (modify dirs in-place to prevent traversal)
            dirs[:] = [
                d for d in dirs 
                if not self._is_excluded(root_path / d, rel_root / d)
            ]
            
            # Check if current directory is excluded
            if self._is_excluded(root_path, rel_root):
                result.excluded_count += 1
                continue
            
            result.directories.append(root_path)
            
            for filename in files:
                file_path = root_path / filename
                rel_path = file_path.relative_to(base_path)
                
                # Skip symlinks unless following them
                if file_path.is_symlink() and not self.follow_symlinks:
                    continue
                
                # Check excludes
                if self._is_excluded(file_path, rel_path):
                    result.excluded_count += 1
                    continue
                
                # Get file info
                try:
                    stat = file_path.stat()
                    entry = FileEntry(
                        path=file_path,
                        relative_path=rel_path,
                        size=stat.st_size,
                        modified_time=stat.st_mtime
                    )
                    result.files.append(entry)
                except (OSError, PermissionError) as e:
                    # Skip files we can't stat
                    continue
                
                scanned += 1
                if self.progress_callback and scanned % 100 == 0:
                    self.progress_callback(scanned, str(rel_path))
        
        result.scanned_count = scanned
        
        # Final progress callback
        if self.progress_callback:
            self.progress_callback(scanned, "complete")
        
        return result
    
    def scan_pair(
        self,
        master_dir: Path,
        slave_dir: Path
    ) -> Tuple[ScanResult, ScanResult]:
        """
        Scan both master and slave directories.
        
        Args:
            master_dir: Master directory
            slave_dir: Slave directory
        
        Returns:
            Tuple of (master_scan, slave_scan)
        """
        master_scan = self.scan(master_dir)
        
        # Reset for slave scan
        scanned = 0
        
        def slave_progress(count: int, path: str) -> None:
            nonlocal scanned
            scanned = count
            if self.progress_callback:
                self.progress_callback(len(master_scan.files) + count, path)
        
        # Temporarily replace callback
        original_callback = self.progress_callback
        self.progress_callback = slave_progress
        
        slave_scan = self.scan(slave_dir)
        
        # Restore original callback
        self.progress_callback = original_callback
        
        return master_scan, slave_scan
    
    def get_files_iterator(
        self,
        directory: Path,
        base_path: Optional[Path] = None
    ) -> Iterator[FileEntry]:
        """
        Generator that yields files one by one.
        Useful for very large directories.
        """
        directory = Path(directory).resolve()
        base_path = base_path or directory
        
        for root, dirs, files in os.walk(directory, followlinks=self.follow_symlinks):
            root_path = Path(root)
            rel_root = root_path.relative_to(base_path)
            
            # Filter excluded directories
            dirs[:] = [
                d for d in dirs 
                if not self._is_excluded(root_path / d, rel_root / d)
            ]
            
            if self._is_excluded(root_path, rel_root):
                continue
            
            for filename in files:
                file_path = root_path / filename
                rel_path = file_path.relative_to(base_path)
                
                if file_path.is_symlink() and not self.follow_symlinks:
                    continue
                
                if self._is_excluded(file_path, rel_path):
                    continue
                
                try:
                    stat = file_path.stat()
                    yield FileEntry(
                        path=file_path,
                        relative_path=rel_path,
                        size=stat.st_size,
                        modified_time=stat.st_mtime
                    )
                except (OSError, PermissionError):
                    continue
