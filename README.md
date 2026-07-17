# GMD v1.0.0 - Git Merge Directories

A Python-based suite for directory synchronization and git submodule management.

## Overview

GMD (Git Merge Directories) provides three complementary tools:

- **gmd-merge**: Command-line tool for synchronizing files between directories
- **gmd-commit**: Batch commit changes across git submodules
- **gmd-gui**: Graphical user interface for visual directory comparison and sync

## Features

### gmd-merge
- **Multiple Actions**: preview, sync, diff, backup
- **Sync Directions**: master→slave, slave→master, bidirectional
- **File Categories**: Track missing, updated, existing, and extra files
- **Interactive Mode**: File-by-file approval with diff preview
- **Backup Support**: Automatic backup before changes with retention policy
- **Progress Bars**: Real-time progress for large directories
- **Multiple Formats**: color, plain, JSON, silent output
- **Exclude Patterns**: Glob/regex pattern support
- **Dry Run**: Preview changes without making them
- **SHA256 Verification**: Verify file integrity after copy

### gmd-commit
- **Auto-Detection**: Automatically find submodules from `.gitmodules`
- **Batch Operations**: status, add, commit, push, full
- **Smart Processing**: Only process changed submodules
- **Parallel Execution**: Process multiple submodules concurrently
### gmd-commit
- **Auto-Detection**: Automatically find submodules from `.gitmodules` or subtrees from git log
- **Batch Operations**: status, add, commit, push, full (for submodules); status, pull, push (for subtrees)
- **Smart Processing**: Only process changed submodules/subtrees
- **Parallel Execution**: Process multiple items concurrently
- **Dry Run**: Preview operations without executing
- **Subtree Support**: Manage git subtrees alongside submodules
- **Exclude Patterns**: Easy pattern entry with visual feedback

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/w4d4f4k/gmd.git
cd gmd

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Or install for production
pip install .
```

### Dependencies

- Python 3.8+
- rich >= 13.0.0 (terminal formatting)
- pydantic >= 2.0.0 (config validation)
- PyYAML >= 6.0 (YAML config support)
- click >= 8.0.0 (CLI framework)
- tkinter (usually included with Python, required for GUI)

### Optional GUI Dependencies

```bash
# For enhanced icon support in GUI
pip install "gmd-tools[gui]"
```

## Quick Start

### gmd-merge

```bash
# Preview differences between directories
gmd-merge -M /path/to/master -S /path/to/slave

# Synchronize with backup
gmd-merge -M /path/to/master -S /path/to/slave --action sync --backup

# Interactive mode with diff preview
gmd-merge -M /path/to/master -S /path/to/slave -i

# Show differences
gmd-merge -M /path/to/master -S /path/to/slave --action diff
# Parallel processing with 8 workers
gmd-commit -M /path/to/repo -j 8
```

### Subtree Support (New!)

gmd-commit now supports **git subtrees** in addition to submodules. Subtrees are an alternative to submodules where external repositories are merged into subdirectories with full history preserved.

**What's the difference?**

| Feature | Submodules | Subtrees |
|---------|-----------|----------|
| Repository | Separate repo, linked | Merged into main repo |
| History | Separate | Combined in main repo |
| Cloning | Requires `git submodule update` | Works with regular clone |
| Management | `.gitmodules` file | `git subtree` commands |

**Subtree Commands:**

```bash
# Detect all subtrees in the repository
gmd-commit -M /path/to/repo --detect-subtrees

# Check status of subtrees
gmd-commit -M /path/to/repo --subtrees --operation status

# Pull updates from remote for all subtrees
gmd-commit -M /path/to/repo --subtrees --operation pull

# Push local subtree changes to remote
gmd-commit -M /path/to/repo --subtrees --operation push

# Dry run to see what would be pulled/pushed
gmd-commit -M /path/to/repo --subtrees --operation pull --dry-run
```

### gmd-gui
gmd-commit -M /path/to/repo -m "Update dependencies"

# Full workflow: add, commit, and push
gmd-commit -M /path/to/repo -m "Update dependencies" --push

# Dry run to see what would be committed
gmd-commit -M /path/to/repo -m "Update" --dry-run

# Process specific submodules
gmd-commit -M /path/to/repo --submodules module1 --submodules module2

# Parallel processing with 8 workers
gmd-commit -M /path/to/repo -j 8
```

### gmd-gui

```bash
# Launch the GUI
gmd-gui

# Or from Python
python -m gmd.gui.main
```

The GUI provides a visual interface for:
- Selecting source and destination directories
- Viewing side-by-side comparison with color coding
- Previewing changes before synchronization
- Configuring sync direction and exclude patterns
- Creating backups with one click

## Configuration Files

### Creating a Config File

```bash
# Create example config (JSON)
gmd-merge --create-config ./myconfig.json

# Create example config (YAML)
gmd-merge --create-config ./myconfig.yaml
```

### Merge Config Example (JSON)

```json
{
  "master": "/home/user/project-master",
  "slave": "/home/user/project-slave",
  "output": {
    "format": "color",
    "progress": true,
    "report": "./gmd-report.json"
  },
  "backup": {
    "enabled": true,
    "directory": "./backups",
    "keep": 10
  },
  "merge": {
    "direction": "master-to-slave",
    "mode": "interactive",
    "categories": ["missing", "update"],
    "excludes": [
      "*.tmp",
      ".git/",
      "node_modules/",
      "__pycache__/",
      "*.pyc",
      "*.log",
      ".env"
    ],
    "dry_run": false
  }
}
```

