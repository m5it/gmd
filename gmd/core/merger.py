"""
Directory merger with support for multiple sync directions.
"""

import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from gmd.config.schema import SyncDirection
from gmd.core.comparator import ComparisonResult, FileComparison, FileStatus


class MergeResult(Enum):
    """Result of a merge operation."""
    SUCCESS = auto()
    FAILED = auto()
    SKIPPED = auto()
    VERIFIED = auto()


@dataclass
class MergeOperation:
    """Record of a merge operation."""
    comparison: FileComparison
    direction: SyncDirection
    result: MergeResult
    message: str = ""
    backup_path: Optional[Path] = None


@dataclass
class MergeReport:
    """Report of merge operations."""
    operations: List[MergeOperation] = field(default_factory=list)
    
    @property
    def successful(self) -> List[MergeOperation]:
        return [op for op in self.operations if op.result == MergeResult.SUCCESS]
    
    @property
    def failed(self) -> List[MergeOperation]:
        return [op for op in self.operations if op.result == MergeResult.FAILED]
    
    @property
    def skipped(self) -> List[MergeOperation]:
        return [op for op in self.operations if op.result == MergeResult.SKIPPED]
    
    def get_stats(self) -> dict:
        return {
            "total": len(self.operations),
            "success": len(self.successful),
            "failed": len(self.failed),
            "skipped": len(self.skipped)
        }


