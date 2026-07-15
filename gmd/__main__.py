"""
GMD package entry point.
Allows running as: python -m gmd
"""

import sys
from gmd.cli.merge import main as merge_main


def main():
    """Default to merge command."""
    return merge_main()


if __name__ == "__main__":
    sys.exit(main())
