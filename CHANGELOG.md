# Changelog

All notable changes to the GMD (Git Merge Directories) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### GUI Application (New!)
- **gmd-gui**: Full graphical user interface for directory synchronization
  - Split-pane directory view with resizable panels
  - Visual comparison with color coding (green=same, yellow=different, red=missing, blue=extra)
  - Unicode icons for file types and actions (📁 📄 ⚠ ➕ ✓ 🔄 💾)
  - Automatic scan and compare on directory selection
  - Progress bar with elapsed time tracking
  - Status bar showing file counts and operation status
  - Context menus for opening files in system file manager
  - Direction selector (Source→Dest, Dest→Source, Bidirectional)
  - Exclude patterns entry with visual feedback
  - Preview, Sync, Diff, Backup, and Cancel action buttons
  - Application icon with gradient design
- **GUI Documentation**: Complete usage guide in `docs/GUI_USAGE.md`
- **GUI Tests**: Integration tests verifying core module compatibility
- **GUI Entry Point**: `gmd-gui` command available after installation

### Changed

- **setup.py**: Added `gmd-gui` console script entry point
- **setup.py**: Added optional `[gui]` extras_require for Pillow dependency
- **README.md**: Updated to include gmd-gui features and quick start

### Fixed

- N/A

## [1.0.0] - 2024-01-XX

### Added

- **gmd-merge**: Command-line directory synchronization tool
  - Multiple actions: preview, sync, diff, backup
  - Sync directions: master→slave, slave→master, bidirectional
  - File categories: missing, updated, existing, extra
  - Interactive mode with file-by-file approval
  - Backup support with retention policy
  - Progress bars for large directories
  - Multiple output formats: color, plain, JSON, silent
  - Exclude patterns with glob/regex support
  - Dry run mode
  - SHA256 verification

- **gmd-commit**: Git submodule batch commit tool
  - Auto-detection from `.gitmodules`
  - Batch operations: status, add, commit, push
  - Smart processing of changed submodules only
  - Parallel execution with configurable workers
  - Dry run mode

- **Configuration System**
  - JSON and YAML config file support
  - Auto-detection of config files (.gmdrc, gmd.config.*)
  - Schema validation with pydantic

- **Core Modules**
  - DirectoryScanner: Fast directory scanning with metadata
  - FileComparator: SHA256 and quick comparison modes
  - DirectoryMerger: Safe file synchronization with verification
  - BackupManager: Automated backup with rotation
  - GitSubmoduleManager: Submodule operations

- **Documentation**
  - README with installation and usage instructions
  - CLI reference documentation
  - Configuration examples

### Security

- SHA256 verification for file integrity
- Backup before changes option
- Dry run mode for safe preview

[Unreleased]: https://github.com/w4d4f4k/gmd/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/w4d4f4k/gmd/releases/tag/v1.0.0
