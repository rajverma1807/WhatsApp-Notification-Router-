"""Entry point for the WhatsApp notification routing pipeline."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pandas as pd

from classifier import NotificationClassifier
from config import AppConfig
from data_loader import load_all_datasets
from output_generator import write_output_csv
from retrieval import MessageRetriever
from utils import LOGGER, ensure_directory


def build_context_for_message(
    message: dict[str, Any],
    datasets: dict[str, pd.DataFrame],
) -> dict[str, Any]:
    """Build a richer context bundle for classification using the provided datasets."""
    context: dict[str, Any] = {}

    users = datasets.get("users.csv")
    if users is not None and not users.empty:
        user_profile = users[users["user_id"] == message.get("user_id")]
        if not user_profile.empty:
            context["user_profile"] = user_profile.iloc[0].to_dict()

    business_history = datasets.get("user_business_history.csv")
    if business_history is not None and not business_history.empty:
        user_business_entries = business_history[business_history["user_id"] == message.get("user_id")]
        business_id = message.get("business_id")
        if business_id is not None and business_id not in {None, ""}:
            business_entries = user_business_entries[user_business_entries["business_id"] == business_id]
            if not business_entries.empty:
                business_row = business_entries.iloc[0].to_dict()
                context["business_context"] = {
                    "activity_count_180d": int(business_row.get("activity_count_180d", 0) or 0),
                    "allows_promotions": bool(business_row.get("allows_promotions", True)),
                }

    history = datasets.get("message_history.csv")
    if history is not None and not history.empty:
        user_history = history[history["user_id"] == message.get("user_id")]
        promotional_history = user_history[user_history["message_text"].astype(str).str.contains("sale|discount|offer|coupon|promotion|deal", case=False, na=False)]
        context["history_context"] = {
            "promotional_dismissals": int(len(promotional_history) or 0),
        }

    return context


def run_pipeline() -> None:
    """Load datasets, classify each message, and write the output CSV."""
    config = AppConfig.from_environment()
    ensure_directory(config.output_dir)

    datasets = load_all_datasets(config.dataset_dir)
    messages = datasets.get("messages.csv")
    if messages is None or messages.empty:
        LOGGER.warning("No messages were loaded; nothing to process.")
        return

    history = datasets.get("message_history.csv")
    retriever = MessageRetriever(history if history is not None else pd.DataFrame())
    classifier = NotificationClassifier()

    rows: list[dict[str, Any]] = []
    start_time = time.time()

    for _, row in messages.iterrows():
        message = row.to_dict()
        context = build_context_for_message(message, datasets)
        evidence_ids = retriever.find_similar_messages(message)
        prediction = classifier.classify_message(message, evidence_ids, context)
        rows.append(
            {
                "message_id": message.get("message_id", ""),
                "action": prediction["action"],
                "message_type": prediction["message_type"],
                "reason": prediction["reason"],
                "confidence": prediction["confidence"],
                "evidence_message_ids": prediction["evidence_message_ids"],
            }
        )

    output_path = config.output_dir / "output.csv"
    write_output_csv(rows, output_path)

    elapsed = time.time() - start_time
    action_counts = pd.Series([row["action"] for row in rows]).value_counts().to_dict()

    print(f"Number of processed messages: {len(rows)}")
    print("Action distribution:")
    for action, count in sorted(action_counts.items()):
        print(f"  {action}: {count}")
    print(f"Time taken: {elapsed:.2f}s")


if __name__ == "__main__":
    run_pipeline()
