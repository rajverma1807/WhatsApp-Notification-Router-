"""Generate the routing output CSV file from classifier predictions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from utils import ensure_directory, LOGGER


def write_output_csv(rows: list[dict[str, Any]], output_path: Path | str) -> pd.DataFrame:
    """Write routing decisions to a CSV file with the required schema and sane formatting."""
    output_path = Path(output_path)
    ensure_directory(output_path.parent)

    frame = pd.DataFrame(rows)
    required_columns = [
        "message_id",
        "action",
        "message_type",
        "reason",
        "confidence",
        "evidence_message_ids",
    ]
    for column in required_columns:
        if column not in frame.columns:
            frame[column] = pd.NA

    frame = frame[required_columns]
    frame["message_id"] = frame["message_id"].fillna("").astype(str)
    frame["action"] = frame["action"].fillna("digest").astype(str)
    frame["message_type"] = frame["message_type"].fillna("unknown").astype(str)
    frame["reason"] = frame["reason"].fillna("").astype(str)
    frame["confidence"] = frame["confidence"].fillna(0.6)
    if "confidence" in frame.columns:
        frame["confidence"] = frame["confidence"].apply(lambda value: round(float(value), 2))
    frame["evidence_message_ids"] = frame["evidence_message_ids"].fillna("none").astype(str)
    frame.to_csv(output_path, index=False)
    LOGGER.info("Wrote %s rows to %s", len(frame), output_path)
    return frame
