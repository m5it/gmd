"""
JSON output formatter for machine-readable output.
"""

import json
from datetime import datetime
from typing import Any, List, Optional


class JsonOutput:
    """JSON output formatter."""
    
    def __init__(self):
        self._data = {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "messages": [],
            "files": [],
            "stats": {},
            "summary": {}
        }
        self._silent = False
    
    def _add_message(self, level: str, message: str, **kwargs) -> None:
        """Add a message to the data."""
        self._data["messages"].append({
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        })
    
    def header(self, title: str) -> None:
        """Print header."""
        self._data["title"] = title
    
    def footer(self) -> None:
        """Print footer."""
        pass
    
    def info(self, message: str) -> None:
        """Print info message."""
        self._add_message("info", message)
    
    def success(self, message: str) -> None:
        """Print success message."""
        self._add_message("success", message)
    
    def warning(self, message: str) -> None:
        """Print warning message."""
        self._add_message("warning", message)
    
    def error(self, message: str) -> None:
        """Print error message."""
        self._add_message("error", message)
    
    def debug(self, message: str) -> None:
        """Print debug message."""
        self._add_message("debug", message)
    
    def file_missing(self, path: str, dest: Optional[str] = None) -> None:
        """Report missing file."""
        self._data["files"].append({
            "type": "missing",
            "source": path,
            "destination": dest,
            "timestamp": datetime.now().isoformat()
        })
    
    def file_update(self, path: str, dest: str, diff: Optional[str] = None) -> None:
        """Report file update."""
        self._data["files"].append({
            "type": "update",
            "source": path,
            "destination": dest,
            "has_diff": diff is not None,
            "timestamp": datetime.now().isoformat()
        })
    
    def file_exists(self, path: str) -> None:
        """Report file exists."""
        self._data["files"].append({
            "type": "exists",
            "path": path,
            "timestamp": datetime.now().isoformat()
        })
    
    def file_copied(self, source: str, dest: str, status: str = "success") -> None:
        """Report file copy result."""
        self._data["files"].append({
            "type": "copied",
            "source": source,
            "destination": dest,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
    
    def file_error(self, path: str, error: str) -> None:
        """Report file error."""
        self._data["files"].append({
            "type": "error",
            "path": path,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
    
    def stats(self, missing: int = 0, update: int = 0, exists: int = 0,
              copied: int = 0, failed: int = 0) -> None:
        """Print statistics."""
        self._data["stats"] = {
            "missing": missing,
            "update": update,
            "exists": exists,
            "copied": copied,
            "failed": failed,
            "total": missing + update + exists
        }
    
    def summary(self, action: str, total: int, processed: int) -> None:
        """Print summary."""
        self._data["summary"] = {
            "action": action,
            "total": total,
            "processed": processed,
            "complete": processed == total,
            "timestamp": datetime.now().isoformat()
        }
    
    def progress_start(self, total: int, description: str = "") -> int:
        """Start progress tracking."""
        self._data["progress"] = {
            "total": total,
            "current": 0,
            "description": description
        }
        return 0
    
    def progress_update(self, task_id: int, advance: int = 1) -> None:
        """Update progress."""
        if "progress" in self._data:
            self._data["progress"]["current"] += advance
    
    def progress_finish(self, task_id: int) -> None:
        """Finish progress."""
        if "progress" in self._data:
            self._data["progress"]["complete"] = True
    
    def prompt_yes_no(self, message: str, default: bool = False) -> bool:
        """Prompt for yes/no - not supported in JSON mode, returns default."""
        return default
    
    def prompt_choice(self, message: str, choices: List[str]) -> str:
        """Prompt for choice - not supported in JSON mode, returns first choice."""
        return choices[0] if choices else ""
    
    def show_diff(self, file1: str, file2: str, diff_content: str) -> None:
        """Show diff between files."""
        self._data.setdefault("diffs", []).append({
            "file1": file1,
            "file2": file2,
            "content": diff_content
        })
    
    def submodule_status(self, name: str, status: str, details: str = "") -> None:
        """Report submodule status."""
        self._data.setdefault("submodules", []).append({
            "name": name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    def git_operation(self, repo: str, operation: str, result: str) -> None:
        """Report git operation result."""
        self._data.setdefault("git_operations", []).append({
            "repo": repo,
            "operation": operation,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
    
    def finalize(self, results: List[Any]) -> Optional[str]:
        """Finalize output and return JSON string."""
        json_output = json.dumps(self._data, indent=2, default=str)
        print(json_output)
        return json_output
    
    def get_data(self) -> dict:
        """Get collected data."""
        return self._data
