"""
Integration tests for GMD GUI module.

Tests that the GUI module integrates correctly with gmd.core modules.
"""

import unittest
import tempfile
import os
from pathlib import Path

from gmd.gui import GMDGuiApp, main, launch_gui
from gmd.core.scanner import DirectoryScanner
from gmd.core.comparator import FileComparator
from gmd.core.merger import DirectoryMerger
from gmd.config.schema import GMDConfig, SyncDirection


class TestGUIIntegration(unittest.TestCase):
    """Test GUI integration with core modules."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.source_dir = Path(self.temp_dir) / "source"
        self.dest_dir = Path(self.temp_dir) / "dest"
        self.source_dir.mkdir()
        self.dest_dir.mkdir()
        
        # Create test files
        (self.source_dir / "file1.txt").write_text("content1")
        (self.source_dir / "file2.txt").write_text("content2")
        (self.dest_dir / "file1.txt").write_text("content1")  # Same
        (self.dest_dir / "file3.txt").write_text("content3")  # Extra
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_gui_imports(self):
        """Test that GUI module imports work correctly."""
        self.assertIsNotNone(GMDGuiApp)
        self.assertIsNotNone(main)
        self.assertIsNotNone(launch_gui)
    
    def test_scanner_integration(self):
        """Test that GUI can use DirectoryScanner."""
        scanner = DirectoryScanner()
        result = scanner.scan(self.source_dir)
        
        self.assertEqual(len(result.files), 2)
        self.assertIn("file1.txt", [f.name for f in result.files])
        self.assertIn("file2.txt", [f.name for f in result.files])
    
    def test_comparator_integration(self):
        """Test that GUI can use FileComparator."""
        scanner = DirectoryScanner()
        source_scan = scanner.scan(self.source_dir)
        dest_scan = scanner.scan(self.dest_dir)
        
        comparator = FileComparator()
        comparison = comparator.compare_directories(source_scan, dest_scan)
        
        self.assertIsNotNone(comparison)
        self.assertTrue(len(comparison.missing) > 0 or len(comparison.exists) > 0)
    
    def test_merger_integration(self):
        """Test that GUI can use DirectoryMerger."""
        scanner = DirectoryScanner()
        source_scan = scanner.scan(self.source_dir)
        dest_scan = scanner.scan(self.dest_dir)
        
        comparator = FileComparator()
        comparison = comparator.compare_directories(source_scan, dest_scan)
        
        merger = DirectoryMerger(direction=SyncDirection.MASTER_TO_SLAVE)
        report = merger.merge_all(comparison)
        
        self.assertIsNotNone(report)
    
    def test_config_integration(self):
        """Test that GUI can use GMDConfig."""
        config = GMDConfig(
            source=self.source_dir,
            destination=self.dest_dir,
            direction=SyncDirection.MASTER_TO_SLAVE
        )
        
        self.assertEqual(config.source, self.source_dir)
        self.assertEqual(config.destination, self.dest_dir)


class TestGUIApp(unittest.TestCase):
    """Test GMDGuiApp class."""
    
    def test_app_creation(self):
        """Test that GMDGuiApp can be created."""
        # Note: We don't call run() to avoid opening a window
        app = GMDGuiApp()
        self.assertIsNotNone(app.root)
        self.assertIsNotNone(app.left_tree)
        self.assertIsNotNone(app.right_tree)
        app.root.destroy()


if __name__ == "__main__":
    unittest.main()