class DirectoryMerger:
    """Merge directories with direction support."""
    
    def __init__(
        self,
        direction: SyncDirection = SyncDirection.MASTER_TO_SLAVE,
        verify: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ):
        self.direction = direction
        self.verify = verify
        self.progress_callback = progress_callback
    
    def _get_source_dest(
        self,
        comparison: FileComparison
    ) -> Tuple[Optional[Path], Optional[Path]]:
        """Get source and destination based on direction."""
        if self.direction == SyncDirection.MASTER_TO_SLAVE:
            return comparison.source_path, comparison.dest_path
        elif self.direction == SyncDirection.SLAVE_TO_MASTER:
            # Reverse: slave is source, master is destination
            if comparison.status == FileStatus.EXTRA:
                # Extra file in slave -> copy to master
                return comparison.slave_entry.path if comparison.slave_entry else None, \
                       comparison.master_entry.path if comparison.master_entry else None
            else:
                return comparison.slave_entry.path if comparison.slave_entry else None, \
                       comparison.master_entry.path if comparison.master_entry else None
        elif self.direction == SyncDirection.BIDIRECTIONAL:
            # Use newer file as source
            if comparison.status == FileStatus.EXTRA:
                return comparison.slave_entry.path if comparison.slave_entry else None, \
                       comparison.master_entry.path if comparison.master_entry else None
            elif comparison.master_entry and comparison.slave_entry:
                if comparison.master_entry.modified_time > comparison.slave_entry.modified_time:
                    return comparison.master_entry.path, comparison.slave_entry.path
                else:
                    return comparison.slave_entry.path, comparison.master_entry.path
            else:
                return comparison.source_path, comparison.dest_path
        
        return None, None
    
    def _ensure_parent_dir(self, path: Path) -> bool:
        """Ensure parent directory exists."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            return True
        except OSError as e:
            return False
    
    def _copy_file(
        self,
        source: Path,
        dest: Path
    ) -> Tuple[bool, str]:
        """
        Copy file from source to destination.
        
        Returns (success, message).
        """
        try:
            # Ensure parent directory exists
            if not self._ensure_parent_dir(dest):
                return False, f"Failed to create parent directory for {dest}"
            
            # Copy file with metadata
            shutil.copy2(source, dest)
            
            # Verify copy if enabled
            if self.verify:
                if not self._verify_copy(source, dest):
                    return False, "Verification failed: files differ after copy"
            
            return True, "Copied successfully"
            
        except PermissionError as e:
            return False, f"Permission denied: {e}"
        except OSError as e:
            return False, f"OS error: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def _verify_copy(self, source: Path, dest: Path) -> bool:
        """Verify that files are identical after copy."""
        try:
            # Compare sizes
            if source.stat().st_size != dest.stat().st_size:
                return False
            
            # Compare hashes for small files
            if source.stat().st_size < 10 * 1024 * 1024:  # 10MB
                import hashlib
                source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
                dest_hash = hashlib.sha256(dest.read_bytes()).hexdigest()
                return source_hash == dest_hash
            
            # For large files, just check they exist and sizes match
            return True
            
        except (OSError, PermissionError):
            return False
    
    def merge(
        self,
        comparison: FileComparison,
        dry_run: bool = False
    ) -> MergeOperation:
        """
        Execute merge for a single file comparison.
        
        Args:
            comparison: FileComparison to process
            dry_run: If True, don't actually copy
        
        Returns:
            MergeOperation with result
        """
        source, dest = self._get_source_dest(comparison)
        
        if source is None:
            return MergeOperation(
                comparison=comparison,
                direction=self.direction,
                result=MergeResult.SKIPPED,
                message="No source file"
            )
        
        if dry_run:
            return MergeOperation(
                comparison=comparison,
                direction=self.direction,
                result=MergeResult.SKIPPED,
                message=f"Would copy: {source} -> {dest}"
            )
        
        # Perform copy
        success, message = self._copy_file(source, dest)
        
        return MergeOperation(
            comparison=comparison,
            direction=self.direction,
            result=MergeResult.SUCCESS if success else MergeResult.FAILED,
            message=message
        )
    
    def merge_all(
        self,
        comparison_result: ComparisonResult,
        categories: Optional[List[FileStatus]] = None,
        dry_run: bool = False
    ) -> MergeReport:
        """
        Merge all files from comparison result.
        
        Args:
            comparison_result: Result from FileComparator
            categories: Which categories to process (default: MISSING, UPDATE)
            dry_run: If True, don't actually copy
        
        Returns:
            MergeReport with all operations
        """
        categories = categories or [FileStatus.MISSING, FileStatus.UPDATE]
        
        report = MergeReport()
        all_comparisons = []
        
        # Collect comparisons to process
        if FileStatus.MISSING in categories:
            all_comparisons.extend(comparison_result.missing)
        if FileStatus.UPDATE in categories:
            all_comparisons.extend(comparison_result.update)
        if FileStatus.EXTRA in categories:
            all_comparisons.extend(comparison_result.extra)
        
        total = len(all_comparisons)
        
        for i, comparison in enumerate(all_comparisons):
            operation = self.merge(comparison, dry_run=dry_run)
            report.operations.append(operation)
            
            if self.progress_callback and (i + 1) % 10 == 0:
                self.progress_callback(i + 1, total, str(comparison.relative_path))
        
        # Final progress
        if self.progress_callback:
            self.progress_callback(total, total, "complete")
        
        return report
    
    def delete_extra(
        self,
        comparison_result: ComparisonResult,
        dry_run: bool = False
    ) -> MergeReport:
        """
        Delete extra files from slave (for bidirectional cleanup).
        
        Args:
            comparison_result: Result from FileComparator
            dry_run: If True, don't actually delete
        
        Returns:
            MergeReport with delete operations
        """
        report = MergeReport()
        
        for comparison in comparison_result.extra:
            if dry_run:
                report.operations.append(MergeOperation(
                    comparison=comparison,
                    direction=self.direction,
                    result=MergeResult.SKIPPED,
                    message=f"Would delete: {comparison.slave_entry.path if comparison.slave_entry else '?'}"
                ))
                continue
            
            try:
                if comparison.slave_entry:
                    comparison.slave_entry.path.unlink()
                    report.operations.append(MergeOperation(
                        comparison=comparison,
                        direction=self.direction,
                        result=MergeResult.SUCCESS,
                        message=f"Deleted: {comparison.slave_entry.path}"
                    ))
            except Exception as e:
                report.operations.append(MergeOperation(
                    comparison=comparison,
                    direction=self.direction,
                    result=MergeResult.FAILED,
                    message=f"Failed to delete: {e}"
                ))
        
        return report
