"""
Progress bar utilities using Rich library.
"""

from typing import Optional, Any

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskID,
    TimeRemainingColumn,
    TimeElapsedColumn,
    MofNCompleteColumn
)


class ProgressManager:
    """Manage progress bars for long-running operations."""
    
    def __init__(
        self,
        description: str = "Processing...",
        total: Optional[int] = None,
        show_speed: bool = True
    ):
        self.description = description
        self.total = total
        self.show_speed = show_speed
        self._progress: Optional[Progress] = None
        self._task_id: Optional[TaskID] = None
        self._console = Console()
    
    def __enter__(self) -> "ProgressManager":
        """Start progress context."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop progress context."""
        self.stop()
    
    def start(self) -> TaskID:
        """Start the progress bar."""
        columns = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            " ",
            TimeElapsedColumn(),
        ]
        
        if self.show_speed:
            columns.append(TextColumn("[{task.fields[speed]:.1f} it/s]"))
        
        columns.append(TimeRemainingColumn())
        
        self._progress = Progress(*columns, console=self._console)
        self._progress.start()
        
        self._task_id = self._progress.add_task(
            self.description,
            total=self.total,
            speed=0.0
        )
        
        return self._task_id
    
    def update(
        self,
        advance: int = 1,
        description: Optional[str] = None,
        total: Optional[int] = None
    ) -> None:
        """Update progress."""
        if self._progress and self._task_id is not None:
            kwargs = {"advance": advance}
            
            if description:
                kwargs["description"] = description
            
            if total is not None:
                kwargs["total"] = total
            
            # Calculate speed
            task = self._progress.tasks[self._task_id]
            if task.elapsed and task.elapsed > 0:
                speed = task.completed / task.elapsed
                kwargs["speed"] = speed
            
            self._progress.update(self._task_id, **kwargs)
    
    def set_total(self, total: int) -> None:
        """Update total."""
        if self._progress and self._task_id is not None:
            self._progress.update(self._task_id, total=total)
    
    def set_description(self, description: str) -> None:
        """Update description."""
        if self._progress and self._task_id is not None:
            self._progress.update(self._task_id, description=description)
    
    def stop(self) -> None:
        """Stop and cleanup progress bar."""
        if self._progress:
            self._progress.stop()
            self._progress = None
            self._task_id = None


class MultiProgressManager:
    """Manage multiple progress bars simultaneously."""
    
    def __init__(self):
        self._progress: Optional[Progress] = None
        self._tasks: dict[str, TaskID] = {}
        self._console = Console()
    
    def __enter__(self) -> "MultiProgressManager":
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()
    
    def start(self) -> None:
        """Start multi-task progress."""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            " ",
            TimeElapsedColumn(),
            console=self._console
        )
        self._progress.start()
    
    def add_task(self, name: str, description: str, total: int) -> TaskID:
        """Add a new task."""
        if self._progress:
            task_id = self._progress.add_task(description, total=total)
            self._tasks[name] = task_id
            return task_id
        return None
    
    def update(self, name: str, advance: int = 1) -> None:
        """Update a specific task."""
        if self._progress and name in self._tasks:
            self._progress.update(self._tasks[name], advance=advance)
    
    def complete(self, name: str) -> None:
        """Mark a task as complete."""
        if self._progress and name in self._tasks:
            task = self._progress.tasks[self._tasks[name]]
            self._progress.update(self._tasks[name], completed=task.total)
    
    def stop(self) -> None:
        """Stop all progress bars."""
        if self._progress:
            self._progress.stop()
            self._progress = None
            self._tasks.clear()


class ProgressCallback:
    """Adapter to use ProgressManager with callback-style APIs."""
    
    def __init__(self, manager: ProgressManager):
        self.manager = manager
    
    def __call__(self, current: int, total: int, message: str = "") -> None:
        """Callback signature: (current, total, message)."""
        if self.manager._task_id is None:
            self.manager.start()
        
        # Update total if changed
        if self.manager.total != total:
            self.manager.set_total(total)
        
        # Update description if provided
        if message and message != "complete":
            self.manager.set_description(f"{self.manager.description}: {message}")
        
        # Advance to current position
        task = self.manager._progress.tasks[self.manager._task_id]
        if current > task.completed:
            self.manager.update(advance=current - task.completed)
