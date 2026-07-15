#!/usr/bin/env python3
"""
GMD GUI Main Application - Tkinter interface for directory merge.
"""

import datetime
import os
import platform
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

from gmd.config.schema import GMDConfig, SyncDirection
from gmd.core.scanner import DirectoryScanner, ScanResult
from gmd.core.comparator import FileComparator, FileStatus, ComparisonResult
from gmd.core.merger import DirectoryMerger


class GMDGuiApp:
    """Main GUI application for GMD Merge."""
    
    def __init__(self):
        """Initialize the GUI application."""
        self.root = tk.Tk()
        self.root.title("GMD Merge - Directory Synchronization")
        self.root.minsize(1200, 700)
        self.root.geometry("1400x800")
        
        # Store current paths
        self.source_path: Path = None
        self.dest_path: Path = None
        
        # Store scan results
        self.source_scan: ScanResult = None
        self.dest_scan: ScanResult = None
        self.comparison: ComparisonResult = None
        
        # Color tags for treeviews
        self.tree_tags = {
            "same": {"background": "#d4edda", "foreground": "#155724"},  # Green
            "different": {"background": "#fff3cd", "foreground": "#856404"},  # Yellow
            "missing": {"background": "#f8d7da", "foreground": "#721c24"},  # Red
            "extra": {"background": "#cce5ff", "foreground": "#004085"},  # Blue
        }
        
        # Icons (using text symbols as icons)
        self.icons = {
            "folder": "📁",
            "file": "📄",
            "modified": "⚠",
            "missing": "➕",
            "same": "✓",
            "extra": "🗑",
            "sync": "🔄",
            "backup": "💾",
            "diff": "📊",
            "preview": "👁",
        }
        
        # Create UI components
        self._create_menu()
        self._create_main_layout()
        self._create_status_bar()
        
        # Configure treeview tags after creation
        self.root.after(100, self._configure_tree_tags)
        
        # Set application icon
        self._set_app_icon()
        
        # Set up window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _set_app_icon(self):
        """Set application icon."""
        try:
            # Try to use a system icon or create a simple one
            self.root.iconbitmap("")  # Clear default
            
            # For Windows/Linux, try to set icon using PhotoImage
            # Create a simple colored square as icon
            icon = tk.PhotoImage(width=64, height=64)
            
            # Fill with a simple pattern (blue gradient effect)
            for x in range(64):
                for y in range(64):
                    # Create a simple blue gradient
                    r = 0
                    g = int(100 + (x / 64) * 100)
                    b = int(200 + (y / 64) * 55)
                    icon.put(f"#{r:02x}{g:02x}{b:02x}", (x, y))
            
            self.root.iconphoto(True, icon)
            self._app_icon = icon  # Keep reference
            
        except Exception:
            # Icon setting is optional
            pass
    
    def _create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Source Directory...", command=self._open_source)
        file_menu.add_command(label="Open Destination Directory...", command=self._open_dest)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        
        # Commands menu
        cmd_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Commands", menu=cmd_menu)
        cmd_menu.add_command(label="Scan Directories", command=self._scan_directories)
        cmd_menu.add_command(label="Compare", command=self._compare_directories)
        cmd_menu.add_separator()
        cmd_menu.add_command(label="Preview Changes", command=self._preview_changes)
        cmd_menu.add_command(label="Synchronize", command=self._synchronize)
        cmd_menu.add_command(label="Show Diff", command=self._show_diff)
        cmd_menu.add_separator()
        cmd_menu.add_command(label="Backup Destination", command=self._backup_dest)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self._show_docs)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_main_layout(self):
        """Create the main horizontal layout."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Top labels row
        ttk.Label(main_frame, text="Source Directory", font=("Helvetica", 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Label(main_frame, text="Destination Directory", font=("Helvetica", 12, "bold")).grid(
            row=0, column=1, sticky="w", padx=5, pady=5
        )
        
        # Paned window for resizable panels
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Left panel (Source)
        self.left_frame = ttk.Frame(paned, relief="sunken", borderwidth=1)
        paned.add(self.left_frame, weight=1)
        
        self.left_label = ttk.Label(self.left_frame, text="No source selected", 
                                    anchor="w", padding="5")
        self.left_label.pack(fill="x")
        
        # Source treeview with scrollbars
        self.left_tree_frame = ttk.Frame(self.left_frame)
        self.left_tree_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        self.left_tree = ttk.Treeview(
            self.left_tree_frame,
            columns=("size", "modified", "status"),
            show="tree headings",
            selectmode="browse"
        )
        self.left_tree.heading("#0", text="Name", anchor="w")
        self.left_tree.heading("size", text="Size", anchor="e")
        self.left_tree.heading("modified", text="Modified", anchor="w")
        self.left_tree.heading("status", text="Status", anchor="w")
        
        self.left_tree.column("#0", width=250, minwidth=150)
        self.left_tree.column("size", width=80, minwidth=60)
        self.left_tree.column("modified", width=120, minwidth=80)
        self.left_tree.column("status", width=80, minwidth=60)
        
        # Scrollbars for source
        left_vsb = ttk.Scrollbar(self.left_tree_frame, orient="vertical", 
                                   command=self.left_tree.yview)
        left_hsb = ttk.Scrollbar(self.left_tree_frame, orient="horizontal", 
                                   command=self.left_tree.xview)
        self.left_tree.configure(yscrollcommand=left_vsb.set, xscrollcommand=left_hsb.set)
        
        self.left_tree.grid(row=0, column=0, sticky="nsew")
        left_vsb.grid(row=0, column=1, sticky="ns")
        left_hsb.grid(row=1, column=0, sticky="ew")
        
        self.left_tree_frame.grid_rowconfigure(0, weight=1)
        self.left_tree_frame.grid_columnconfigure(0, weight=1)
        
        # Right panel (Destination)
        self.right_frame = ttk.Frame(paned, relief="sunken", borderwidth=1)
        paned.add(self.right_frame, weight=1)
        
        self.right_label = ttk.Label(self.right_frame, text="No destination selected", 
                                     anchor="w", padding="5")
        self.right_label.pack(fill="x")
        
        # Destination treeview with scrollbars
        self.right_tree_frame = ttk.Frame(self.right_frame)
        self.right_tree_frame.pack(expand=True, fill="both", padx=5, pady=5)
        
        self.right_tree = ttk.Treeview(
            self.right_tree_frame,
            columns=("size", "modified", "status"),
            show="tree headings",
            selectmode="browse"
        )
        self.right_tree.heading("#0", text="Name", anchor="w")
        self.right_tree.heading("size", text="Size", anchor="e")
        self.right_tree.heading("modified", text="Modified", anchor="w")
        self.right_tree.heading("status", text="Status", anchor="w")
        
        self.right_tree.column("#0", width=250, minwidth=150)
        self.right_tree.column("size", width=80, minwidth=60)
        self.right_tree.column("modified", width=120, minwidth=80)
        self.right_tree.column("status", width=80, minwidth=60)
        
        # Scrollbars for destination
        right_vsb = ttk.Scrollbar(self.right_tree_frame, orient="vertical", 
                                    command=self.right_tree.yview)
        right_hsb = ttk.Scrollbar(self.right_tree_frame, orient="horizontal", 
                                    command=self.right_tree.xview)
        self.right_tree.configure(yscrollcommand=right_vsb.set, xscrollcommand=right_hsb.set)
        
        self.right_tree.grid(row=0, column=0, sticky="nsew")
        right_vsb.grid(row=0, column=1, sticky="ns")
        right_hsb.grid(row=1, column=0, sticky="ew")
        
        self.right_tree_frame.grid_rowconfigure(0, weight=1)
        self.right_tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind right-click context menus
        self._setup_context_menu(self.left_tree, "source")
        self._setup_context_menu(self.right_tree, "destination")
        
        # Bottom control panel
        self._create_control_panel(main_frame)
    
    def _create_control_panel(self, main_frame: ttk.Frame):
        """Create the bottom control panel with action buttons."""
        self.control_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        self.control_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        
        # Configure grid
        self.control_frame.columnconfigure(1, weight=1)  # Excludes entry expands
        
        # Row 0: Direction selector
        ttk.Label(self.control_frame, text="Direction:").grid(row=0, column=0, sticky="w", padx=5)
        
        self.direction_var = tk.StringVar(value="source_to_dest")
        direction_frame = ttk.Frame(self.control_frame)
        direction_frame.grid(row=0, column=1, columnspan=2, sticky="w", padx=5)
        
        ttk.Radiobutton(
            direction_frame, 
            text="Source → Destination",
            variable=self.direction_var,
            value="source_to_dest"
        ).pack(side="left", padx=5)
        
        ttk.Radiobutton(
            direction_frame,
            text="Destination → Source",
            variable=self.direction_var,
            value="dest_to_source"
        ).pack(side="left", padx=5)
        
        ttk.Radiobutton(
            direction_frame,
            text="Bidirectional",
            variable=self.direction_var,
            value="bidirectional"
        ).pack(side="left", padx=5)
        
        # Row 1: Exclude patterns
        ttk.Label(self.control_frame, text="Excludes:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        self.excludes_var = tk.StringVar()
        self.excludes_entry = ttk.Entry(
            self.control_frame,
            textvariable=self.excludes_var,
            width=50
        )
        self.excludes_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Label(
            self.control_frame,
            text="Comma-separated patterns (*.tmp, .git/, etc)",
            foreground="gray"
        ).grid(row=1, column=2, sticky="w", padx=5)
        
        # Row 2: Action buttons with icons
        button_frame = ttk.Frame(self.control_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=10)
        
        self.preview_btn = ttk.Button(
            button_frame,
            text=f"{self.icons['preview']} Preview",
            command=self._preview_changes
        )
        self.preview_btn.pack(side="left", padx=5)
        
        self.sync_btn = ttk.Button(
            button_frame,
            text=f"{self.icons['sync']} Synchronize",
            command=self._synchronize
        )
        self.sync_btn.pack(side="left", padx=5)
        
        self.diff_btn = ttk.Button(
            button_frame,
            text=f"{self.icons['diff']} Show Diff",
            command=self._show_diff
        )
        self.diff_btn.pack(side="left", padx=5)
        
        self.backup_btn = ttk.Button(
            button_frame,
            text=f"{self.icons['backup']} Backup",
            command=self._backup_dest
        )
        self.backup_btn.pack(side="left", padx=5)
        
        ttk.Separator(button_frame, orient="vertical").pack(side="left", fill="y", padx=10)
        
        self.cancel_btn = ttk.Button(
            button_frame,
            text="⏹ Cancel",
            command=self._cancel_operation,
            state="disabled"
        )
        self.cancel_btn.pack(side="left", padx=5)
    
    def _create_status_bar(self):
        """Create the status bar at the bottom."""
        self.status_frame = ttk.Frame(self.root, relief="sunken", borderwidth=1)
        self.status_frame.grid(row=1, column=0, sticky="ew")
        
        # Left: Status message
        self.status_label = ttk.Label(self.status_frame, text="Ready", anchor="w", padding="3")
        self.status_label.pack(side="left", fill="x", expand=True)
        
        # Middle: File counts
        self.counts_label = ttk.Label(
            self.status_frame, 
            text="Files: 0 | Same: 0 | Diff: 0", 
            anchor="center", 
            padding="3"
        )
        self.counts_label.pack(side="left", padx=20)
        
        # Right: Elapsed time
        self.time_label = ttk.Label(self.status_frame, text="Time: 0.0s", anchor="e", padding="3")
        self.time_label.pack(side="left", padx=10)
        
        # Far right: Progress bar
        self.progress = ttk.Progressbar(self.status_frame, mode="determinate", length=200)
        self.progress.pack(side="right", padx=5)
        self.progress["value"] = 0
        
        # Operation timing
        self._operation_start_time = None
        self._operation_timer_id = None
    
    def _start_timer(self):
        """Start operation timer."""
        self._operation_start_time = time.time()
        self._update_timer()
    
    def _update_timer(self):
        """Update elapsed time display."""
        if self._operation_start_time:
            elapsed = time.time() - self._operation_start_time
            self.time_label.config(text=f"Time: {elapsed:.1f}s")
            self._operation_timer_id = self.root.after(100, self._update_timer)
    
    def _stop_timer(self):
        """Stop operation timer."""
        if self._operation_timer_id:
            self.root.after_cancel(self._operation_timer_id)
            self._operation_timer_id = None
    
    def _update_counts(self):
        """Update file counts display."""
        if self.comparison:
            stats = self.comparison.get_stats()
            self.counts_label.config(
                text=f"Files: {stats['total']} | "
                     f"Same: {stats['exists']} | "
                     f"Diff: {stats['update']} | "
                     f"Missing: {stats['missing']}"
            )
        else:
            total = 0
            if self.source_scan:
                total += len(self.source_scan.files)
            if self.dest_scan:
                total += len(self.dest_scan.files)
            self.counts_label.config(text=f"Files: {total} | Same: 0 | Diff: 0")
    
    def _setup_context_menu(self, tree: ttk.Treeview, panel_type: str):
        """Set up right-click context menu for a treeview."""
        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(
            label="Open in File Browser",
            command=lambda: self._open_in_file_browser(tree, panel_type)
        )
        context_menu.add_separator()
        context_menu.add_command(
            label="Refresh",
            command=lambda: self._refresh_tree(tree, panel_type)
        )
        
        # Bind right-click event
        def show_context_menu(event):
            # Select item under cursor
            item = tree.identify_row(event.y)
            if item:
                tree.selection_set(item)
            
            # Show menu
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
        
        tree.bind("<Button-3>", show_context_menu)  # Right-click on Linux/Windows
        tree.bind("<Control-1>", show_context_menu)  # Right-click on macOS
    
    def _open_in_file_browser(self, tree: ttk.Treeview, panel_type: str):
        """Open selected item in system file manager."""
        selection = tree.selection()
        if not selection:
            return
        
        item = selection[0]
        
        # Get full path
        if panel_type == "source" and self.source_path:
            base_path = self.source_path
        elif panel_type == "destination" and self.dest_path:
            base_path = self.dest_path
        else:
            return
        
        # Build path from tree item
        path_parts = []
        current = item
        
        while current:
            text = tree.item(current, "text")
            path_parts.insert(0, text)
            current = tree.parent(current)
        
        # Construct full path
        full_path = base_path
        for part in path_parts[1:]:  # Skip root
            full_path = full_path / part
        
        # Open in file browser
        self._launch_file_manager(full_path)
    
    def _launch_file_manager(self, path: Path):
        """Launch system file manager at path."""
        if not path.exists():
            messagebox.showerror("Error", f"Path does not exist: {path}")
            return
        
        system = platform.system()
        
        try:
            if system == "Windows":
                # Windows
                os.startfile(str(path))
            elif system == "Darwin":
                # macOS
                subprocess.run(["open", str(path)], check=True)
            else:
                # Linux - try common file managers
                for cmd in ["xdg-open", "nautilus", "dolphin", "thunar", "pcmanfm"]:
                    try:
                        subprocess.run([cmd, str(path)], check=True, capture_output=True)
                        return
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                
                # Fallback to xdg-open without check
                subprocess.Popen(["xdg-open", str(path)])
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file manager: {e}")
    
    def _refresh_tree(self, tree: ttk.Treeview, panel_type: str):
        """Refresh tree contents."""
        if panel_type == "source" and self.source_path:
            self._load_directory_to_tree(tree, self.source_path)
        elif panel_type == "destination" and self.dest_path:
            self._load_directory_to_tree(tree, self.dest_path)
    
    def _open_source(self):
        """Open source directory dialog."""
        path = filedialog.askdirectory(title="Select Source Directory")
        if path:
            self.source_path = Path(path)
            self.left_label.config(text=str(self.source_path))
            self._update_status(f"Source: {self.source_path}")
            self._load_directory_to_tree(self.left_tree, self.source_path)
            self._auto_scan()
    
    def _open_dest(self):
        """Open destination directory dialog."""
        path = filedialog.askdirectory(title="Select Destination Directory")
        if path:
            self.dest_path = Path(path)
            self.right_label.config(text=str(self.dest_path))
            self._update_status(f"Destination: {self.dest_path}")
            self._load_directory_to_tree(self.right_tree, self.dest_path)
            self._auto_scan()
    
    def _auto_scan(self):
        """Auto-scan when both directories are set."""
        if self.source_path and self.dest_path:
            self._scan_directories()
    
    def _scan_directories(self):
        """Scan both directories."""
        if not self.source_path or not self.dest_path:
            messagebox.showwarning("Warning", "Please select both directories first")
            return
        
        self._update_status("Scanning directories...")
        self._start_timer()
        self.progress["mode"] = "indeterminate"
        self.progress.start()
        
        try:
            scanner = DirectoryScanner()
            self.source_scan = scanner.scan(self.source_path)
            self.dest_scan = scanner.scan(self.dest_path)
            
            self.progress.stop()
            self.progress["mode"] = "determinate"
            self.progress["value"] = 100
            
            # Reload trees with scan data
            self._load_directory_to_tree(self.left_tree, self.source_path, self.source_scan)
            self._load_directory_to_tree(self.right_tree, self.dest_path, self.dest_scan)
            
            self._update_counts()
            self._update_status(f"Scanned: {len(self.source_scan.files)} source, {len(self.dest_scan.files)} dest files")
            
            # Auto-compare after scan
            self._compare_directories()
            
        except Exception as e:
            self.progress.stop()
            self.progress["mode"] = "determinate"
            messagebox.showerror("Error", f"Scan failed: {e}")
            self._update_status("Scan failed")
        finally:
            self._stop_timer()
    
    def _compare_directories(self):
        """Compare scanned directories."""
        if not self.source_scan or not self.dest_scan:
            self._update_status("Please scan directories first")
            return
        
        self._update_status("Comparing directories...")
        self._start_timer()
        self.progress["value"] = 0
        
        try:
            comparator = FileComparator(use_quick_compare=True)
            self.comparison = comparator.compare_directories(
                self.source_scan,
                self.dest_scan,
                categories=[FileStatus.MISSING, FileStatus.UPDATE, FileStatus.EXISTS, FileStatus.EXTRA]
            )
            
            self.progress["value"] = 100
            
            # Update treeviews with color coding
            self._apply_comparison_colors()
            
            self._update_counts()
            stats = self.comparison.get_stats()
            self._update_status(
                f"Comparison complete: {stats['missing']} missing, "
                f"{stats['update']} different, {stats['exists']} same, "
                f"{stats['extra']} extra"
            )
            
        except Exception as e:
            messagebox.showerror("Error", f"Comparison failed: {e}")
            self._update_status("Comparison failed")
        finally:
            self._stop_timer()
    
    def _apply_comparison_colors(self):
        """Apply color tags to tree items based on comparison."""
        if not self.comparison:
            return
        
        # Build lookup by relative path
        status_map = {}
        
        for comp in self.comparison.missing:
            rel_path = str(comp.relative_path)
            status_map[rel_path] = "missing"
        
        for comp in self.comparison.update:
            rel_path = str(comp.relative_path)
            status_map[rel_path] = "different"
        
        for comp in self.comparison.exists:
            rel_path = str(comp.relative_path)
            status_map[rel_path] = "same"
        
        for comp in self.comparison.extra:
            rel_path = str(comp.relative_path)
            status_map[rel_path] = "extra"
        
        # Apply colors to tree items
        self._colorize_tree(self.left_tree, self.source_path, status_map)
        self._colorize_tree(self.right_tree, self.dest_path, status_map)
    
    def _colorize_tree(self, tree: ttk.Treeview, base_path: Path, status_map: dict):
        """Apply color tags and status icons to tree items."""
        def process_item(item, current_path):
            text = tree.item(item, "text")
            
            # Extract name from icon+name format
            if " " in text:
                icon, name = text.split(" ", 1)
            else:
                icon, name = "", text
            
            new_path = current_path / name
            
            # Check if this is a file (has size in values)
            values = tree.item(item, "values")
            is_file = values and values[0]  # Size column not empty
            
            rel_path = str(new_path.relative_to(base_path))
            
            if is_file and rel_path in status_map:
                tag = status_map[rel_path]
                tree.item(item, tags=(tag,))
                # Update status column with icon
                status_icon = self.icons.get(tag, "")
                tree.set(item, "status", f"{status_icon} {tag.capitalize()}")
            
            # Process children
            for child in tree.get_children(item):
                process_item(child, new_path)
        
        # Start from root
        for root_item in tree.get_children():
            process_item(root_item, base_path)
    
    def _preview_changes(self):
        """Preview changes before sync."""
        if not self.comparison:
            messagebox.showwarning("Warning", "Please scan and compare directories first")
            return
        
        # Create preview window
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Preview Changes")
        preview_window.geometry("800x600")
        
        # Create treeview for changes
        tree = ttk.Treeview(
            preview_window,
            columns=("action", "source", "destination"),
            show="headings"
        )
        tree.heading("action", text="Action")
        tree.heading("source", text="Source")
        tree.heading("destination", text="Destination")
        tree.column("action", width=100)
        tree.column("source", width=300)
        tree.column("destination", width=300)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(preview_window, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        # Populate with changes with icons
        direction = self.direction_var.get()
        
        for comp in self.comparison.missing:
            tree.insert("", "end", values=(
                f"{self.icons['missing']} Copy", 
                str(comp.source_path), 
                str(comp.dest_path)
            ))
        
        for comp in self.comparison.update:
            tree.insert("", "end", values=(
                f"{self.icons['modified']} Update", 
                str(comp.source_path), 
                str(comp.dest_path)
            ))
        
        if direction == "bidirectional":
            for comp in self.comparison.extra:
                tree.insert("", "end", values=(
                    f"{self.icons['extra']} Copy Back", 
                    str(comp.slave_entry.path), 
                    str(comp.master_entry.path if comp.master_entry else "")
                ))
        
        # Add close button
        ttk.Button(preview_window, text="Close", command=preview_window.destroy).pack(pady=5)
    
    def _synchronize(self):
        """Synchronize directories."""
        if not self.comparison:
            messagebox.showwarning("Warning", "Please scan and compare directories first")
            return
        
        # Get direction
        direction_map = {
            "source_to_dest": SyncDirection.MASTER_TO_SLAVE,
            "dest_to_source": SyncDirection.SLAVE_TO_MASTER,
            "bidirectional": SyncDirection.BIDIRECTIONAL
        }
        direction = direction_map.get(self.direction_var.get(), SyncDirection.MASTER_TO_SLAVE)
        
        # Confirm
        stats = self.comparison.get_stats()
        msg = f"Synchronize with direction: {direction.value}?\n\n"
        msg += f"Files to copy: {stats['missing']}\n"
        msg += f"Files to update: {stats['update']}\n"
        
        if not messagebox.askyesno("Confirm Sync", msg):
            return
        
        self._update_status("Synchronizing...")
        self._start_timer()
        self.progress["value"] = 0
        
        try:
            # Perform merge
            merger = DirectoryMerger(direction=direction, verify=True)
            
            categories = [FileStatus.MISSING, FileStatus.UPDATE]
            if direction == SyncDirection.BIDIRECTIONAL:
                categories.append(FileStatus.EXTRA)
            
            report = merger.merge_all(self.comparison, categories=categories)
            
            # Update progress
            self.progress["value"] = 100
            
            stats = report.get_stats()
            messagebox.showinfo(
                "Sync Complete",
                f"Success: {stats['success']}\nFailed: {stats['failed']}"
            )
            
            self._update_status(f"Sync complete: {stats['success']} success, {stats['failed']} failed")
            
            # Refresh
            self._scan_directories()
            
        except Exception as e:
            messagebox.showerror("Error", f"Sync failed: {e}")
            self._update_status("Sync failed")
        finally:
            self._stop_timer()
    
    def _show_diff(self):
        """Show differences between files."""
        if not self.comparison or not self.comparison.update:
            messagebox.showinfo("Info", "No differences to show")
            return
        
        # Show first different file's diff
        comp = self.comparison.update[0]
        
        diff_window = tk.Toplevel(self.root)
        diff_window.title(f"Diff: {comp.relative_path}")
        diff_window.geometry("900x600")
        
        text = tk.Text(diff_window, wrap="none", font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(diff_window, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        
        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Generate and display diff
        try:
            comparator = FileComparator()
            diff_content = comparator.generate_diff(comp)
            
            if diff_content:
                text.insert("1.0", diff_content)
            else:
                text.insert("1.0", "Unable to generate diff (binary file or permission denied)")
                
        except Exception as e:
            text.insert("1.0", f"Error generating diff: {e}")
        
        text.configure(state="disabled")
    
    def _backup_dest(self):
        """Backup destination directory."""
        if not self.dest_path:
            messagebox.showwarning("Warning", "No destination directory selected")
            return
        
        self._update_status("Creating backup...")
        
        try:
            from gmd.config.schema import BackupConfig
            from gmd.core.backup import BackupManager
            
            config = BackupConfig(enabled=True, directory=Path("./backups"), keep=10)
            backup_mgr = BackupManager(config)
            
            entry = backup_mgr.create_backup(self.dest_path)
            
            if entry:
                messagebox.showinfo(
                    "Backup Complete",
                    f"Backup created: {entry.backup_path}\n"
                    f"Size: {entry.size_bytes} bytes\n"
                    f"Files: {entry.file_count}"
                )
                self._update_status(f"Backup created: {entry.backup_path}")
            else:
                messagebox.showerror("Error", "Backup failed")
                self._update_status("Backup failed")
                
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {e}")
            self._update_status("Backup failed")
    
    def _cancel_operation(self):
        """Cancel current operation."""
        self._update_status("Operation cancelled")
        self.progress["value"] = 0
    
    def _load_directory_to_tree(self, tree: ttk.Treeview, directory: Path, 
                                 scan_result: ScanResult = None):
        """Load directory contents into treeview."""
        # Clear existing items
        for item in tree.get_children():
            tree.delete(item)
        
        if not directory or not directory.exists():
            return
        
        # Add root node with folder icon
        root_node = tree.insert("", "end", text=f"{self.icons['folder']} {directory.name}", 
                                values=("", "", ""), open=True)
        
        if scan_result:
            # Use scan result data
            self._populate_from_scan(tree, root_node, directory, scan_result)
        else:
            # Simple directory listing
            self._populate_simple(tree, root_node, directory)
    
    def _populate_from_scan(self, tree: ttk.Treeview, parent: str, 
                            base_path: Path, scan_result: ScanResult):
        """Populate tree from scan result with icons."""
        from gmd.utils.common import format_size
        
        # Group files by directory
        dirs: dict[str, list] = {}
        for entry in scan_result.files:
            parent_path = str(entry.relative_path.parent)
            if parent_path == ".":
                parent_path = ""
            
            if parent_path not in dirs:
                dirs[parent_path] = []
            dirs[parent_path].append(entry)
        
        # Create directory structure
        created_dirs = {"": parent}
        
        # Sort directories by depth
        sorted_dirs = sorted(dirs.keys(), key=lambda x: x.count("/"))
        
        for dir_path in sorted_dirs:
            # Find or create parent node
            if dir_path == "":
                node_parent = parent
            else:
                parent_dir = str(Path(dir_path).parent)
                if parent_dir == ".":
                    parent_dir = ""
                node_parent = created_dirs.get(parent_dir, parent)
            
            # Create directory node if needed
            if dir_path:
                dir_name = Path(dir_path).name
                if dir_path not in created_dirs:
                    # Add folder icon
                    node = tree.insert(node_parent, "end", text=f"{self.icons['folder']} {dir_name}", 
                                       values=("", "", ""), open=False)
                    created_dirs[dir_path] = node
                else:
                    node = created_dirs[dir_path]
            else:
                node = node_parent
            
            # Add files with icon
            for entry in dirs[dir_path]:
                size_str = format_size(entry.size)
                mtime_str = datetime.datetime.fromtimestamp(
                    entry.modified_time
                ).strftime("%Y-%m-%d %H:%M")
                
                tree.insert(node, "end", text=f"{self.icons['file']} {entry.relative_path.name}",
                           values=(size_str, mtime_str, ""), tags=(""))
    
    def _populate_simple(self, tree: ttk.Treeview, parent: str, directory: Path):
        """Simple directory population without scan result."""
        try:
            for item in sorted(directory.iterdir()):
                if item.is_dir():
                    # Add folder icon
                    node = tree.insert(parent, "end", text=f"{self.icons['folder']} {item.name}", 
                                       values=("", "", ""), open=False)
                    # Recursively add subdirectories (limited depth)
                    self._populate_simple_limited(tree, node, item, depth=1)
                else:
                    size_str = self._format_size(item.stat().st_size)
                    mtime_str = self._format_time(item.stat().st_mtime)
                    # Add file icon
                    tree.insert(parent, "end", text=f"{self.icons['file']} {item.name}",
                               values=(size_str, mtime_str, ""))
        except PermissionError:
            pass
    
    def _populate_simple_limited(self, tree: ttk.Treeview, parent: str, 
                                  directory: Path, depth: int = 0):
        """Populate with limited recursion."""
        if depth <= 0:
            return
        
        try:
            for item in sorted(directory.iterdir()):
                if item.is_dir():
                    # Add folder icon
                    node = tree.insert(parent, "end", text=f"{self.icons['folder']} {item.name}",
                                       values=("", "", ""), open=False)
                    self._populate_simple_limited(tree, node, item, depth - 1)
                else:
                    size_str = self._format_size(item.stat().st_size)
                    mtime_str = self._format_time(item.stat().st_mtime)
                    # Add file icon
                    tree.insert(parent, "end", text=f"{self.icons['file']} {item.name}",
                               values=(size_str, mtime_str, ""))
        except PermissionError:
            pass
    
    def _format_size(self, size: int) -> str:
        """Format file size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def _format_time(self, timestamp: float) -> str:
        """Format timestamp."""
        return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    
    def _show_docs(self):
        """Show documentation."""
        import webbrowser
        docs_path = Path(__file__).parent.parent.parent / "README.md"
        if docs_path.exists():
            webbrowser.open(f"file://{docs_path}")
        else:
            messagebox.showinfo("Documentation", "README.md not found")
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About GMD Merge",
            "GMD Merge v1.0.0\n\n"
            "Directory Synchronization Tool\n\n"
            "A graphical interface for comparing and\n"
            "synchronizing directory contents.\n\n"
            "by w4d4f4k at gmail dot com"
        )
    
    def _update_status(self, message: str):
        """Update status bar message."""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def _on_close(self):
        """Handle window close."""
        if messagebox.askyesno("Confirm", "Are you sure you want to exit?"):
            self.root.destroy()
    
    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()


def main():
    """Entry point for GUI application."""
    app = GMDGuiApp()
    app.run()


if __name__ == "__main__":
    main()
