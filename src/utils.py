"""Utility helpers shared across the notification routing pipeline."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def configure_logging(name: str = "notification_router") -> logging.Logger:
    """Create a consistent logger for the application."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


LOGGER = configure_logging()


def ensure_directory(path: Path | str) -> Path:
    """Create a directory if it does not already exist."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def clean_text(text: Any) -> str:
    """Normalize text by stripping whitespace and collapsing repeated spaces."""
    if text is None:
        return ""
    cleaned = str(text).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def convert_timestamp(value: Any, fmt: str = "%Y-%m-%d %H:%M") -> datetime | None:
    """Try to parse a timestamp from common string formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        candidate = value.strip()
        for pattern in (fmt, "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(candidate, pattern)
            except ValueError:
                continue
    return None
