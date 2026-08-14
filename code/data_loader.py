"""Data loading utilities for the notification routing project."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from utils import LOGGER


def _safe_read_csv(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    """Load a CSV file, returning an empty DataFrame when the file is missing."""
    if not path.exists():
        if columns:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame()

    try:
        frame = pd.read_csv(path)
    except Exception as exc:  # pragma: no cover - defensive path for malformed CSVs
        LOGGER.warning("Could not read %s: %s", path, exc)
        if columns:
            return pd.DataFrame(columns=columns)
        return pd.DataFrame()

    if columns:
        missing_columns = [column for column in columns if column not in frame.columns]
        for column in missing_columns:
            frame[column] = pd.NA
    return frame


def load_messages(dataset_dir: Path) -> pd.DataFrame:
    """Load the main messages dataset."""
    return _safe_read_csv(
        dataset_dir / "messages.csv",
        columns=[
            "message_id",
            "user_id",
            "conversation_type",
            "group_id",
            "business_id",
            "sender_user_id",
            "created_at",
            "message_text",
            "media_type",
            "media_id",
            "forwarded_count",
        ],
    )


def load_users(dataset_dir: Path) -> pd.DataFrame:
    """Load the user profile dataset."""
    return _safe_read_csv(
        dataset_dir / "users.csv",
        columns=[
            "user_id",
            "do_not_disturb_window",
            "messages_opened_30d",
            "messages_replied_30d",
            "notifications_dismissed_30d",
            "messages_reported_30d",
        ],
    )


def load_groups(dataset_dir: Path) -> pd.DataFrame:
    """Load group metadata."""
    return _safe_read_csv(
        dataset_dir / "groups.csv",
        columns=["group_id", "group_name", "group_type", "member_count", "admin_count", "created_at", "messages_30d"],
    )


def load_group_members(dataset_dir: Path) -> pd.DataFrame:
    """Load group membership records."""
    return _safe_read_csv(
        dataset_dir / "group_members.csv",
        columns=[
            "group_id",
            "user_id",
            "role",
            "joined_at",
            "messages_sent_30d",
            "messages_read_30d",
            "replies_sent_30d",
            "notifications_dismissed_30d",
            "group_muted_by_user",
        ],
    )


def load_business_accounts(dataset_dir: Path) -> pd.DataFrame:
    """Load business account metadata."""
    return _safe_read_csv(
        dataset_dir / "business_accounts.csv",
        columns=[
            "business_id",
            "display_name",
            "brand_name",
            "category",
            "verified",
            "official_domain",
            "domain_used_by_sender",
            "account_age_days",
            "messages_sent_30d",
            "user_reports_30d",
            "domain_used_by_sender_age_days",
        ],
    )


def load_user_business_history(dataset_dir: Path) -> pd.DataFrame:
    """Load user-to-business interaction history."""
    return _safe_read_csv(
        dataset_dir / "user_business_history.csv",
        columns=[
            "user_id",
            "business_id",
            "why_user_knows_account",
            "last_activity_at",
            "allows_promotions",
            "promotions_opted_out_at",
            "activity_count_180d",
            "messages_opened_30d",
            "messages_dismissed_30d",
            "messages_replied_30d",
            "last_reply_at",
        ],
    )


def load_message_history(dataset_dir: Path) -> pd.DataFrame:
    """Load historical messages for retrieval and evidence matching."""
    return _safe_read_csv(
        dataset_dir / "message_history.csv",
        columns=[
            "message_id",
            "user_id",
            "conversation_type",
            "group_id",
            "business_id",
            "sender_user_id",
            "created_at",
            "message_text",
            "media_type",
            "media_id",
            "forwarded_count",
        ],
    )


def load_message_events(dataset_dir: Path) -> pd.DataFrame:
    """Load message interaction events such as opens and replies."""
    return _safe_read_csv(
        dataset_dir / "message_events.csv",
        columns=[
            "user_id",
            "message_id",
            "message_opened",
            "message_replied",
            "reaction_time_minutes",
            "notification_dismissed",
            "muted_after_message",
            "message_reported",
        ],
    )


def load_images(dataset_dir: Path) -> pd.DataFrame:
    """Load image metadata."""
    return _safe_read_csv(dataset_dir / "images.csv", columns=["image_id", "file_path"])


def load_voice_notes(dataset_dir: Path) -> pd.DataFrame:
    """Load voice note metadata."""
    return _safe_read_csv(dataset_dir / "voice_notes.csv", columns=["voice_note_id", "file_path"])


def load_daily_notification_summary(dataset_dir: Path) -> pd.DataFrame:
    """Load daily notification summary data."""
    return _safe_read_csv(
        dataset_dir / "daily_notification_summary.csv",
        columns=["user_id", "date", "notifications_sent", "notifications_dismissed"],
    )


def load_all_datasets(dataset_dir: Path) -> dict[str, pd.DataFrame]:
    """Load all supported datasets into a dictionary keyed by filename."""
    loaders = {
        "messages.csv": load_messages,
        "users.csv": load_users,
        "groups.csv": load_groups,
        "group_members.csv": load_group_members,
        "business_accounts.csv": load_business_accounts,
        "user_business_history.csv": load_user_business_history,
        "message_history.csv": load_message_history,
        "message_events.csv": load_message_events,
        "images.csv": load_images,
        "voice_notes.csv": load_voice_notes,
        "daily_notification_summary.csv": load_daily_notification_summary,
    }

    datasets: dict[str, pd.DataFrame] = {}
    for filename, loader in loaders.items():
        datasets[filename] = loader(dataset_dir)
    return datasets
