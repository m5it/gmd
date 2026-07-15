"""
GMD v1.0.0 - Git Merge Directories Suite

A Python-based directory synchronization and git submodule management tool.

Modules:
    core: Directory scanning, comparison, merging, and backup
    cli: Command-line interfaces for merge and commit operations
    config: Configuration loading and validation
    output: Output formatting (color, plain, JSON)
    utils: Utility functions and helpers
"""

__version__ = "1.0.0"
__author__ = "w4d4f4k"
__email__ = "w4d4f4k@gmail.com"

from gmd.config.schema import GMDConfig

__all__ = ["GMDConfig", "__version__"]
