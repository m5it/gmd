"""
Pydantic models for GMD configuration validation.
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class OutputFormat(str, Enum):
    """Supported output formats."""
    COLOR = "color"
    PLAIN = "plain"
    JSON = "json"
    SILENT = "silent"


class SyncDirection(str, Enum):
    """Sync directions."""
    MASTER_TO_SLAVE = "master-to-slave"
    SLAVE_TO_MASTER = "slave-to-master"
    BIDIRECTIONAL = "bidirectional"


class SyncMode(str, Enum):
    """Sync modes."""
    INTERACTIVE = "interactive"
    AUTO = "auto"
    SAFE = "safe"


class Action(str, Enum):
    """Merge actions."""
    PREVIEW = "preview"
    SYNC = "sync"
    DIFF = "diff"
    BACKUP = "backup"


class Categories(str, Enum):
    """File categories to process."""
    MISSING = "missing"
    UPDATE = "update"
    EXISTS = "exists"


class OutputConfig(BaseModel):
    """Output configuration."""
    format: OutputFormat = OutputFormat.COLOR
    progress: bool = True
    report: Optional[Path] = None
    
    @field_validator("report")
    @classmethod
    def validate_report(cls, v: Optional[Path]) -> Optional[Path]:
        if v is not None and v.is_dir():
            raise ValueError("report must be a file path, not a directory")
        return v


class BackupConfig(BaseModel):
    """Backup configuration."""
    enabled: bool = True
    directory: Path = Path("./backups")
    keep: int = Field(default=10, ge=1, le=100)
    
    @field_validator("directory")
    @classmethod
    def validate_directory(cls, v: Path) -> Path:
        return v.expanduser().resolve()


class MergeConfig(BaseModel):
    """Merge-specific configuration."""
    direction: SyncDirection = SyncDirection.MASTER_TO_SLAVE
    mode: SyncMode = SyncMode.INTERACTIVE
    categories: List[Categories] = Field(default_factory=lambda: [Categories.MISSING, Categories.UPDATE])
    excludes: List[str] = Field(default_factory=list)
    dry_run: bool = False


class CommitConfig(BaseModel):
    """Commit-specific configuration."""
    auto_push: bool = False
    parallel: bool = True
    max_workers: int = Field(default=4, ge=1, le=16)


class GMDConfig(BaseModel):
    """Main GMD configuration."""
    master: Optional[Path] = None
    slave: Optional[Path] = None
    gitdir: Optional[Path] = None
    
    output: OutputConfig = Field(default_factory=OutputConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)
    merge: MergeConfig = Field(default_factory=MergeConfig)
    commit: CommitConfig = Field(default_factory=CommitConfig)
    
    @field_validator("master", "slave", "gitdir")
    @classmethod
    def validate_paths(cls, v: Optional[Path]) -> Optional[Path]:
        if v is not None:
            return v.expanduser().resolve()
        return v
    
    class Config:
        extra = "ignore"
