"""Similarity-based retrieval helpers for prior messages and evidence IDs."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.utils import clean_text


class MessageRetriever:
    """Retrieve only high-signal historical messages for evidence selection."""

    def __init__(self, history_frame: pd.DataFrame):
        self.history_frame = history_frame

    def find_similar_messages(self, message: dict[str, Any], top_k: int = 3) -> list[str]:
        """Return message IDs of similar historical messages only when the match is meaningful."""
        if self.history_frame.empty:
            return []

        current_text = clean_text(message.get("message_text", ""))
        if not current_text:
            return []

        current_tokens = set(self._tokenize(current_text))
        if not current_tokens:
            return []

        conversation_type = str(message.get("conversation_type", "") or "")
        business_id = str(message.get("business_id", "") or "")
        sender_user_id = str(message.get("sender_user_id", "") or "")

        scored_matches: list[tuple[float, str]] = []
        for _, row in self.history_frame.iterrows():
            historical_text = clean_text(row.get("message_text", ""))
            if not historical_text:
                continue

            historical_tokens = set(self._tokenize(historical_text))
            if not historical_tokens:
                continue

            overlap = len(current_tokens & historical_tokens)
            union = len(current_tokens | historical_tokens)
            if union == 0:
                continue

            score = overlap / union
            if business_id and str(row.get("business_id", "") or "") == business_id:
                score += 0.2
            if sender_user_id and str(row.get("sender_user_id", "") or "") == sender_user_id:
                score += 0.15
            if conversation_type and str(row.get("conversation_type", "") or "") == conversation_type:
                score += 0.08

            if score < 0.16:
                continue

            message_id = str(row.get("message_id", ""))
            if message_id:
                scored_matches.append((score, message_id))

        scored_matches.sort(key=lambda item: item[0], reverse=True)
        return [message_id for _, message_id in scored_matches[:top_k]]

    @staticmethod
    def _tokenize(value: str) -> list[str]:
        """Tokenize text into lowercase word-like tokens."""
        lowered = value.lower()
        return [token for token in lowered.replace("\n", " ").split() if token.isalnum()]
