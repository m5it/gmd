"""
Plain text output (no colors, suitable for piping/logging).
"""

from typing import Any, List, Optional


class PlainOutput:
    """Plain text output without colors."""
    
    def __init__(self, silent: bool = False):
        self.silent = silent
        self._progress_total = 0
        self._progress_current = 0
    
    def _print(self, message: str) -> None:
        """Print if not silent."""
        if not self.silent:
            print(message)
    
    def header(self, title: str) -> None:
        """Print header."""
        self._print(f"\n{'=' * 50}")
        self._print(f"  {title}")
        self._print(f"{'=' * 50}\n")
    
    def footer(self) -> None:
        """Print footer."""
        self._print(f"\n{'-' * 50}")
    
    def info(self, message: str) -> None:
        """Print info message."""
        self._print(f"INFO: {message}")
    
    def success(self, message: str) -> None:
        """Print success message."""
        self._print(f"SUCCESS: {message}")
    
    def warning(self, message: str) -> None:
        """Print warning message."""
        self._print(f"WARNING: {message}")
    
    def error(self, message: str) -> None:
        """Print error message."""
        self._print(f"ERROR: {message}")
    
    def debug(self, message: str) -> None:
        """Print debug message."""
        self._print(f"DEBUG: {message}")
    
    def file_missing(self, path: str, dest: Optional[str] = None) -> None:
        """Report missing file."""
        if dest:
            self._print(f"[MISSING] {path} -> {dest}")
        else:
            self._print(f"[MISSING] {path}")
    
    def file_update(self, path: str, dest: str, diff: Optional[str] = None) -> None:
        """Report file update."""
        self._print(f"[UPDATE] {path} -> {dest}")
    
    def file_exists(self, path: str) -> None:
        """Report file exists."""
        self._print(f"[EXISTS] {path}")
    
    def file_copied(self, source: str, dest: str, status: str = "success") -> None:
        """Report file copy result."""
        if status == "success":
            self._print(f"[COPIED] {source} -> {dest}")
        else:
            self._print(f"[FAILED] {source} -> {dest}: {status}")
    
    def file_error(self, path: str, error: str) -> None:
        """Report file error."""
        self._print(f"[ERROR] {path}: {error}")
    
    def stats(self, missing: int = 0, update: int = 0, exists: int = 0,
              copied: int = 0, failed: int = 0) -> None:
        """Print statistics."""
        self._print(f"\n--- Statistics ---")
        self._print(f"Missing: {missing}")
        self._print(f"Update: {update}")
        self._print(f"Exists: {exists}")
        self._print(f"Copied: {copied}")
        self._print(f"Failed: {failed}")
        self._print(f"------------------")
    
    def summary(self, action: str, total: int, processed: int) -> None:
        """Print summary."""
        if processed == total:
            self._print(f"\nSUCCESS: {action} complete - {processed}/{total} items")
        else:
            self._print(f"\nPARTIAL: {action} - {processed}/{total} items")
    
    def progress_start(self, total: int, description: str = "") -> int:
        """Start progress tracking."""
        self._progress_total = total
        self._progress_current = 0
        self._print(f"{description or 'Processing'}: 0/{total}")
        return 0
    
    def progress_update(self, task_id: int, advance: int = 1) -> None:
        """Update progress."""
        self._progress_current += advance
        if self._progress_current % 10 == 0 or self._progress_current >= self._progress_total:
            self._print(f"Progress: {self._progress_current}/{self._progress_total}")
    
    def progress_finish(self, task_id: int) -> None:
        """Finish progress."""
        self._print(f"Complete: {self._progress_current}/{self._progress_total}")
    
    def prompt_yes_no(self, message: str, default: bool = False) -> bool:
        """Prompt for yes/no."""
        if self.silent:
            return default
        prompt = f"{message} [{'Y/n' if default else 'y/N'}]: "
        response = input(prompt).strip().lower()
        if not response:
            return default
        return response in ('y', 'yes')
    
    def prompt_choice(self, message: str, choices: List[str]) -> str:
        """Prompt for choice."""
        if self.silent:
            return choices[0] if choices else ""
        self._print(f"{message} ({'/'.join(choices)})")
        while True:
            response = input("> ").strip()
            if response in choices:
                return response
            self._print(f"Invalid choice. Options: {', '.join(choices)}")
    
    def show_diff(self, file1: str, file2: str, diff_content: str) -> None:
        """Show diff between files."""
        self._print(f"\n--- Diff: {file1} vs {file2} ---")
        self._print(diff_content)
        self._print("--- End diff ---")
    
    def submodule_status(self, name: str, status: str, details: str = "") -> None:
        """Report submodule status."""
        self._print(f"[{status.upper()}] {name}: {details or status}")
    
    def git_operation(self, repo: str, operation: str, result: str) -> None:
        """Report git operation result."""
        self._print(f"[{repo}] {operation}: {result}")
    
    def finalize(self, results: List[Any]) -> Optional[str]:
        """Finalize output."""
        return None
