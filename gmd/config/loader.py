"""
Configuration loader with auto-detection and CLI merging.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from gmd.config.schema import GMDConfig


class ConfigLoader:
    """Load and merge configuration from files and CLI arguments."""
    
    CONFIG_FILES = [
        ".gmdrc",
        ".gmdrc.json",
        ".gmdrc.yaml",
        ".gmdrc.yml",
        "gmd.config.json",
        "gmd.config.yaml",
        "gmd.config.yml",
    ]
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path
        self._loaded_config: Dict[str, Any] = {}
    
    def load(self) -> GMDConfig:
        """Load configuration from file or auto-detect."""
        if self.config_path:
            self._loaded_config = self._load_file(self.config_path)
        else:
            self._loaded_config = self._auto_detect()
        
        return GMDConfig(**self._loaded_config)
    
    def _auto_detect(self) -> Dict[str, Any]:
        """Auto-detect config file in current directory."""
        for filename in self.CONFIG_FILES:
            path = Path(filename)
            if path.exists():
                print(f"Loading config: {path}")
                return self._load_file(path)
        return {}
    
    def _load_file(self, path: Path) -> Dict[str, Any]:
        """Load configuration from file."""
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        content = path.read_text(encoding="utf-8")
        
        if path.suffix in (".yaml", ".yml"):
            return yaml.safe_load(content) or {}
        elif path.suffix == ".json" or path.name == ".gmdrc":
            return json.loads(content)
        else:
            # Try JSON first, then YAML
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return yaml.safe_load(content) or {}
    
    def merge_with_cli(self, cli_args: Dict[str, Any]) -> GMDConfig:
        """
        Merge loaded config with CLI arguments.
        CLI args take precedence over config file.
        """
        # Start with loaded config
        merged = self._loaded_config.copy()
        
        # Merge CLI args (non-None values only)
        self._deep_merge(merged, self._filter_none(cli_args))
        
        return GMDConfig(**merged)
    
    def _filter_none(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out None values from dict."""
        return {k: v for k, v in d.items() if v is not None}
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Deep merge override into base."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def create_example_config(self, path: Path, format: str = "json") -> None:
        """Create example configuration file."""
        example = self._get_example_config()
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format in ("yaml", "yml"):
            path = path.with_suffix(".yaml")
            path.write_text(yaml.dump(example, default_flow_style=False, sort_keys=False))
        else:
            path = path.with_suffix(".json")
            path.write_text(json.dumps(example, indent=2))
        
        print(f"Created example config: {path}")
    
    def _get_example_config(self) -> Dict[str, Any]:
        """Get example configuration dictionary."""
        return {
            "master": "/path/to/master/directory",
            "slave": "/path/to/slave/directory",
            "output": {
                "format": "color",
                "progress": True,
                "report": "./gmd-report.json"
            },
            "backup": {
                "enabled": True,
                "directory": "./backups",
                "keep": 10
            },
            "merge": {
                "direction": "master-to-slave",
                "mode": "interactive",
                "categories": ["missing", "update"],
                "excludes": ["*.tmp", ".git/", "node_modules/", "*.log"],
                "dry_run": False
            },
            "commit": {
                "auto_push": False,
                "parallel": True,
                "max_workers": 4
            }
        }
