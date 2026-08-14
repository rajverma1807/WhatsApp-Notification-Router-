"""Configuration helpers and path discovery for the notification router project."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    """Application configuration object with project and dataset paths."""

    project_root: Path
    src_dir: Path
    dataset_dir: Path
    output_dir: Path
    media_dir: Path

    @classmethod
    def from_environment(cls) -> "AppConfig":
        """Load configuration from environment variables and auto-detect paths."""
        load_dotenv()

        project_root = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parent.parent)).expanduser().resolve()
        src_dir = project_root / "src"
        output_dir = project_root / "output"
        media_dir = project_root / "media"

        dataset_dir_value = os.getenv("DATASET_DIR", "").strip()
        if dataset_dir_value:
            dataset_dir = Path(dataset_dir_value).expanduser().resolve()
        else:
            dataset_dir = cls._find_dataset_dir(project_root)

        return cls(
            project_root=project_root,
            src_dir=src_dir,
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            media_dir=media_dir,
        )

    @staticmethod
    def _find_dataset_dir(project_root: Path) -> Path:
        """Locate a dataset directory by checking common project layouts."""
        candidates = [
            project_root / "dataset",
            project_root / "hackerrank-orchestrate-august26" / "dataset",
        ]

        for path in project_root.rglob("dataset"):
            if path.is_dir():
                candidates.append(path)

        seen: set[Path] = set()
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.exists() and resolved.is_dir():
                csv_files = list(resolved.glob("*.csv"))
                if csv_files:
                    return resolved

        # Return a non-existent path as default instead of raising error
        # This allows the app to work in environments where datasets are not available
        return project_root / "dataset"
