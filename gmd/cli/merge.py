#!/usr/bin/env python3
"""
GMD Merge CLI - Directory synchronization tool.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from gmd.config.loader import ConfigLoader
from gmd.config.schema import (
    GMDConfig,
    OutputFormat,
    SyncDirection,
    SyncMode,
)
from gmd.core.scanner import DirectoryScanner
from gmd.core.comparator import FileComparator, FileStatus
from gmd.core.merger import DirectoryMerger
from gmd.core.backup import BackupManager
from gmd.output.formatter import OutputFormatter
from gmd.utils.interactive import InteractiveMode
from gmd.utils.progress import ProgressManager


@click.command()
@click.option(
    "-M", "--master",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Master directory (source)"
)
@click.option(
    "-S", "--slave",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Slave directory (destination)"
)
@click.option(
    "-c", "--config",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Configuration file path"
)
@click.option(
    "-a", "--action",
    type=click.Choice(["preview", "sync", "diff", "backup"], case_sensitive=False),
    default="preview",
    help="Action to perform"
)
@click.option(
    "-f", "--format",
    "output_format",
    type=click.Choice(["color", "plain", "json", "silent"], case_sensitive=False),
    default=None,
    help="Output format"
)
@click.option(
    "-i", "--interactive",
    is_flag=True,
    help="Interactive mode (confirm each file)"
)
@click.option(
    "-b", "--backup",
    is_flag=True,
    help="Create backup before changes"
)
@click.option(
    "-n", "--dry-run",
    is_flag=True,
    help="Show what would be done without making changes"
)
@click.option(
    "-r", "--reverse",
    is_flag=True,
    help="Reverse direction (slave to master)"
)
@click.option(
    "-e", "--excludes",
    multiple=True,
    help="Exclude patterns (can be specified multiple times)"
)
@click.option(
    "-p", "--progress/--no-progress",
    default=None,
    help="Show/hide progress bars"
)
@click.option(
    "-y", "--yes",
    is_flag=True,
    help="Yes to all (skip confirmations)"
)
@click.option(
    "--categories",
    default="missing,update",
    help="Categories to process: missing,update,exists,extra (comma-separated)"
)
@click.version_option(version="1.0.0", prog_name="gmd-merge")
def main(
    master: Optional[Path],
    slave: Optional[Path],
    config: Optional[Path],
    action: str,
    output_format: Optional[str],
    interactive: bool,
    backup: bool,
    dry_run: bool,
    reverse: bool,
    excludes: tuple,
    progress: Optional[bool],
    yes: bool,
    categories: str,
) -> int:
    """
    GMD Merge - Directory synchronization tool.
    
    Synchronize files between two directories with support for
    preview, sync, diff, and backup operations.
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
    if master:
        cli_args["master"] = master
    if slave:
        cli_args["slave"] = slave
    if output_format:
        cli_args["output"] = {"format": OutputFormat(output_format)}
    if progress is not None:
        cli_args.setdefault("output", {})["progress"] = progress
    if excludes:
        cli_args.setdefault("merge", {})["excludes"] = list(excludes)
    if yes:
        cli_args.setdefault("merge", {})["mode"] = SyncMode.AUTO
    
    # Apply CLI overrides
    if cli_args:
        config_obj = loader.merge_with_cli(cli_args)
    
    # Validate required paths
    if not config_obj.master or not config_obj.slave:
        click.echo("Error: --master and --slave are required (or set in config file)", err=True)
        click.echo("\nUsage: gmd-merge -M /path/to/master -S /path/to/slave [options]")
        click.echo("       gmd-merge --config /path/to/config.yaml")
        return 1
    
    # Setup output formatter
    formatter = OutputFormatter(config_obj.output)
    
    # Display header
    formatter.header("GMD Merge v1.0.0")
    formatter.info(f"Master: {config_obj.master}")
    formatter.info(f"Slave: {config_obj.slave}")
    formatter.info(f"Action: {action}")
    
    # Determine direction
    direction = SyncDirection.SLAVE_TO_MASTER if reverse else config_obj.merge.direction
    
    # Parse categories
    category_map = {
        "missing": FileStatus.MISSING,
        "update": FileStatus.UPDATE,
        "exists": FileStatus.EXISTS,
        "extra": FileStatus.EXTRA,
    }
    selected_categories = []
    for cat in categories.lower().split(","):
        cat = cat.strip()
        if cat in category_map:
            selected_categories.append(category_map[cat])
    
    # Create scanner
    scanner = DirectoryScanner(
        excludes=config_obj.merge.excludes,
        progress_callback=None if not config_obj.output.progress else lambda c, p: None
    )
    
    # Scan directories
    formatter.info("Scanning directories...")
    
    with ProgressManager(description="Scanning", total=None) as scan_progress:
        def scan_callback(count: int, path: str) -> None:
            if path == "complete":
                scan_progress.set_total(count)
                scan_progress.update(advance=count)
            else:
                scan_progress.update(advance=1)
        
        scanner.progress_callback = scan_callback if config_obj.output.progress else None
        master_scan, slave_scan = scanner.scan_pair(config_obj.master, config_obj.slave)
    
    formatter.success(f"Found {len(master_scan.files)} files in master")
    formatter.success(f"Found {len(slave_scan.files)} files in slave")
    
    # Compare directories
    formatter.info("Comparing files...")
    
    comparator = FileComparator(
        progress_callback=lambda c, t, p: None,
        use_quick_compare=True
    )
    
    with ProgressManager(description="Comparing", total=len(master_scan.files)) as compare_progress:
        def compare_callback(current: int, total: int, path: str) -> None:
            compare_progress.set_total(total)
            compare_progress.update(advance=1)
        
        comparator.progress_callback = compare_callback if config_obj.output.progress else None
        comparison_result = comparator.compare_directories(
            master_scan, 
            slave_scan,
            categories=[FileStatus.MISSING, FileStatus.UPDATE, FileStatus.EXTRA]
        )
    
    stats = comparison_result.get_stats()
    formatter.stats(
        missing=stats["missing"],
        update=stats["update"],
        exists=stats["exists"],
        extra=stats["extra"]
    )
    
    # Execute action
    if action == "preview":
        return _action_preview(formatter, comparison_result, selected_categories)
    
    elif action == "diff":
        return _action_diff(formatter, comparison_result, comparator, selected_categories)
    
    elif action == "backup":
        return _action_backup(formatter, config_obj, comparison_result)
    
    elif action == "sync":
        return _action_sync(
            formatter,
            config_obj,
            comparison_result,
            selected_categories,
            direction,
            interactive,
            backup or config_obj.backup.enabled,
            dry_run,
            yes
        )
    
    return 0


