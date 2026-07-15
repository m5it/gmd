"""
GMD GUI Module - Tkinter-based graphical interface for directory synchronization.

This module provides a graphical user interface for the GMD (Git Merge Directories)
suite, allowing users to compare, synchronize, and manage directories through
an intuitive visual interface.

Example:
    Launch the GUI from command line:
        $ gmd-gui
    
    Or from Python:
        >>> from gmd.gui import main
        >>> main()
"""

from gmd.gui.main import GMDGuiApp, main

__all__ = ["GMDGuiApp", "main", "launch_gui"]


def launch_gui():
    """
    Convenience function to launch the GMD GUI.
    
    This is an alias for main() that provides a more descriptive name.
    """
    return main()


# Version info
__version__ = "1.0.0"
