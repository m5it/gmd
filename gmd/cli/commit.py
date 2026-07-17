#!/usr/bin/env python3
"""
GMD Commit CLI - Git submodule and subtree batch commit tool.
"""

import concurrent.futures
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Union

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


@dataclass
class Subtree:
    """Represents a git subtree."""
    name: str
    path: Path
    url: Optional[str] = None
    prefix: Optional[str] = None
    
    def __hash__(self) -> int:
        return hash(self.path)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Subtree):
            return NotImplemented
        return self.path == other.path


class GitSubmoduleManager:
    """Manage git submodules and subtrees."""
    
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
    
    def detect_subtrees(self) -> List[Subtree]:
        """Auto-detect subtrees from git log."""
        try:
            result = subprocess.run(
                ["git", "log", "--all", "--oneline", "--grep=git-subtree-dir:"],
                cwd=self.gitdir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return []
            
            subtrees = []
            seen_paths = set()
            
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                
                commit_hash = line.split()[0]
                
                commit_result = subprocess.run(
                    ["git", "show", "--format=full", "--no-patch", commit_hash],
                    cwd=self.gitdir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if commit_result.returncode != 0:
                    continue
                
                message = commit_result.stdout
                
                dir_match = re.search(r'git-subtree-dir: ([^\n]+)', message)
                if not dir_match:
                    continue
                
                subtree_path_str = dir_match.group(1).strip()
                subtree_path = (self.gitdir / subtree_path_str).resolve()
                
                if str(subtree_path) in seen_paths or not subtree_path.exists():
                    continue
                seen_paths.add(str(subtree_path))
                
                url_match = re.search(r'git-subtree-url: ([^\n]+)', message)
                url = url_match.group(1).strip() if url_match else None
                
                subtrees.append(Subtree(
                    name=subtree_path.name,
                    path=subtree_path,
                    url=url,
                    prefix=subtree_path_str
                ))
            
            return subtrees
            
        except Exception:
            return []
    
    def get_submodule_status(self, submodule: Submodule) -> Tuple[str, str]:
        """Get status of a submodule."""
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
            
        except Exception as e:
            return "error", str(e)
    
    def get_subtree_status(self, subtree: Subtree) -> Tuple[str, str]:
        """Get status of a subtree directory."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", subtree.prefix or str(subtree.path)],
                cwd=self.gitdir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return "error", result.stderr.strip()
            
            lines = [line for line in result.stdout.strip().split("\n") if line]
            
            if not lines:
                return "clean", "no changes"
            
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
            
        except Exception as e:
            return "error", str(e)
    
    def subtree_pull(self, subtree: Subtree, squash: bool = True, dry_run: bool = False) -> Tuple[bool, str]:
        """Pull updates from remote for a subtree."""
        if not subtree.url or not subtree.prefix:
            return False, "Subtree missing URL or prefix"
        
        if dry_run:
            return True, f"Would pull from {subtree.url} into {subtree.prefix}"
        
        try:
            cmd = ["git", "subtree", "pull"]
            if squash:
                cmd.append("--squash")
            cmd.extend(["--prefix", subtree.prefix, subtree.url, "main"])
            
            result = subprocess.run(cmd, cwd=self.gitdir, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                return True, f"Pulled updates for {subtree.name}"
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, str(e)
    
    def subtree_push(self, subtree: Subtree, dry_run: bool = False) -> Tuple[bool, str]:
        """Push local changes to remote for a subtree."""
        if not subtree.url or not subtree.prefix:
            return False, "Subtree missing URL or prefix"
        
        if dry_run:
            return True, f"Would push {subtree.prefix} to {subtree.url}"
        
        try:
            result = subprocess.run(
                ["git", "subtree", "push", "--prefix", subtree.prefix, subtree.url, "main"],
                cwd=self.gitdir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return True, f"Pushed changes for {subtree.name}"
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, str(e)
    
    def process_subtree(self, subtree: Subtree, operation: str, dry_run: bool = False) -> dict:
        """Process a single subtree."""
        result = {"name": subtree.name, "path": str(subtree.path), "operation": operation, "type": "subtree", "steps": []}
        
        if operation == "status":
            status, details = self.get_subtree_status(subtree)
            result["status"] = status
            result["details"] = details
            self.formatter.submodule_status(subtree.name, status, details)
            return result
        
        if operation == "pull":
            success, msg = self.subtree_pull(subtree, squash=True, dry_run=dry_run)
            result["steps"].append({"action": "pull", "success": success, "message": msg})
            self.formatter.git_operation(subtree.name, "pull", msg if success else f"failed: {msg}")
            result["success"] = success
            return result
        
        if operation == "push":
            success, msg = self.subtree_push(subtree, dry_run=dry_run)
            result["steps"].append({"action": "push", "success": success, "message": msg})
            self.formatter.git_operation(subtree.name, "push", msg if success else f"failed: {msg}")
            result["success"] = success
            return result
        
        result["success"] = all(step.get("success", True) for step in result["steps"])
        return result
    
    def has_changes(self, submodule: Submodule) -> bool:
        """Check if submodule has uncommitted changes."""
        status, _ = self.get_submodule_status(submodule)
        return status == "modified"
    
    def git_add(self, submodule: Submodule, dry_run: bool = False) -> Tuple[bool, str]:
        """Run git add . in submodule."""
        if dry_run:
            return True, "Would add all files"
        
        try:
            result = subprocess.run(["git", "add", "."], cwd=submodule.path, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, "Added all files"
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, str(e)
    
    def git_commit(self, submodule: Submodule, message: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Run git commit in submodule."""
        if dry_run:
            return True, f"Would commit with message: {message}"
        
        try:
            result = subprocess.run(["git", "commit", "-m", message], cwd=submodule.path, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return True, "Committed successfully"
            elif "nothing to commit" in result.stdout.lower():
                return True, "Nothing to commit"
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, str(e)
    
    def git_push(self, submodule: Submodule, dry_run: bool = False) -> Tuple[bool, str]:
        """Run git push in submodule."""
        if dry_run:
            return True, "Would push to remote"
        
        try:
            result = subprocess.run(["git", "push"], cwd=submodule.path, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                return True, "Pushed successfully"
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, str(e)
    
    def process_submodule(self, submodule: Submodule, operation: str, message: str = "", push: bool = False, dry_run: bool = False) -> dict:
        """Process a single submodule."""
        result = {"name": submodule.name, "path": str(submodule.path), "operation": operation, "type": "submodule", "steps": []}
        
        if operation == "status":
            status, details = self.get_submodule_status(submodule)
            result["status"] = status
            result["details"] = details
            self.formatter.submodule_status(submodule.name, status, details)
            return result
        
        if operation != "full" and not self.has_changes(submodule):
            result["skipped"] = True
            result["reason"] = "no changes"
            self.formatter.submodule_status(submodule.name, "clean", "skipped - no changes")
            return result
        
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
@click.option("-M", "--directory", "gitdir", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path), help="Git directory")
@click.option("-m", "--message", default="Update submodules", help="Commit message")
@click.option("-c", "--config", type=click.Path(exists=True, dir_okay=False, path_type=Path), help="Config file path")
@click.option("-f", "--format", "output_format", type=click.Choice(["color", "plain", "json", "silent"], case_sensitive=False), default=None, help="Output format")
@click.option("-n", "--dry-run", is_flag=True, help="Show what would be done")
@click.option("--push", is_flag=True, help="Push after commit")
@click.option("-o", "--operation", type=click.Choice(["status", "add", "commit", "push", "full", "pull"], case_sensitive=False), default="full", help="Operation")
@click.option("--submodules", multiple=True, help="Specific submodules to process")
@click.option("--subtrees", is_flag=True, help="Enable subtree mode")
@click.option("--detect-subtrees", is_flag=True, help="Detect and list all subtrees in the repository")
@click.option("-j", "--jobs", type=int, default=4, help="Parallel workers")
@click.version_option(version="1.0.0", prog_name="gmd-commit")
def main(gitdir: Optional[Path], message: str, config: Optional[Path], output_format: Optional[str],
         dry_run: bool, push: bool, operation: str, submodules: Tuple[str, ...], subtrees: bool, 
         detect_subtrees: bool, jobs: int):
    """GMD Commit - Batch commit tool for git submodules and subtrees."""
    config_loader = ConfigLoader()
    cfg = config_loader.load(config, gitdir)
    
    if gitdir:
        cfg.gitdir = gitdir
    if output_format:
        cfg.output.format = OutputFormat(output_format.lower())
    
    if not cfg.gitdir:
        click.echo("Error: Git directory required. Use -M/--directory or config file.", err=True)
        sys.exit(1)
    
    formatter = OutputFormatter(cfg.output.format)
    manager = GitSubmoduleManager(cfg.gitdir, formatter)
    
    # Handle detect-subtrees flag (just list and exit)
    if detect_subtrees:
        subtrees_list = manager.detect_subtrees()
        if subtrees_list:
            formatter.info(f"Found {len(subtrees_list)} subtree(s):")
            for subtree in subtrees_list:
                click.echo(f"  - {subtree.name}: {subtree.prefix} ({subtree.url or 'no URL'})")
        else:
            formatter.info("No subtrees found")
        sys.exit(0)
    
    # Determine mode and select items to process
    if subtrees:
        # Subtree mode
        selected = manager.detect_subtrees()
        item_type = "subtree"
        formatter.info(f"Found {len(selected)} subtree(s)")
    else:
        # Submodule mode
        if submodules:
            detected = manager.detect_submodules()
            selected = [s for s in detected if s.name in submodules]
        else:
            selected = manager.detect_submodules()
        item_type = "submodule"
        formatter.info(f"Found {len(selected)} submodule(s)")
    
    if not selected:
        formatter.warning(f"No {item_type}s found")
        sys.exit(0)
    
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as executor:
        if subtrees:
            # Process subtrees
            futures = {executor.submit(manager.process_subtree, subtree, operation, dry_run): subtree for subtree in selected}
        else:
            # Process submodules
            futures = {executor.submit(manager.process_submodule, submodule, operation, message, push, dry_run): submodule for submodule in selected}
        
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                formatter.error(f"Error processing {item.name}: {e}")
                results.append({"name": item.name, "error": str(e), "type": item_type})
    
    # Summary
    successful = sum(1 for r in results if r.get("success", False))
    skipped = sum(1 for r in results if r.get("skipped", False))
    failed = len(results) - successful - skipped
    
    formatter.summary(total=len(results), successful=successful, failed=failed, skipped=skipped)
    
    if failed > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
