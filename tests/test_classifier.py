import unittest

from src.classifier import NotificationClassifier


class NotificationClassifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.classifier = NotificationClassifier()

    def test_otp_message_is_routed_as_urgent_notify(self) -> None:
        prediction = self.classifier.classify_message(
            {"message_text": "Please verify your OTP now to keep the account active."},
            evidence_message_ids=["msg_1"],
            context={"user_profile": {"notifications_dismissed_30d": 5}},
        )
        self.assertEqual(prediction["action"], "notify")
        self.assertEqual(prediction["message_type"], "urgent")
        self.assertIn("immediate attention", prediction["reason"].lower())
        self.assertGreaterEqual(prediction["confidence"], 0.9)
        self.assertEqual(prediction["evidence_message_ids"], "msg_1")

    def test_payment_message_is_routed_as_payment_notify(self) -> None:
        prediction = self.classifier.classify_message(
            {"message_text": "Payment due for your EMI is tomorrow."},
            context={"user_profile": {"notifications_dismissed_30d": 12}},
        )
        self.assertEqual(prediction["action"], "notify")
        self.assertEqual(prediction["message_type"], "payment")
        self.assertIn("payment reminder", prediction["reason"].lower())

    def test_promotion_message_uses_allowed_message_type(self) -> None:
        prediction = self.classifier.classify_message(
            {"message_text": "Huge discount on your favorite items today."},
            context={"user_profile": {"notifications_dismissed_30d": 2}},
        )
        self.assertEqual(prediction["message_type"], "promotion")
        self.assertEqual(prediction["action"], "digest")

    def test_spam_message_is_moved_to_mute(self) -> None:
        prediction = self.classifier.classify_message(
            {"message_text": "Reply STOP to unsubscribe from marketing messages now."},
            context={"user_profile": {"notifications_dismissed_30d": 2}},
        )
        self.assertEqual(prediction["action"], "mute")
        self.assertEqual(prediction["message_type"], "spam")


if __name__ == "__main__":
    unittest.main()
