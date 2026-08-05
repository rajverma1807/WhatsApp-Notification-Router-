"""Prompt constructors for future OpenAI and RAG-based enhancements."""

from __future__ import annotations

from typing import Any


def build_classification_prompt(message: dict[str, Any], context: dict[str, Any] | None = None) -> str:
    """Create a prompt template for classification tasks."""
    context = context or {}
    return (
        "You are routing a WhatsApp notification. "
        f"Message: {message.get('message_text', '')}\n"
        f"User context: {context.get('user_profile', {})}\n"
        "Return JSON with action, message_type, reason, confidence, evidence_message_ids."
    )


def build_retrieval_prompt(message: dict[str, Any]) -> str:
    """Create a prompt template for retrieval or similarity tasks."""
    return (
        "Find the most relevant prior messages for this WhatsApp message.\n"
        f"Message: {message.get('message_text', '')}"
    )
