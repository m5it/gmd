# GMD GUI Usage Guide

## Overview

The GMD GUI provides a graphical interface for directory synchronization using the GMD (Git Merge Directories) suite. It allows you to visually compare, synchronize, and manage directories with an intuitive drag-and-drop interface.

## Launching the GUI

### From Command Line

```bash
# If installed via pip
gmd-gui

# Or directly from source
python -m gmd.gui.main

# Or using the script
python scripts/gmd-gui
```

### From Python

```python
from gmd.gui import main
main()

# Or
from gmd.gui import GMDGuiApp
app = GMDGuiApp()
app.run()
```

## Main Interface

The GUI is divided into several sections:

### 1. Directory Panels (Top)
- **Left Panel**: Source directory tree
- **Right Panel**: Destination directory tree
- Both panels show file names, sizes, modification dates, and sync status

### 2. Action Panel (Middle)
- **Direction Selector**: Choose sync direction
  - Source → Destination
  - Destination → Source
  - Bidirectional
- **Exclude Patterns**: Comma-separated patterns to exclude (*.tmp, .git/, etc)
- **Action Buttons**:
  - 👁 Preview: Show pending changes
  - 🔄 Synchronize: Execute sync operation
  - 📊 Show Diff: View file differences
  - 💾 Backup: Create backup of destination
  - ⏹ Cancel: Stop current operation

### 3. Status Bar (Bottom)
- Current operation status
- File counts (total, same, different, missing)
- Elapsed time
- Progress bar

## Color Coding

Files are color-coded based on comparison results:

- **Green**: Files are identical (same)
- **Yellow**: Files differ (different/update)
- **Red**: File missing in destination (missing)
- **Blue**: Extra files in destination (extra)

## Context Menus

Right-click on any file or folder to:
- Open in system file manager
- Refresh directory view

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+O | Open Source Directory |
| Ctrl+D | Open Destination Directory |
| F5 | Refresh/Scan |
| Escape | Cancel Operation |

## Workflow

1. **Select Directories**: Click "Open Source Directory" and "Open Destination Directory"
2. **Scan**: The GUI automatically scans both directories
3. **Review**: Check the color-coded comparison results
4. **Preview**: Click Preview to see pending changes
5. **Configure**: Set direction and exclude patterns if needed
6. **Sync**: Click Synchronize to execute

## Menu Options

### File Menu
- Open Source Directory
- Open Destination Directory
- Exit

### Commands Menu
- Scan Directories
- Compare
- Preview Changes
- Synchronize
- Show Diff
- Backup Destination

### Help Menu
- Documentation
- About

## Tips

- Use exclude patterns to skip temporary files (*.tmp, .log, etc)
- Always preview changes before synchronizing
- Create backups before major sync operations
- The GUI automatically rescans after sync completion

## Troubleshooting

### GUI Won't Start
- Ensure tkinter is installed: `python -m tkinter`
- Check Python version (3.8+ required)

### Slow Performance
- Large directories may take time to scan
- Use exclude patterns to skip unnecessary files
- Consider using CLI for very large operations

### Permission Errors
- Ensure read/write access to both directories
- Run with appropriate permissions if needed

## See Also

- [CLI Documentation](CLI.md) - Command-line interface
- [Configuration](CONFIG.md) - Configuration file options
- [Core Modules](CORE.md) - Core module documentation
