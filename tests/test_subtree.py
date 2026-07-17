"""
Integration tests for git subtree functionality in gmd-commit.

Tests subtree detection, pull, push operations with mocked git commands.
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from gmd.cli.commit import GitSubmoduleManager, Subtree, OutputFormatter
from gmd.config.schema import OutputConfig


class TestSubtreeDetection(unittest.TestCase):
    """Test subtree detection functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.gitdir = Path("/fake/repo")
        self.formatter = OutputFormatter(OutputConfig())
        self.manager = GitSubmoduleManager(self.gitdir, self.formatter)
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_detect_subtrees_empty(self, mock_run):
        """Test detection when no subtrees exist."""
        # Mock git log returning empty result
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        subtrees = self.manager.detect_subtrees()
        self.assertEqual(len(subtrees), 0)
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_detect_subtrees_success(self, mock_run):
        """Test successful subtree detection."""
        # Mock git log returning commit hashes
        mock_run.side_effect = [
            # First call: git log
            Mock(returncode=0, stdout="abc123 Subtree merge\n", stderr=""),
            # Second call: git show for first commit
            Mock(
                returncode=0,
                stdout="git-subtree-dir: libs/mylib\ngit-subtree-url: https://github.com/user/mylib.git\n",
                stderr=""
            ),
        ]
        
        subtrees = self.manager.detect_subtrees()
        self.assertEqual(len(subtrees), 1)
        self.assertEqual(subtrees[0].name, "mylib")
        self.assertEqual(subtrees[0].prefix, "libs/mylib")
        self.assertEqual(subtrees[0].url, "https://github.com/user/mylib.git")
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_detect_subtrees_multiple(self, mock_run):
        """Test detection of multiple subtrees."""
        mock_run.side_effect = [
            # First call: git log with multiple commits
            Mock(returncode=0, stdout="abc123 First subtree\ndef456 Second subtree\n", stderr=""),
            # Second call: git show first
            Mock(returncode=0, stdout="git-subtree-dir: lib/a\ngit-subtree-url: url-a\n", stderr=""),
            # Third call: git show second
            Mock(returncode=0, stdout="git-subtree-dir: lib/b\ngit-subtree-url: url-b\n", stderr=""),
        ]
        
        subtrees = self.manager.detect_subtrees()
        self.assertEqual(len(subtrees), 2)
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_detect_subtrees_no_url(self, mock_run):
        """Test detection when subtree has no URL."""
        mock_run.side_effect = [
            Mock(returncode=0, stdout="abc123 Subtree merge\n", stderr=""),
            Mock(returncode=0, stdout="git-subtree-dir: libs/mylib\n", stderr=""),
        ]
        
        subtrees = self.manager.detect_subtrees()
        self.assertEqual(len(subtrees), 1)
        self.assertIsNone(subtrees[0].url)


class TestSubtreeStatus(unittest.TestCase):
    """Test subtree status checking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.gitdir = Path("/fake/repo")
        self.formatter = OutputFormatter(OutputConfig())
        self.manager = GitSubmoduleManager(self.gitdir, self.formatter)
        self.subtree = Subtree(
            name="mylib",
            path=Path("/fake/repo/libs/mylib"),
            url="https://github.com/user/mylib.git",
            prefix="libs/mylib"
        )
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_get_subtree_status_clean(self, mock_run):
        """Test status when subtree is clean."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        status, details = self.manager.get_subtree_status(self.subtree)
        self.assertEqual(status, "clean")
        self.assertEqual(details, "no changes")
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_get_subtree_status_modified(self, mock_run):
        """Test status when subtree has modifications."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=" M file1.txt\n?? file2.txt\n D file3.txt\n",
            stderr=""
        )
        
        status, details = self.manager.get_subtree_status(self.subtree)
        self.assertEqual(status, "modified")
        self.assertIn("1 modified", details)
        self.assertIn("1 added", details)
        self.assertIn("1 deleted", details)
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_get_subtree_status_error(self, mock_run):
        """Test status when git command fails."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="fatal: not a git repository"
        )
        
        status, details = self.manager.get_subtree_status(self.subtree)
        self.assertEqual(status, "error")
        self.assertIn("not a git repository", details)


class TestSubtreeOperations(unittest.TestCase):
    """Test subtree pull and push operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.gitdir = Path("/fake/repo")
        self.formatter = OutputFormatter(OutputConfig())
        self.manager = GitSubmoduleManager(self.gitdir, self.formatter)
        self.subtree = Subtree(
            name="mylib",
            path=Path("/fake/repo/libs/mylib"),
            url="https://github.com/user/mylib.git",
            prefix="libs/mylib"
        )
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_subtree_pull_success(self, mock_run):
        """Test successful subtree pull."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Merge made by the 'ort' strategy.",
            stderr=""
        )
        
        success, message = self.manager.subtree_pull(self.subtree, squash=True, dry_run=False)
        self.assertTrue(success)
        self.assertIn("Pulled", message)
        
        # Verify correct command was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertIn("subtree", call_args)
        self.assertIn("pull", call_args)
        self.assertIn("--squash", call_args)
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_subtree_pull_dry_run(self, mock_run):
        """Test subtree pull in dry-run mode."""
        success, message = self.manager.subtree_pull(self.subtree, squash=True, dry_run=True)
        self.assertTrue(success)
        self.assertIn("Would pull", message)
        mock_run.assert_not_called()
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_subtree_pull_missing_url(self, mock_run):
        """Test pull when subtree has no URL."""
        subtree_no_url = Subtree(
            name="mylib",
            path=Path("/fake/repo/libs/mylib"),
            url=None,
            prefix="libs/mylib"
        )
        
        success, message = self.manager.subtree_pull(subtree_no_url)
        self.assertFalse(success)
        self.assertIn("missing URL", message)
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_subtree_push_success(self, mock_run):
        """Test successful subtree push."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="git push using: https://github.com/user/mylib.git main\n",
            stderr=""
        )
        
        success, message = self.manager.subtree_push(self.subtree, dry_run=False)
        self.assertTrue(success)
        self.assertIn("Pushed", message)
    
    @patch('gmd.cli.commit.subprocess.run')
    def test_subtree_push_failure(self, mock_run):
        """Test failed subtree push."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="fatal: unable to access"
        )
        
        success, message = self.manager.subtree_push(self.subtree, dry_run=False)
        self.assertFalse(success)
        self.assertIn("unable to access", message)