### Commit Config Example (YAML)

```yaml
gitdir: /home/user/project-with-submodules

output:
  format: color
  progress: true

commit:
  auto_push: false
  parallel: true
  max_workers: 4
```

### Config File Locations

GMD auto-detects config files in this order:
1. `.gmdrc`
2. `.gmdrc.json`
3. `.gmdrc.yaml`
4. `.gmdrc.yml`
5. `gmd.config.json`
6. `gmd.config.yaml`
7. `gmd.config.yml`

## CLI Reference

### gmd-merge Options

| Option | Short | Description |
|--------|-------|-------------|
| `--master` | `-M` | Master directory (source) |
| `--slave` | `-S` | Slave directory (destination) |
### gmd-commit Options

| Option | Short | Description |
|--------|-------|-------------|
| `--directory` | `-M` | Git directory with submodules/subtrees |
| `--message` | `-m` | Commit message |
| `--config` | `-c` | Configuration file path |
| `--format` | `-f` | Output format: color, plain, json, silent |
| `--dry-run` | `-n` | Preview without making changes |
| `--push` | | Push after commit |
| `--operation` | `-o` | Operation: status, add, commit, push, full (submodule); status, pull, push (subtree) |
| `--submodules` | | Specific submodules to process |
| `--subtrees` | | Enable subtree mode |
| `--detect-subtrees` | | Detect and list all subtrees |
| `--jobs` | `-j` | Number of parallel workers |
| `--directory` | `-M` | Git directory with submodules |
| `--message` | `-m` | Commit message |
| `--config` | `-c` | Configuration file path |
| `--format` | `-f` | Output format: color, plain, json, silent |
| `--dry-run` | `-n` | Preview without making changes |
| `--push` | | Push after commit |
| `--operation` | `-o` | Operation: status, add, commit, push, full |
| `--submodules` | | Specific submodules to process |
| `--jobs` | `-j` | Number of parallel workers |

## Example Workflows

### Workflow 1: Sync Project with Submodules

```bash
# Step 1: Sync main project
gmd-merge -M ./project-master -S ./project-slave --action sync --backup -y

# Step 2: Commit submodule changes
gmd-commit -M ./project-slave -m "Sync from master" --push
```

### Workflow 2: Development to Production

```bash
# Preview changes first
gmd-merge -M ./dev -S ./prod --action preview

# Create backup and sync with interactive approval
gmd-merge -M ./dev -S ./prod --action sync --backup --interactive

# Generate report
gmd-merge -M ./dev -S ./prod --format json --action preview > changes.json
```

### Workflow 3: Submodule Update Pipeline

```bash
# Check which submodules have changes
gmd-commit -M ./myproject --operation status

# Add and commit all changes
gmd-commit -M ./myproject -m "Update submodules" --operation full --push
```

### Workflow 4: Bidirectional Sync

```bash
# Preview bidirectional changes
gmd-merge -M ./folder-a -S ./folder-b --action preview

# Sync newer files in both directions
gmd-merge -M ./folder-a -S ./folder-b --action sync --categories missing,update

# Handle extra files (in slave but not master)
gmd-merge -M ./folder-a -S ./folder-b --action sync --categories extra
```

### Workflow 5: Automated CI/CD

```bash
#!/bin/bash
# ci-sync.sh - Automated sync script

set -e

# Sync with JSON output for parsing
gmd-merge \
  -M "${MASTER_DIR}" \
  -S "${SLAVE_DIR}" \
  --action sync \
  --format json \
  --yes \
  --backup > sync-result.json

# Check for failures
if jq -e '.stats.failed > 0' sync-result.json > /dev/null; then
  echo "Sync failed!"
  exit 1
fi

# Commit submodule changes if any
gmd-commit \
  -M "${SLAVE_DIR}" \
  -m "Auto-sync from CI" \
  --push \
  --yes || true
```

## Output Formats

### Color (default)
Rich terminal output with colors, progress bars, and tables.

### Plain
Text-only output suitable for logging and piping.

### JSON
Machine-readable JSON for scripting and automation.

```json
{
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00",
  "files": [
    {
      "type": "missing",
      "source": "/path/to/file",
      "destination": "/path/to/dest"
    }
  ],
  "stats": {
    "missing": 5,
    "update": 3,
    "exists": 100,
    "total": 108
  }
}
```

### Silent
Errors only, useful for cron jobs.

## Troubleshooting

### Permission Denied
```bash
# Check permissions
ls -la /path/to/directories

# Run with appropriate permissions
sudo gmd-merge ...
```

### Submodule Not Found
```bash
# Initialize submodules first
cd /path/to/repo
git submodule update --init --recursive

# Then run gmd-commit
gmd-commit -M . -m "Update"
```

### Large Directories
For very large directories, use:
```bash
# Disable progress bars for better performance
gmd-merge -M /large/dir -S /dest --no-progress

# Use plain output
gmd-merge -M /large/dir -S /dest --format plain
```

## License

MIT License - See LICENSE file for details.

## Author

w4d4f4k at gmail dot com
