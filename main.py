#!/usr/bin/env python3
"""
GMD launcher - run GMD tools directly from the repository without pip install.

Usage:
    python main.py gmd-merge -M /path/to/master -S /path/to/slave
    python main.py gmd-commit -M /path/to/repo -m "message"
    python main.py gmd-gui
    python main.py --help
    python main.py -v
    python main.py --version
"""

import sys
from typing import List


__version__ = "1.0.1"


# Map official command names to their launcher prog_name.
_COMMAND_NAMES = {
    "gmd-merge": "gmd-merge",
    "merge": "gmd-merge",
    "gmd-commit": "gmd-commit",
    "commit": "gmd-commit",
    "gmd-gui": "gmd-gui",
    "gui": "gmd-gui",
}


def _show_version() -> int:
    """Display launcher version."""
    print(f"GMD launcher {__version__}")
    return 0


def _show_help() -> int:
    """Display launcher help and available commands."""
    print(f"GMD v{__version__} - Git Merge Directories Suite")
    print()
    print("Usage: python main.py <command> [options]")
    print()
    print("Commands:")
    print("  gmd-merge   Directory synchronization tool")
    print("  gmd-commit  Batch commit tool for git submodules/subtrees")
    print("  gmd-gui     Graphical user interface")
    print()
    print("Aliases: merge, commit, gui")
    print()
    print("Global options:")
    print("  -h, --help     Show this help message and exit")
    print("  -v, --version  Show launcher version and exit")
    print()
    print("Run 'python main.py <command> --help' for command options.")
    return 0


def _missing_deps(exc: ImportError) -> None:
    """Print a friendly message when a required dependency is missing."""
    print(f"Error: missing required dependency ({exc.name}).", file=sys.stderr)
    print("Install GMD dependencies with:", file=sys.stderr)
    print("    pip install -r requirements.txt", file=sys.stderr)
    print("Or for a minimal install:", file=sys.stderr)
    print("    pip install rich pydantic PyYAML click", file=sys.stderr)


def _run_with_prog_name(target, args: List[str], prog_name: str, accepts_args: bool = True) -> int:
    """Run a target while showing the correct tool name in help text."""
    original_argv0 = sys.argv[0]
    sys.argv[0] = prog_name
    try:
        if accepts_args:
            return target(args)
        return target()
    finally:
        sys.argv[0] = original_argv0


def run_merge(args: List[str]) -> int:
    """Launch gmd-merge CLI."""
    try:
        from gmd.cli.merge import main as merge_main
    except ImportError as exc:
        _missing_deps(exc)
        return 1
    return _run_with_prog_name(merge_main, args, "gmd-merge")


def run_commit(args: List[str]) -> int:
    """Launch gmd-commit CLI."""
    try:
        from gmd.cli.commit import main as commit_main
    except ImportError as exc:
        _missing_deps(exc)
        return 1
    return _run_with_prog_name(commit_main, args, "gmd-commit")


def run_gui(args: List[str]) -> int:
    """Launch gmd-gui."""
    try:
        from gmd.gui.main import main as gui_main
    except ImportError as exc:
        _missing_deps(exc)
        return 1
    return _run_with_prog_name(gui_main, args, "gmd-gui", accepts_args=False)


def main() -> int:
    """Route to the requested GMD command."""
    if len(sys.argv) < 2:
        print("Error: no command provided.", file=sys.stderr)
        print("Run 'python main.py --help' for usage.", file=sys.stderr)
        return 1

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    if command in ("-h", "--help", "help"):
        return _show_help()

    if command in ("-v", "--version", "version"):
        return _show_version()

    commands = {
        "gmd-merge": run_merge,
        "merge": run_merge,
        "gmd-commit": run_commit,
        "commit": run_commit,
        "gmd-gui": run_gui,
        "gui": run_gui,
    }

    if command not in commands:
        print(f"Error: unknown command '{sys.argv[1]}'", file=sys.stderr)
        print("Run 'python main.py --help' for available commands.", file=sys.stderr)
        return 1

    return commands[command](args)


if __name__ == "__main__":
    sys.exit(main())