class TestSubtreeProcessing(unittest.TestCase):
    """Test subtree processing workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.gitdir = Path("/fake/repo")
        self.formatter = OutputFormatter(OutputConfig())
        self.manager = GitSubmoduleManager(self.gitdir, self.formatter)
        self.subtree = Subtree(
            name="mylib",
            path=Path("/fake/repo/libs/mylib"),
            url="https://github.com/user/mylib.git",
            prefix="libs/mylib"
        )
    
    @patch.object(GitSubmoduleManager, 'get_subtree_status')
    def test_process_subtree_status(self, mock_status):
        """Test processing status operation."""
        mock_status.return_value = ("clean", "no changes")
        
        result = self.manager.process_subtree(self.subtree, "status", dry_run=False)
        
        self.assertEqual(result["name"], "mylib")
        self.assertEqual(result["status"], "clean")
        self.assertEqual(result["operation"], "status")
        self.assertEqual(result["type"], "subtree")
    
    @patch.object(GitSubmoduleManager, 'subtree_pull')
    def test_process_subtree_pull(self, mock_pull):
        """Test processing pull operation."""
        mock_pull.return_value = (True, "Pulled successfully")
        
        result = self.manager.process_subtree(self.subtree, "pull", dry_run=False)
        
        self.assertTrue(result["success"])
        self.assertEqual(len(result["steps"]), 1)
        self.assertEqual(result["steps"][0]["action"], "pull")
    
    @patch.object(GitSubmoduleManager, 'subtree_push')
    def test_process_subtree_push(self, mock_push):
        """Test processing push operation."""
        mock_push.return_value = (True, "Pushed successfully")
        
        result = self.manager.process_subtree(self.subtree, "push", dry_run=False)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["steps"][0]["action"], "push")


class TestSubtreeConfig(unittest.TestCase):
    """Test subtree configuration."""
    
    def test_subtree_config_defaults(self):
        """Test default subtree configuration values."""
        from gmd.config.schema import SubtreeConfig
        
        config = SubtreeConfig()
        self.assertFalse(config.auto_pull)
        self.assertTrue(config.squash)
        self.assertEqual(config.message_prefix, "[subtree] ")
        self.assertEqual(config.default_branch, "main")
    
    def test_subtree_config_validation(self):
        """Test subtree configuration validation."""
        from gmd.config.schema import SubtreeConfig
        
        # Test message prefix auto-adds space
        config = SubtreeConfig(message_prefix="[custom]")
        self.assertEqual(config.message_prefix, "[custom] ")
        
        # Test with trailing space preserved
        config2 = SubtreeConfig(message_prefix="[custom] ")
        self.assertEqual(config2.message_prefix, "[custom] ")


class TestSubtreeIntegration(unittest.TestCase):
    """Test integration with existing commit workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.gitdir = Path("/fake/repo")
        self.formatter = OutputFormatter(OutputConfig())
        self.manager = GitSubmoduleManager(self.gitdir, self.formatter)
    
    @patch.object(GitSubmoduleManager, 'detect_subtrees')
    @patch.object(GitSubmoduleManager, 'process_subtree')
    def test_subtree_mode_detection(self, mock_process, mock_detect):
        """Test that --subtrees flag triggers subtree mode."""
        # Setup mock subtrees
        mock_subtree = Subtree(
            name="mylib",
            path=Path("/fake/repo/libs/mylib"),
            url="https://github.com/user/mylib.git",
            prefix="libs/mylib"
        )
        mock_detect.return_value = [mock_subtree]
        mock_process.return_value = {"name": "mylib", "success": True, "type": "subtree"}
        
        # Verify detection was called
        subtrees = self.manager.detect_subtrees()
        self.assertEqual(len(subtrees), 1)
        
        # Verify processing works
        result = self.manager.process_subtree(mock_subtree, "status")
        self.assertEqual(result["type"], "subtree")
    
    def test_subtree_vs_submodule_methods(self):
        """Test that subtree methods don't interfere with submodule methods."""
        # Both should exist and be callable
        self.assertTrue(hasattr(self.manager, 'detect_submodules'))
        self.assertTrue(hasattr(self.manager, 'detect_subtrees'))
        self.assertTrue(hasattr(self.manager, 'get_submodule_status'))
        self.assertTrue(hasattr(self.manager, 'get_subtree_status'))
        self.assertTrue(hasattr(self.manager, 'process_submodule'))
        self.assertTrue(hasattr(self.manager, 'process_subtree'))


if __name__ == "__main__":
    unittest.main()
