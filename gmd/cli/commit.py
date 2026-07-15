#!/usr/bin/env python3
"""
GMD Commit CLI - Git submodule batch commit tool.
"""

import concurrent.futures
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import click

from gmd.config.loader import ConfigLoader
from gmd.config.schema import GMDConfig, OutputFormat
from gmd.output.formatter import OutputFormatter


@dataclass
class Submodule:
    """Represents a git submodule."""
    name: str
    path: Path
    url: Optional[str] = None
    
    def __hash__(self) -> int:
        return hash(self.path)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Submodule):
            return NotImplemented
        return self.path == other.path


class GitSubmoduleManager:
    """Manage git submodules."""
    
    def __init__(self, gitdir: Path, formatter: OutputFormatter):
        self.gitdir = gitdir.resolve()
        self.formatter = formatter
    
    def detect_submodules(self) -> List[Submodule]:
        """Auto-detect submodules from .gitmodules file."""
        gitmodules_path = self.gitdir / ".gitmodules"
        
        if not gitmodules_path.exists():
            return []
        
        submodules = []
        content = gitmodules_path.read_text(encoding="utf-8")
        
        # Parse [submodule "name"] sections
        submodule_pattern = r'\[submodule\s+"([^"]+)"\]\s*path\s*=\s*([^\n]+)'
        matches = re.findall(submodule_pattern, content, re.MULTILINE)
        
        for name, path_str in matches:
            path = (self.gitdir / path_str.strip()).resolve()
            if path.exists():
                submodules.append(Submodule(name=name, path=path))
        
        return submodules
    
    def get_submodule_status(self, submodule: Submodule) -> Tuple[str, str]:
        """
        Get status of a submodule.
        
        Returns (status, details) where status is:
        - "clean": no changes
        - "modified": has changes
        - "error": error checking status
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=submodule.path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return "error", result.stderr.strip()
            
            lines = [line for line in result.stdout.strip().split("\n") if line]
            
            if not lines:
                return "clean", "no changes"
            
            # Count changes
            modified = len([l for l in lines if l.startswith(" M") or l.startswith("M")])
            added = len([l for l in lines if l.startswith("??") or l.startswith("A")])
            deleted = len([l for l in lines if l.startswith(" D") or l.startswith("D")])
            
            details = []
            if modified:
                details.append(f"{modified} modified")
            if added:
                details.append(f"{added} added")
            if deleted:
                details.append(f"{deleted} deleted")
            
            return "modified", ", ".join(details) if details else "changes detected"
            
        except subprocess.TimeoutExpired:
            return "error", "timeout"
        except Exception as e:
            return "error", str(e)
    
    def has_changes(self, submodule: Submodule) -> bool:
        """Check if submodule has uncommitted changes."""
        status, _ = self.get_submodule_status(submodule)
        return status == "modified"
    
    def git_add(self, submodule: Submodule, dry_run: bool = False) -> Tuple[bool, str]:
        """Run git add . in submodule."""
        if dry_run:
            return True, "Would add all files"
        
        try:
            result = subprocess.run(
                ["git", "add", "."],
                cwd=submodule.path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, "Added all files"
            else:
                return False, result.stderr.strip()
                
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    def git_commit(self, submodule: Submodule, message: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Run git commit in submodule."""
        if dry_run:
            return True, f"Would commit with message: {message}"
        
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=submodule.path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, "Committed successfully"
            elif "nothing to commit" in result.stdout.lower():
                return True, "Nothing to commit"
            else:
                return False, result.stderr.strip()
                
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    def git_push(self, submodule: Submodule, dry_run: bool = False) -> Tuple[bool, str]:
        """Run git push in submodule."""
        if dry_run:
            return True, "Would push to remote"
        
        try:
            result = subprocess.run(
                ["git", "push"],
                cwd=submodule.path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, "Pushed successfully"
            else:
                return False, result.stderr.strip()
                
        except subprocess.TimeoutExpired:
            return False, "Timeout"
        except Exception as e:
            return False, str(e)
    
    def process_submodule(
        self,
        submodule: Submodule,
        operation: str,
        message: str = "",
        push: bool = False,
        dry_run: bool = False
    ) -> dict:
        """
        Process a single submodule.
        
        Returns dict with results.
        """
        result = {
            "name": submodule.name,
            "path": str(submodule.path),
            "operation": operation,
            "steps": []
        }
        
        if operation == "status":
            status, details = self.get_submodule_status(submodule)
            result["status"] = status
            result["details"] = details
            self.formatter.submodule_status(submodule.name, status, details)
            return result
        
        # For other operations, only process if has changes (or force)
        if operation != "full" and not self.has_changes(submodule):
            result["skipped"] = True
            result["reason"] = "no changes"
            self.formatter.submodule_status(submodule.name, "clean", "skipped - no changes")
            return result
        
        # Execute operation
        if operation in ("add", "full"):
            success, msg = self.git_add(submodule, dry_run)
            result["steps"].append({"action": "add", "success": success, "message": msg})
            self.formatter.git_operation(submodule.name, "add", msg if success else f"failed: {msg}")
            
            if not success:
                result["success"] = False
                return result
        
        if operation in ("commit", "full"):
            success, msg = self.git_commit(submodule, message, dry_run)
            result["steps"].append({"action": "commit", "success": success, "message": msg})
            self.formatter.git_operation(submodule.name, "commit", msg if success else f"failed: {msg}")
            
            if not success:
                result["success"] = False
                return result
        
        if push and operation in ("push", "full"):
            success, msg = self.git_push(submodule, dry_run)
            result["steps"].append({"action": "push", "success": success, "message": msg})
            self.formatter.git_operation(submodule.name, "push", msg if success else f"failed: {msg}")
            
            if not success:
                result["success"] = False
                return result
        
        result["success"] = all(step.get("success", True) for step in result["steps"])
        return result


@click.command()
@click.option(
    "-M", "--directory",
    "gitdir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Git directory containing submodules"
)
@click.option(
    "-m", "--message",
    default="Update submodules",
    help="Commit message"
)
@click.option(
    "-c", "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Configuration file path"
)
@click.option(
    "-f", "--format",
    "output_format",
    type=click.Choice(["color", "plain", "json", "silent"], case_sensitive=False),
    default=None,
    help="Output format"
)
@click.option(
    "-n", "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes"
)
@click.option(
    "--push",
    is_flag=True,
    help="Push after commit"
)
@click.option(
    "-o", "--operation",
    type=click.Choice(["status", "add", "commit", "push", "full"], case_sensitive=False),
    default="full",
    help="Operation to perform"
)
@click.option(
    "--submodules",
    multiple=True,
    help="Specific submodules to process (default: auto-detect)"
)
@click.option(
    "-j", "--jobs",
    type=int,
    default=4,
    help="Number of parallel workers"
)
@click.version_option(version="1.0.0", prog_name="gmd-commit")
def main(
    gitdir: Optional[Path],
    message: str,
    config: Optional[Path],
    output_format: Optional[str],
    dry_run: bool,
    push: bool,
    operation: str,
    submodules: tuple,
    jobs: int,
) -> int:
    """
    GMD Commit - Git submodule batch commit tool.
    
    Automatically commit changes across multiple git submodules.
    """
    # Load configuration
    try:
        loader = ConfigLoader(config_path=config)
        config_obj = loader.load()
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        return 1
    
    # Merge CLI args with config
    cli_args = {}
    if gitdir:
        cli_args["gitdir"] = gitdir
    if output_format:
        cli_args["output"] = {"format": OutputFormat(output_format)}
    if push:
        cli_args.setdefault("commit", {})["auto_push"] = True
    
    # Apply CLI overrides
    if cli_args:
        config_obj = loader.merge_with_cli(cli_args)
    
    # Validate gitdir
    if not config_obj.gitdir:
        click.echo("Error: --directory is required (or set in config file)", err=True)
        click.echo("\nUsage: gmd-commit -M /path/to/repo [options]")
        return 1
    
    # Setup output formatter
    formatter = OutputFormatter(config_obj.output)
    
    # Display header
    formatter.header("GMD Commit v1.0.0")
    formatter.info(f"Directory: {config_obj.gitdir}")
    formatter.info(f"Operation: {operation}")
    if operation in ("commit", "full"):
        formatter.info(f"Message: {message}")
    
    # Create manager
    manager = GitSubmoduleManager(config_obj.gitdir, formatter)
    
    # Get submodules
    if submodules:
        # Manual list
        submodule_list = [
            Submodule(name=Path(s).name, path=(config_obj.gitdir / s).resolve())
            for s in submodules
        ]
    else:
        # Auto-detect
        submodule_list = manager.detect_submodules()
    
    if not submodule_list:
        formatter.warning("No submodules found!")
        return 0
    
    formatter.info(f"Found {len(submodule_list)} submodules")
    
    # Filter to changed submodules (except for status)
    if operation != "status":
        changed_submodules = [s for s in submodule_list if manager.has_changes(s)]
        formatter.info(f"{len(changed_submodules)} submodules have changes")
        
        if not changed_submodules:
            formatter.success("All submodules are clean - nothing to do!")
            return 0
        
        submodule_list = changed_submodules
    
    # Confirm before making changes
    if operation != "status" and not dry_run:
        if not click.confirm(f"Process {len(submodule_list)} submodules?"):
            formatter.info("Cancelled.")
            return 0
    
    # Process submodules
    formatter.header(f"Executing: {operation}")
    
    results = []
    
    if config_obj.commit.parallel and len(submodule_list) > 1 and jobs > 1:
        # Parallel processing
        formatter.info(f"Processing with {jobs} workers...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
            future_to_submodule = {
                executor.submit(
                    manager.process_submodule,
                    sub,
                    operation,
                    message,
                    push or config_obj.commit.auto_push,
                    dry_run
                ): sub for sub in submodule_list
            }
            
            for future in concurrent.futures.as_completed(future_to_submodule):
                sub = future_to_submodule[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        "name": sub.name,
                        "path": str(sub.path),
                        "success": False,
                        "error": str(e)
                    })
    else:
        # Sequential processing
        for sub in submodule_list:
            result = manager.process_submodule(
                sub,
                operation,
                message,
                push or config_obj.commit.auto_push,
                dry_run
            )
            results.append(result)
    
    # Summary
    formatter.header("Summary")
    
    successful = sum(1 for r in results if r.get("success", False))
    failed = len(results) - successful
    
    formatter.stats(
        missing=0,
        update=0,
        exists=0,
        copied=successful,
        failed=failed
    )
    
    if dry_run:
        formatter.info("(Dry run - no changes made)")
    
    formatter.footer()
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
