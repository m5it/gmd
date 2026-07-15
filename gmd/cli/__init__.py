"""
CLI modules for gmd-merge and gmd-commit commands.
"""

from gmd.cli.merge import main as merge_main
from gmd.cli.commit import main as commit_main

__all__ = ["merge_main", "commit_main"]
