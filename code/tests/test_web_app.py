import unittest

from web_app import create_app


class WebAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app()
        self.client = self.app.test_client()

    def test_home_page_renders(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("WhatsApp Notification Router", response.get_data(as_text=True))

    def test_classification_endpoint_returns_prediction(self) -> None:
        response = self.client.post(
            "/classify",
            data={"message_text": "Meeting starts at 10 AM. Please join ASAP."},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("notify", response.get_data(as_text=True).lower())


if __name__ == "__main__":
    unittest.main()
