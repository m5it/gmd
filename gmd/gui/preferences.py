"""
Persistent preferences for the GMD GUI.

Stores window geometry, selected categories, direction, and exclude patterns
in ~/.config/kosgmd/config.yaml (XDG-compliant).
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class GuiPreferences:
    """Manage persistent GUI preferences."""

    _DEFAULT_CONFIG_DIR = Path.home() / ".config" / "kosgmd"
    _DEFAULT_CONFIG_PATH = _DEFAULT_CONFIG_DIR / "config.yaml"

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self._DEFAULT_CONFIG_PATH
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load preferences from disk."""
        if not self.config_path.exists():
            self.data = {}
            return
        try:
            with open(self.config_path, "r", encoding="utf-8") as fh:
                loaded = yaml.safe_load(fh)
                self.data = loaded if isinstance(loaded, dict) else {}
        except Exception:
            self.data = {}

    def save(self) -> None:
        """Save preferences to disk."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as fh:
                yaml.safe_dump(self.data, fh, default_flow_style=False, sort_keys=True)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """Get a top-level preference value."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a top-level preference value and save."""
        self.data[key] = value
        self.save()

    def get_geometry(self) -> Optional[Dict[str, Any]]:
        """Return stored window geometry dict or None."""
        return self.get("geometry")

    def set_geometry(self, width: int, height: int, x: int, y: int) -> None:
        """Store window geometry."""
        self.set("geometry", {
            "width": width,
            "height": height,
            "x": x,
            "y": y,
        })

    def get_categories(self) -> Optional[List[str]]:
        """Return list of selected category names or None."""
        return self.get("categories")

    def set_categories(self, categories: List[str]) -> None:
        """Store selected category names."""
        self.set("categories", categories)

    def get_direction(self) -> Optional[str]:
        """Return selected sync direction or None."""
        return self.get("direction")

    def set_direction(self, direction: str) -> None:
        """Store selected sync direction."""
        self.set("direction", direction)

    def get_excludes(self) -> Optional[str]:
        """Return exclude patterns string or None."""
        return self.get("excludes")

    def set_excludes(self, excludes: str) -> None:
        """Store exclude patterns string."""
        self.set("excludes", excludes)

    def get_last_dirs(self) -> Optional[Dict[str, Optional[str]]]:
        """Return last selected source/destination directories."""
        return self.get("last_dirs")

    def set_last_dirs(self, source: Optional[str], destination: Optional[str]) -> None:
        """Store last selected source/destination directories."""
        self.set("last_dirs", {"source": source, "destination": destination})
