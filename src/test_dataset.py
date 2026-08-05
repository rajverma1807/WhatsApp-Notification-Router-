"""Inspect the workspace datasets and print their schema and sample rows.

This script is intentionally simple and Windows-friendly. It detects the
project root automatically, finds the dataset directory even when it is nested,
and loads every CSV file in that directory using pandas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


def find_dataset_directory(start_path: Path | None = None) -> Path:
    """Locate the dataset directory by checking common project layouts.

    The search order is:
    1. The project root (parent of this script)
    2. A nested project folder such as <project>/hackerrank-orchestrate-august26
    3. Any descendant directory named "dataset" that contains CSV files

    Returns:
        Path: The resolved dataset directory.

    Raises:
        FileNotFoundError: If no dataset directory containing CSV files is found.
    """
    if start_path is None:
        start_path = Path(__file__).resolve().parent.parent

    candidates: list[Path] = []
    project_root = start_path.resolve()
    candidates.append(project_root / "dataset")
    candidates.append(project_root / "hackerrank-orchestrate-august26" / "dataset")

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

    raise FileNotFoundError(
        "Could not find a dataset directory containing CSV files. "
        f"Searched from: {project_root}"
    )


def load_all_csv_files(dataset_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load every CSV file in the dataset directory into a dictionary.

    Args:
        dataset_dir: Path to the directory that contains CSV files.

    Returns:
        Dict[str, pd.DataFrame]: A mapping of file name to DataFrame.
    """
    csv_files = sorted(dataset_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {dataset_dir}")

    loaded_frames: Dict[str, pd.DataFrame] = {}
    for csv_path in csv_files:
        df = pd.read_csv(csv_path)
        loaded_frames[csv_path.name] = df

    return loaded_frames


def print_dataset_summary(dataframes: Dict[str, pd.DataFrame]) -> None:
    """Print each DataFrame's shape, columns, and first two rows."""
    for name, df in dataframes.items():
        print(f"{'=' * 60}")
        print(f"File: {name}")
        print(f"Shape: {df.shape}")
        print("Columns:")
        for column in df.columns:
            print(f"  - {column}")
        print("First two rows:")
        print(df.head(2).to_string(index=False))
        print()


def main() -> None:
    """Entry point for the dataset inspection script."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root: {project_root}")

    dataset_dir = find_dataset_directory(project_root)
    print(f"Dataset directory: {dataset_dir}")

    dataframes = load_all_csv_files(dataset_dir)
    print_dataset_summary(dataframes)


if __name__ == "__main__":
    main()
