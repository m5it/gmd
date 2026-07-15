"""
Output formatter dispatcher.
Routes output to the appropriate formatter based on configuration.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from gmd.config.schema import OutputFormat, OutputConfig
from gmd.output.console import ConsoleOutput
from gmd.output.plain import PlainOutput
from gmd.output.json_fmt import JsonOutput


class OutputFormatter:
    """Dispatcher for output formatting."""
    
    def __init__(self, config: OutputConfig):
        self.config = config
        self._formatter = self._create_formatter()
        self._results: List[Dict[str, Any]] = []
    
    def _create_formatter(self):
        """Create the appropriate formatter based on config."""
        if self.config.format == OutputFormat.COLOR:
            return ConsoleOutput()
        elif self.config.format == OutputFormat.PLAIN:
            return PlainOutput()
        elif self.config.format == OutputFormat.JSON:
            return JsonOutput()
        elif self.config.format == OutputFormat.SILENT:
            return PlainOutput(silent=True)
        else:
            return ConsoleOutput()
    
    # Header/Footer
    def header(self, title: str) -> None:
        """Print header."""
        self._formatter.header(title)
    
    def footer(self) -> None:
        """Print footer."""
        self._formatter.footer()
    
    # Info messages
    def info(self, message: str) -> None:
        """Print info message."""
        self._formatter.info(message)
    
    def success(self, message: str) -> None:
        """Print success message."""
        self._formatter.success(message)
    
    def warning(self, message: str) -> None:
        """Print warning message."""
        self._formatter.warning(message)
    
    def error(self, message: str) -> None:
        """Print error message."""
        self._formatter.error(message)
    
    def debug(self, message: str) -> None:
        """Print debug message."""
        self._formatter.debug(message)
    
    # File operations
    def file_missing(self, path: str, dest: Optional[str] = None) -> None:
        """Report missing file (will be copied)."""
        self._formatter.file_missing(path, dest)
        self._results.append({
            "type": "missing",
            "source": path,
            "destination": dest
        })
    
    def file_update(self, path: str, dest: str, diff: Optional[str] = None) -> None:
        """Report file update (different content)."""
        self._formatter.file_update(path, dest, diff)
        self._results.append({
            "type": "update",
            "source": path,
            "destination": dest,
            "has_diff": diff is not None
        })
    
    def file_exists(self, path: str) -> None:
        """Report file exists (identical)."""
        self._formatter.file_exists(path)
        self._results.append({
            "type": "exists",
            "path": path
        })
    
    def file_copied(self, source: str, dest: str, status: str = "success") -> None:
        """Report file copy result."""
        self._formatter.file_copied(source, dest, status)
        self._results.append({
            "type": "copied",
            "source": source,
            "destination": dest,
            "status": status
        })
    
    def file_error(self, path: str, error: str) -> None:
        """Report file error."""
        self._formatter.file_error(path, error)
        self._results.append({
            "type": "error",
            "path": path,
            "error": error
        })
    
    # Statistics
    def stats(self, missing: int = 0, update: int = 0, exists: int = 0, 
              copied: int = 0, failed: int = 0) -> None:
        """Print statistics."""
        self._formatter.stats(missing, update, exists, copied, failed)
    
    # Summary
    def summary(self, action: str, total: int, processed: int) -> None:
        """Print summary."""
        self._formatter.summary(action, total, processed)
    
    # Progress
    def progress_start(self, total: int, description: str = "") -> Any:
        """Start progress bar."""
        if self.config.progress:
            return self._formatter.progress_start(total, description)
        return None
    
    def progress_update(self, progress_id: Any, advance: int = 1) -> None:
        """Update progress."""
        if self.config.progress and progress_id is not None:
            self._formatter.progress_update(progress_id, advance)
    
    def progress_finish(self, progress_id: Any) -> None:
        """Finish progress."""
        if self.config.progress and progress_id is not None:
            self._formatter.progress_finish(progress_id)
    
    # Interactive
    def prompt_yes_no(self, message: str, default: bool = False) -> bool:
        """Prompt for yes/no."""
        return self._formatter.prompt_yes_no(message, default)
    
    def prompt_choice(self, message: str, choices: List[str]) -> str:
        """Prompt for choice."""
        return self._formatter.prompt_choice(message, choices)
    
    def show_diff(self, file1: str, file2: str, diff_content: str) -> None:
        """Show diff between files."""
        self._formatter.show_diff(file1, file2, diff_content)
    
    # Git operations
    def submodule_status(self, name: str, status: str, details: str = "") -> None:
        """Report submodule status."""
        self._formatter.submodule_status(name, status, details)
    
    def git_operation(self, repo: str, operation: str, result: str) -> None:
        """Report git operation result."""
        self._formatter.git_operation(repo, operation, result)
    
    # Final output
    def finalize(self) -> Optional[str]:
        """Finalize output and return JSON if applicable."""
        return self._formatter.finalize(self._results)
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get collected results."""
        return self._results
