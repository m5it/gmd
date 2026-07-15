"""
Interactive mode for file-by-file approval with diff preview.
"""

from enum import Enum
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table

from gmd.core.comparator import FileComparison, FileStatus, FileComparator
from gmd.output.formatter import OutputFormatter


class InteractiveAction(Enum):
    """Actions available in interactive mode."""
    YES = "y"
    NO = "n"
    YES_TO_ALL = "a"
    DIFF = "d"
    SKIP = "s"
    QUIT = "q"


class InteractiveMode:
    """Interactive file approval mode."""
    
    def __init__(self, formatter: OutputFormatter):
        self.formatter = formatter
        self.console = Console()
        self.yes_to_all = False
        self.comparator = FileComparator()
    
    def prompt_file(
        self,
        comparison: FileComparison,
        show_diff: bool = False
    ) -> InteractiveAction:
        """
        Prompt user for action on a single file.
        
        Args:
            comparison: FileComparison to review
            show_diff: Whether to show diff by default
        
        Returns:
            Selected action
        """
        if self.yes_to_all:
            return InteractiveAction.YES
        
        # Display file info
        self._display_file_info(comparison)
        
        # Show diff if requested or if update
        if show_diff or comparison.status == FileStatus.UPDATE:
            self._show_diff(comparison)
        
        # Get user choice
        return self._get_user_choice()
    
    def _display_file_info(self, comparison: FileComparison) -> None:
        """Display file information."""
        status_color = {
            FileStatus.MISSING: "yellow",
            FileStatus.UPDATE: "orange3",
            FileStatus.EXTRA: "red",
        }.get(comparison.status, "white")
        
        title = f"[{status_color}]{comparison.status.name}[/{status_color}]"
        
        table = Table(show_header=False)
        table.add_column("Property", style="cyan")
        table.add_column("Value")
        
        table.add_row("Relative Path", str(comparison.relative_path))
        
        if comparison.master_entry:
            table.add_row(
                "Master",
                f"{comparison.master_entry.path} ({comparison.master_entry.size} bytes)"
            )
        
        if comparison.slave_entry:
            table.add_row(
                "Slave",
                f"{comparison.slave_entry.path} ({comparison.slave_entry.size} bytes)"
            )
        
        if comparison.master_hash and comparison.slave_hash:
            table.add_row("Master Hash", comparison.master_hash[:16] + "...")
            table.add_row("Slave Hash", comparison.slave_hash[:16] + "...")
        
        self.console.print()
        self.console.print(Panel(table, title=title))
    
    def _show_diff(self, comparison: FileComparison) -> None:
        """Show diff between files."""
        if comparison.status not in (FileStatus.UPDATE,):
            self.console.print("[dim]No diff available for this file type.[/dim]")
            return
        
        diff_content = self.comparator.generate_diff(comparison)
        
        if diff_content:
            self.console.print(Panel(
                Syntax(diff_content, "diff", theme="monokai"),
                title="Diff Preview"
            ))
        else:
            self.console.print("[dim]Unable to generate diff (binary file or permission denied).[/dim]")
    
    def _get_user_choice(self) -> InteractiveAction:
        """Get user choice for file action."""
        choices = "[y]es, [n]o, [a]ll, [d]iff, [s]kip, [q]uit"
        
        while True:
            response = Prompt.ask(
                f"Action? {choices}",
                choices=["y", "n", "a", "d", "s", "q"],
                default="y",
                show_choices=False
            ).lower().strip()
            
            if response == "y":
                return InteractiveAction.YES
            elif response == "n":
                return InteractiveAction.NO
            elif response == "a":
                self.yes_to_all = True
                return InteractiveAction.YES_TO_ALL
            elif response == "d":
                return InteractiveAction.DIFF
            elif response == "s":
                return InteractiveAction.SKIP
            elif response == "q":
                return InteractiveAction.QUIT
            
            self.console.print("[red]Invalid choice.[/red]")
    
    def process_files(
        self,
        comparisons: List[FileComparison],
        on_approve: callable,
        on_reject: callable = None
    ) -> dict:
        """
        Process files interactively.
        
        Args:
            comparisons: List of FileComparison to process
            on_approve: Callback when file is approved
            on_reject: Callback when file is rejected
        
        Returns:
            Statistics dict
        """
        approved = 0
        rejected = 0
        skipped = 0
        quit_requested = False
        
        for i, comparison in enumerate(comparisons, 1):
            if quit_requested:
                skipped += 1
                continue
            
            self.console.print(f"\n[dim]File {i}/{len(comparisons)}[/dim]")
            
            action = self.prompt_file(comparison)
            
            if action == InteractiveAction.YES or action == InteractiveAction.YES_TO_ALL:
                if on_approve:
                    on_approve(comparison)
                approved += 1
            
            elif action == InteractiveAction.NO:
                if on_reject:
                    on_reject(comparison)
                rejected += 1
            
            elif action == InteractiveAction.DIFF:
                # Show diff and re-prompt
                self._show_diff(comparison)
                action = self._get_user_choice()
                
                if action in (InteractiveAction.YES, InteractiveAction.YES_TO_ALL):
                    if on_approve:
                        on_approve(comparison)
                    approved += 1
                elif action == InteractiveAction.NO:
                    if on_reject:
                        on_reject(comparison)
                    rejected += 1
                elif action == InteractiveAction.QUIT:
                    quit_requested = True
                    skipped += len(comparisons) - i + 1
                    break
            
            elif action == InteractiveAction.SKIP:
                skipped += 1
            
            elif action == InteractiveAction.QUIT:
                quit_requested = True
                skipped += len(comparisons) - i + 1
                break
        
        return {
            "approved": approved,
            "rejected": rejected,
            "skipped": skipped,
            "total": len(comparisons)
        }
    
    def confirm_batch(
        self,
        missing_count: int = 0,
        update_count: int = 0,
        extra_count: int = 0
    ) -> bool:
        """
        Confirm batch operation before starting.
        
        Returns:
            True if confirmed
        """
        if missing_count == 0 and update_count == 0 and extra_count == 0:
            self.console.print("[green]No changes needed.[/green]")
            return False
        
        table = Table(title="Batch Summary")
        table.add_column("Action", style="cyan")
        table.add_column("Count", justify="right", style="magenta")
        
        if missing_count:
            table.add_row("Add new files", str(missing_count))
        if update_count:
            table.add_row("Update existing files", str(update_count))
        if extra_count:
            table.add_row("Remove extra files", str(extra_count))
        
        self.console.print()
        self.console.print(table)
        
        return Confirm.ask("Proceed with these changes?", default=True)
