"""
Colored console output using Rich library.
"""

from typing import Any, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskID
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.theme import Theme


class ConsoleOutput:
    """Colored terminal output using Rich."""
    
    def __init__(self):
        self.console = Console(theme=Theme({
            "info": "cyan",
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "debug": "dim",
            "header": "bold magenta",
            "file.missing": "yellow",
            "file.update": "orange3",
            "file.exists": "dim green",
            "file.copied": "green",
            "file.error": "red",
        }))
        self._progress: Optional[Progress] = None
    
    def header(self, title: str) -> None:
        """Print header."""
        self.console.print()
        self.console.print(Panel(f"[header]{title}[/header]", border_style="magenta"))
        self.console.print()
    
    def footer(self) -> None:
        """Print footer."""
        self.console.print()
        self.console.print("─" * 50, style="dim")
    
    def info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"[info]ℹ[/info] {message}")
    
    def success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"[success]✓[/success] {message}")
    
    def warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"[warning]⚠[/warning] {message}")
    
    def error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"[error]✗[/error] {message}")
    
    def debug(self, message: str) -> None:
        """Print debug message."""
        self.console.print(f"[debug]{message}[/debug]")
    
    def file_missing(self, path: str, dest: Optional[str] = None) -> None:
        """Report missing file."""
        if dest:
            self.console.print(f"[file.missing]⊕[/file.missing] [yellow]{path}[/yellow] → {dest}")
        else:
            self.console.print(f"[file.missing]⊕[/file.missing] [yellow]{path}[/yellow] (missing)")
    
    def file_update(self, path: str, dest: str, diff: Optional[str] = None) -> None:
        """Report file update."""
        self.console.print(f"[file.update]↻[/file.update] [orange3]{path}[/orange3] → {dest}")
    
    def file_exists(self, path: str) -> None:
        """Report file exists."""
        self.console.print(f"[file.exists]=[/file.exists] [dim]{path}[/dim]")
    
    def file_copied(self, source: str, dest: str, status: str = "success") -> None:
        """Report file copy result."""
        if status == "success":
            self.console.print(f"[file.copied]✓[/file.copied] Copied: {source} → {dest}")
        else:
            self.console.print(f"[file.error]✗[/file.error] Failed: {source} → {dest} ({status})")
    
    def file_error(self, path: str, error: str) -> None:
        """Report file error."""
        self.console.print(f"[file.error]✗[/file.error] Error with {path}: {error}")
    
    def stats(self, missing: int = 0, update: int = 0, exists: int = 0,
              copied: int = 0, failed: int = 0) -> None:
        """Print statistics."""
        table = Table(title="Statistics", show_header=True, header_style="bold")
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right", style="magenta")
        
        table.add_row("Missing", str(missing))
        table.add_row("Update", str(update))
        table.add_row("Exists", str(exists))
        table.add_row("Copied", f"[green]{copied}[/green]")
        table.add_row("Failed", f"[red]{failed}[/red]" if failed > 0 else "0")
        
        self.console.print()
        self.console.print(table)
    
    def summary(self, action: str, total: int, processed: int) -> None:
        """Print summary."""
        self.console.print()
        if processed == total:
            self.console.print(f"[success]✓ {action} complete: {processed}/{total} items processed[/success]")
        else:
            self.console.print(f"[warning]⚠ {action} partial: {processed}/{total} items processed[/warning]")
    
    def progress_start(self, total: int, description: str = "") -> TaskID:
        """Start progress bar."""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        )
        self._progress.start()
        task_id = self._progress.add_task(description or "Processing...", total=total)
        return task_id
    
    def progress_update(self, task_id: TaskID, advance: int = 1) -> None:
        """Update progress."""
        if self._progress:
            self._progress.update(task_id, advance=advance)
    
    def progress_finish(self, task_id: TaskID) -> None:
        """Finish progress."""
        if self._progress:
            self._progress.stop()
            self._progress = None
    
    def prompt_yes_no(self, message: str, default: bool = False) -> bool:
        """Prompt for yes/no."""
        return Confirm.ask(message, default=default, console=self.console)
    
    def prompt_choice(self, message: str, choices: List[str]) -> str:
    def submodule_status(self, name: str, status: str, details: str = "") -> None:
        """Report submodule status."""
        if status == "clean":
            self.console.print(f"[file.exists]✓[/file.exists] {name}: {details or 'clean'}")
        elif status == "modified":
            self.console.print(f"[file.update]↻[/file.update] {name}: {details or 'modified'}")
        elif status == "error":
            self.console.print(f"[file.error]✗[/file.error] {name}: {details or 'error'}")
        else:
            self.console.print(f"[info]ℹ[/info] {name}: {status} {details}")
    
    def subtree_status(self, name: str, status: str, details: str = "") -> None:
        """Report subtree status."""
        # Use tree emoji for subtrees to distinguish from submodules
        if status == "clean":
            self.console.print(f"[file.exists]🌲[/file.exists] {name}: {details or 'clean'}")
        elif status == "modified":
            self.console.print(f"[file.update]🌲[/file.update] {name}: {details or 'modified'}")
        elif status == "error":
            self.console.print(f"[file.error]🌲[/file.error] {name}: {details or 'error'}")
        else:
            self.console.print(f"[info]🌲[/info] {name}: {status} {details}")
    
    def git_operation(self, repo: str, operation: str, result: str) -> None:
        """Report git operation result."""
        if "error" in result.lower() or "failed" in result.lower():
            self.console.print(f"[error]✗[/error] [{repo}] {operation}: {result}")
        elif "success" in result.lower():
            self.console.print(f"[success]✓[/success] [{repo}] {operation}: {result}")
        else:
            self.console.print(f"[info]ℹ[/info] [{repo}] {operation}: {result}")
    
    def subtree_operation(self, name: str, operation: str, result: str) -> None:
        """Report subtree operation result."""
        # Prefix with tree emoji to indicate subtree
        if "error" in result.lower() or "failed" in result.lower():
            self.console.print(f"[error]🌲[/error] [{name}] {operation}: {result}")
        elif "success" in result.lower():
            self.console.print(f"[success]🌲[/success] [{name}] {operation}: {result}")
        else:
            self.console.print(f"[info]🌲[/info] [{name}] {operation}: {result}")
    def git_operation(self, repo: str, operation: str, result: str) -> None:
        """Report git operation result."""
        if "error" in result.lower() or "failed" in result.lower():
            self.console.print(f"[error]✗[/error] [{repo}] {operation}: {result}")
        elif "success" in result.lower():
            self.console.print(f"[success]✓[/success] [{repo}] {operation}: {result}")
        else:
            self.console.print(f"[info]ℹ[/info] [{repo}] {operation}: {result}")
    
    def finalize(self, results: List[Any]) -> Optional[str]:
        """Finalize output."""
        return None
