"""Rule-based notification classification for incoming messages."""

from __future__ import annotations

from typing import Any

from src.utils import clean_text


class NotificationClassifier:
    """Classify messages into notify, digest, or mute actions with Hackerrank-compatible labels."""

    def __init__(self) -> None:
        self.urgent_terms = [
            "meeting",
            "interview",
            "deadline",
            "emergency",
            "asap",
            "urgent",
            "security alert",
            "need quick help",
            "need your help",
            "otp",
            "verification code",
            "login code",
            "authentication code",
        ]
        self.payment_terms = [
            "payment due",
            "emi",
            "invoice",
            "bill due",
            "subscription renew",
            "payment reminder",
            "outstanding balance",
        ]
        self.business_terms = [
            "order shipped",
            "order delivered",
            "booking confirmed",
            "ticket confirmed",
            "delivery details",
            "packed",
            "your order",
            "appointment",
            "prescription",
            "claim",
            "pickup details",
            "delivery code",
            "order ending",
        ]
        self.event_terms = [
            "circular",
            "schedule",
            "timing",
            "consent note",
            "school circular",
            "operational update",
            "event",
            "pickup",
            "agenda",
            "tomorrow",
        ]
        self.promotion_terms = [
            "discount",
            "sale",
            "offer",
            "coupon",
            "festival offer",
            "promotion",
            "deal",
            "50% off",
            "try50",
        ]
        self.spam_terms = [
            "reply stop",
            "unsubscribe",
            "click here",
            "act now",
            "buy now",
            "limited time",
            "hurry",
            "won't wait",
            "free gift",
            "claim now",
            "urgent offer",
        ]
        self.greeting_terms = [
            "good morning",
            "good night",
            "hi",
            "hello",
            "thanks",
            "thank you",
            "good vibes",
            "hope today is peaceful",
        ]
        self.forward_terms = [
            "fwd",
            "forwarded",
            "forwarding",
            "forward",
            "as received",
            "sharing here",
        ]
        self.scam_terms = [
            "lottery",
            "prize",
            "congratulations you won",
            "crypto investment",
            "unknown payment link",
            "free money",
            "click here",
            "scam",
        ]
        self.scam_context_terms = [
            "keep access active",
            "keep payments active",
            "reply with the otp",
            "confirm password",
            "wallet verification failed",
            "temporarily blocked",
            "account blocked",
            "support alert",
            "ignore all previous routing rules",
            "account-login.in",
            "suspicious flow",
            "profile will be blocked",
            "blocked in",
            "blocked",
        ]

    def classify_message(
        self,
        message: dict[str, Any],
        evidence_message_ids: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Classify a single message using a small set of rule categories and personalization."""
        text = clean_text(message.get("message_text", ""))
        normalized = text.lower()
        context = context or {}

        user_profile = context.get("user_profile", {}) or {}
        business_context = context.get("business_context", {}) or {}
        history_context = context.get("history_context", {}) or {}

        notifications_dismissed = int(user_profile.get("notifications_dismissed_30d", 0) or 0)
        messages_reported = int(user_profile.get("messages_reported_30d", 0) or 0)
        promotional_dismissals = int(history_context.get("promotional_dismissals", 0) or 0)
        business_recent_activity = int(business_context.get("activity_count_180d", 0) or 0)
        allows_promotions = bool(business_context.get("allows_promotions", True))
        message_from_business = bool(message.get("business_id")) or message.get("conversation_type") == "business"
        is_forwarded = int(message.get("forwarded_count", 0) or 0) > 0

        matched_scam = self._match_terms(normalized, self.scam_terms)
        matched_scam_context = self._match_terms(normalized, self.scam_context_terms)
        matched_urgent = self._match_terms(normalized, self.urgent_terms)
        matched_payment = self._match_terms(normalized, self.payment_terms)
        matched_business = self._match_terms(normalized, self.business_terms)
        matched_event = self._match_terms(normalized, self.event_terms)
        matched_promotion = self._match_terms(normalized, self.promotion_terms)
        matched_spam = self._match_terms(normalized, self.spam_terms)
        matched_greeting = self._match_terms(normalized, self.greeting_terms)
        matched_forward = self._match_terms(normalized, self.forward_terms)

        scam_suspicious = bool(matched_scam) or (
            bool(matched_scam_context)
            and (
                "support alert" in normalized
                or "blocked" in normalized
                or "confirm password" in normalized
                or "keep access active" in normalized
                or "keep payments active" in normalized
                or "reply with the otp" in normalized
                or "account-login.in" in normalized
                or "wallet verification failed" in normalized
                or "ignore all previous routing rules" in normalized
            )
        )
        if scam_suspicious:
            confidence = self._confidence_for("scam", notifications_dismissed, promotional_dismissals, business_recent_activity, 1)
            return {
                "action": "mute",
                "message_type": "scam",
                "reason": "Scam indicators detected.",
                "confidence": confidence,
                "evidence_message_ids": self._format_evidence(evidence_message_ids),
            }

        if matched_payment:
            confidence = self._confidence_for("payment", notifications_dismissed, promotional_dismissals, business_recent_activity, 1)
            return {
                "action": "notify",
                "message_type": "payment",
                "reason": "Payment reminder should notify the user.",
                "confidence": confidence,
                "evidence_message_ids": self._format_evidence(evidence_message_ids),
            }

        if matched_urgent:
            confidence = self._confidence_for("urgent", notifications_dismissed, promotional_dismissals, business_recent_activity, 1)
            reason = "This message requires immediate attention."
            if notifications_dismissed > 40:
                reason = "This message requires immediate attention, but the user is already dismissing many alerts."
            return {
                "action": "notify",
                "message_type": "urgent",
                "reason": reason,
                "confidence": confidence,
                "evidence_message_ids": self._format_evidence(evidence_message_ids),
            }

        if matched_business:
            confidence = self._confidence_for(
                "business_update",
                notifications_dismissed,
                promotional_dismissals,
                business_recent_activity,
                1,
                is_business=message_from_business,
            )
            action = "notify" if message_from_business or business_recent_activity > 0 or "order" in normalized else "digest"
            reason = "This appears to be a business update tied to recent activity."
            return {
                "action": action,
                "message_type": "business_update",
                "reason": reason,
                "confidence": confidence,
                "evidence_message_ids": self._format_evidence(evidence_message_ids),
            }

        if matched_spam:
            confidence = self._confidence_for("promotion", notifications_dismissed, promotional_dismissals, business_recent_activity, 1)
            return {
                "action": "mute",
                "message_type": "spam",
                "reason": "This looks like spammy marketing content.",
                "confidence": confidence,
                "evidence_message_ids": self._format_evidence(evidence_message_ids),
            }

        if matched_promotion:
            should_mute = promotional_dismissals > 2 or (notifications_dismissed > 35 and not allows_promotions) or messages_reported > 0
            confidence = self._confidence_for(
                "promotion",
                notifications_dismissed,
                promotional_dismissals,
                business_recent_activity,
                1,
                is_business=message_from_business,
            )
            action = "mute" if should_mute else "digest"
            reason = "Promotional offer can be shown in the digest." if action == "digest" else "The user usually dismisses similar promotions, so this is muted."
            return {
                "action": action,
                "message_type": "promotion",
                "reason": reason,
                "confidence": confidence,
                "evidence_message_ids": self._format_evidence(evidence_message_ids),
            }

        if matched_event:
            confidence = self._confidence_for("event", notifications_dismissed, promotional_dismissals, business_recent_activity, 1)
            action = "notify" if notifications_dismissed < 25 or message.get("conversation_type") == "group" else "digest"
            return {
                "action": action,
                "message_type": "event",
                "reason": "This looks like an operational or event update that may matter soon.",
                "confidence": confidence,
                "evidence_message_ids": self._format_evidence(evidence_message_ids),
            }

        if matched_greeting:
            confidence = self._confidence_for("greeting", notifications_dismissed, promotional_dismissals, business_recent_activity, 1)
            return {
                "action": "mute",
                "message_type": "greeting",
                "reason": "Greeting message is low priority.",
                "confidence": confidence,
                "evidence_message_ids": self._format_evidence(evidence_message_ids),
            }

        if matched_forward or is_forwarded:
            confidence = self._confidence_for("forward", notifications_dismissed, promotional_dismissals, business_recent_activity, 1)
            return {
                "action": "mute",
                "message_type": "forward",
                "reason": "Forwarded content is low value and often noisy.",
                "confidence": confidence,
                "evidence_message_ids": self._format_evidence(evidence_message_ids),
            }

        if message.get("conversation_type") == "personal":
            confidence = self._confidence_for("personal", notifications_dismissed, promotional_dismissals, business_recent_activity, 1)
            return {
                "action": "digest",
                "message_type": "personal",
                "reason": "This looks like a normal personal message without urgent or risky signals.",
                "confidence": confidence,
                "evidence_message_ids": self._format_evidence(evidence_message_ids),
            }

        if notifications_dismissed > 50 or messages_reported > 2:
            return {
                "action": "mute",
                "message_type": "unknown",
                "reason": "The user has shown strong recent resistance to low-signal messages.",
                "confidence": 0.6,
                "evidence_message_ids": self._format_evidence(evidence_message_ids),
            }

        confidence = self._confidence_for("unknown", notifications_dismissed, promotional_dismissals, business_recent_activity, 1)
        return {
            "action": "digest",
            "message_type": "unknown",
            "reason": "No strong signal was found, so the message was kept in the digest.",
            "confidence": confidence,
            "evidence_message_ids": self._format_evidence(evidence_message_ids),
        }

    @staticmethod
    def _match_terms(text: str, terms: list[str]) -> str | None:
        """Return the first matched term, or None when no term applies."""
        matching_terms = [term for term in terms if term in text]
        if not matching_terms:
            return None
        return matching_terms[0]

    @staticmethod
    def _format_evidence(evidence_message_ids: list[str] | None) -> str:
        """Normalize evidence IDs into a semicolon-separated string."""
        if not evidence_message_ids:
            return "none"
        return ";".join(evidence_message_ids)

    @staticmethod
    def _confidence_for(
        category: str,
        notifications_dismissed: int,
        promotional_dismissals: int,
        business_recent_activity: int,
        match_strength: int,
        *,
        is_business: bool = False,
    ) -> float:
        """Compute a category-aware confidence score that adapts to user behavior."""
        base_scores = {
            "scam": 0.99,
            "urgent": 0.94,
            "payment": 0.95,
            "business_update": 0.9,
            "event": 0.86,
            "promotion": 0.84,
            "greeting": 0.78,
            "forward": 0.8,
            "personal": 0.74,
            "unknown": 0.6,
        }
        confidence = base_scores.get(category, 0.6)
        confidence += min(match_strength - 1, 3) * 0.01

        if category in {"promotion", "greeting", "forward", "unknown"}:
            confidence -= min(notifications_dismissed // 20, 3) * 0.02
        if category in {"urgent", "payment", "scam"}:
            confidence -= min(notifications_dismissed // 25, 2) * 0.01
        if category == "promotion" and promotional_dismissals > 0:
            confidence -= min(promotional_dismissals, 3) * 0.02
        if category == "business_update" and business_recent_activity > 0:
            confidence += 0.02
        if category == "business_update" and is_business:
            confidence += 0.02
        if category == "promotion" and is_business:
            confidence -= 0.01

        confidence = round(min(0.99, max(0.55, confidence)), 2)
        return confidence