def _action_preview(
    formatter: OutputFormatter,
    comparison_result,
    categories: list
) -> int:
    """Preview action - show what would change."""
    formatter.header("Preview")
    
    if FileStatus.MISSING in categories:
        for comp in comparison_result.missing:
            formatter.file_missing(str(comp.source_path), str(comp.dest_path))
    
    if FileStatus.UPDATE in categories:
        for comp in comparison_result.update:
            formatter.file_update(str(comp.source_path), str(comp.dest_path))
    
    if FileStatus.EXTRA in categories:
        for comp in comparison_result.extra:
            formatter.file_missing(str(comp.slave_entry.path), "extra file")
    
    formatter.footer()
    return 0


def _action_diff(
    formatter: OutputFormatter,
    comparison_result,
    comparator: FileComparator,
    categories: list
) -> int:
    """Diff action - show differences."""
    formatter.header("Differences")
    
    if FileStatus.UPDATE not in categories:
        formatter.info("No updates to diff.")
        return 0
    
    for comp in comparison_result.update:
        diff_content = comparator.generate_diff(comp)
        if diff_content:
            formatter.show_diff(
                str(comp.master_entry.path),
                str(comp.slave_entry.path),
                diff_content
            )
    
    formatter.footer()
    return 0


def _action_backup(
    formatter: OutputFormatter,
    config_obj: GMDConfig,
    comparison_result
) -> int:
    """Backup action - create backup of files that would change."""
    formatter.header("Backup")
    
    backup_mgr = BackupManager(config_obj.backup)
    
    # Collect files to backup
    files_to_backup = []
    for comp in comparison_result.update:
        if comp.slave_entry:
            files_to_backup.append(comp.slave_entry.path)
    
    if not files_to_backup:
        formatter.info("No files need backup.")
        return 0
    
    formatter.info(f"Creating backup of {len(files_to_backup)} files...")
    
    entry = backup_mgr.create_backup(
        config_obj.slave,
        specific_files=files_to_backup
    )
    
    if entry:
        formatter.success(f"Backup created: {entry.backup_path}")
        formatter.info(f"Size: {entry.size_bytes} bytes")
    else:
        formatter.error("Backup failed!")
        return 1
    
    formatter.footer()
    return 0


