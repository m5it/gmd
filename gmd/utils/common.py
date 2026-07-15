"""
Common utility functions shared across GMD modules.
"""

import os
import platform
import shutil
from pathlib import Path
from typing import List, Optional, Tuple


def format_size(size_bytes: int) -> str:
    """Format byte size to human readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"


def format_time(seconds: float) -> str:
    """Format seconds to human readable string."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def ensure_dir(path: Path) -> bool:
    """Ensure directory exists, create if needed."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def safe_copy(src: Path, dst: Path, verify: bool = False) -> Tuple[bool, str]:
    """
    Safely copy file with verification.
    
    Returns (success, message).
    """
    try:
        # Ensure parent directory exists
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy with metadata
        shutil.copy2(src, dst)
        
        # Verify if requested
        if verify:
            if not verify_copy(src, dst):
                return False, "Verification failed: files differ after copy"
        
        return True, "Copied successfully"
        
    except PermissionError:
        return False, "Permission denied"
    except OSError as e:
        return False, f"OS error: {e}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def verify_copy(src: Path, dst: Path) -> bool:
    """Verify files are identical after copy."""
    try:
        # Quick check: sizes
        if src.stat().st_size != dst.stat().st_size:
            return False
        
        # For small files, compare hashes
        if src.stat().st_size < 10 * 1024 * 1024:  # 10MB
            import hashlib
            src_hash = hashlib.sha256(src.read_bytes()).hexdigest()
            dst_hash = hashlib.sha256(dst.read_bytes()).hexdigest()
            return src_hash == dst_hash
        
        return True
        
    except (OSError, PermissionError):
        return False


def is_binary_file(path: Path, sample_size: int = 8192) -> bool:
    """
    Check if file is binary by looking for null bytes.
    
    Returns True if binary, False if text.
    """
    try:
        with open(path, 'rb') as f:
            chunk = f.read(sample_size)
            return b'\x00' in chunk
    except (OSError, PermissionError):
        return True  # Assume binary if can't read


def find_files(
    directory: Path,
    pattern: str = "*",
    recursive: bool = True
) -> List[Path]:
    """
    Find files matching pattern.
    
    Args:
        directory: Directory to search
        pattern: Glob pattern
        recursive: Whether to search recursively
    
    Returns:
        List of matching file paths
    """
    if recursive:
        return list(directory.rglob(pattern))
    else:
        return list(directory.glob(pattern))


def get_disk_usage(path: Path) -> Tuple[int, int, int]:
    """
    Get disk usage for a path.
    
    Returns (total, used, free) in bytes.
    """
    try:
        stat = shutil.disk_usage(path)
        return stat.total, stat.used, stat.free
    except OSError:
        return 0, 0, 0


def truncate_path(path: Path, max_length: int = 60) -> str:
    """Truncate long paths for display."""
    path_str = str(path)
    if len(path_str) <= max_length:
        return path_str
    
    # Keep beginning and end
    start = max_length // 2 - 3
    end = max_length // 2 - 3
    return path_str[:start] + "..." + path_str[-end:]


def get_terminal_width() -> int:
    """Get terminal width, default to 80."""
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 80


def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
    """Pluralize word based on count."""
    if count == 1:
        return f"{count} {singular}"
    
    if plural is None:
        plural = singular + "s"
    
    return f"{count} {plural}"


def confirm_overwrite(path: Path) -> bool:
    """Confirm file overwrite with user."""
    if not path.exists():
        return True
    
    response = input(f"File {path} exists. Overwrite? [y/N]: ").strip().lower()
    return response in ('y', 'yes')


def safe_delete(path: Path) -> Tuple[bool, str]:
    """
    Safely delete file or directory.
    
    Returns (success, message).
    """
    try:
        if path.is_file() or path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        else:
            return False, f"Unknown file type: {path}"
        
        return True, "Deleted successfully"
        
    except PermissionError:
        return False, "Permission denied"
    except OSError as e:
        return False, f"OS error: {e}"


def get_system_info() -> dict:
    """Get system information."""
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
    }