def _action_sync(
    formatter: OutputFormatter,
    config_obj: GMDConfig,
    comparison_result,
    categories: list,
    direction: SyncDirection,
    interactive: bool,
    backup_enabled: bool,
    dry_run: bool,
    yes_to_all: bool
) -> int:
    """Sync action - perform synchronization."""
    formatter.header("Synchronization")
    
    # Collect files to process
    files_to_process = []
    if FileStatus.MISSING in categories:
        files_to_process.extend(comparison_result.missing)
    if FileStatus.UPDATE in categories:
        files_to_process.extend(comparison_result.update)
    
    if not files_to_process:
        formatter.info("No files to synchronize.")
        return 0
    
    # Create backup if enabled
    if backup_enabled and not dry_run:
        backup_mgr = BackupManager(config_obj.backup)
        files_to_backup = [comp.slave_entry.path for comp in files_to_process if comp.slave_entry]
        
        if files_to_backup:
            formatter.info("Creating backup...")
            entry = backup_mgr.create_backup(
                config_obj.slave,
                specific_files=files_to_backup
            )
            if entry:
                formatter.success(f"Backup: {entry.backup_path}")
    
    # Interactive mode
    if interactive and not yes_to_all and not dry_run:
        interactive_mode = InteractiveMode(formatter)
        
        approved = []
        
        def on_approve(comp):
            approved.append(comp)
        
        result = interactive_mode.process_files(
            files_to_process,
            on_approve=on_approve
        )
        
        files_to_process = approved
        
        formatter.stats(
            missing=0,
            update=0,
            exists=0,
            copied=result["approved"],
            failed=result["rejected"]
        )
    
    elif not yes_to_all and not dry_run:
        # Simple confirmation
        if not click.confirm(f"Sync {len(files_to_process)} files?"):
            formatter.info("Cancelled.")
            return 0
    
    # Perform merge
    merger = DirectoryMerger(
        direction=direction,
        verify=True,
        progress_callback=lambda c, t, p: None
    )
    
    with ProgressManager(description="Syncing", total=len(files_to_process)) as sync_progress:
        def merge_callback(current: int, total: int, path: str) -> None:
            sync_progress.set_total(total)
            sync_progress.update(advance=1)
        
        merger.progress_callback = merge_callback if config_obj.output.progress else None
        report = merger.merge_all(comparison_result, categories=categories, dry_run=dry_run)
    
    # Report results
    stats = report.get_stats()
    formatter.stats(
        missing=0,
        update=0,
        exists=0,
        copied=stats["success"],
        failed=stats["failed"]
    )
    
    if dry_run:
        formatter.info("(Dry run - no changes made)")
    
    formatter.footer()
    
    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
