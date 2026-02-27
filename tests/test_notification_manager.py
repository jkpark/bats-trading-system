import unittest
from unittest.mock import patch, MagicMock
from src.core.notification_channel import NotificationChannel
from src.core.notification_manager import NotificationManager
from src.core.discord_notification_channel import DiscordNotificationChannel


class MockNotificationChannel(NotificationChannel):
    """테스트용 Mock NotificationChannel 구현체"""

    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed
        self.sent_payloads = []

    def send(self, payload: dict) -> bool:
        self.sent_payloads.append(payload)
        return self.should_succeed


class TestNotificationManager(unittest.TestCase):
    def setUp(self):
        self.mock_channel = MockNotificationChannel()
        self.manager = NotificationManager(channel=self.mock_channel)

    def test_send_trade_buy(self):
        result = self.manager.send_trade("BUY", "BTCUSDT", 50000, 0.1)

        self.assertTrue(result)
        self.assertEqual(len(self.mock_channel.sent_payloads), 1)

        payload = self.mock_channel.sent_payloads[0]
        embed = payload["embeds"][0]
        self.assertEqual(embed["color"], 0x00ff00)  # Green for BUY
        self.assertEqual(embed["title"], "Trade Notification: SUCCESS")

    def test_send_trade_sell(self):
        result = self.manager.send_trade("SELL", "BTCUSDT", 50000, 0.1)

        self.assertTrue(result)
        embed = self.mock_channel.sent_payloads[0]["embeds"][0]
        self.assertEqual(embed["color"], 0xff0000)  # Red for SELL

    def test_send_trade_failed_status(self):
        result = self.manager.send_trade("BUY", "BTCUSDT", 50000, 0.1, status="FAILED")

        self.assertTrue(result)
        embed = self.mock_channel.sent_payloads[0]["embeds"][0]
        self.assertEqual(embed["color"], 0x808080)  # Gray for failed

    def test_send_error(self):
        result = self.manager.send_error("Test Error Message")

        self.assertTrue(result)
        embed = self.mock_channel.sent_payloads[0]["embeds"][0]
        self.assertEqual(embed["title"], "🚨 System Error Alert")
        self.assertIn("Test Error Message", embed["description"])

    def test_send_status(self):
        result = self.manager.send_status("Title", "Message")

        self.assertTrue(result)
        embed = self.mock_channel.sent_payloads[0]["embeds"][0]
        self.assertEqual(embed["title"], "Title")
        self.assertEqual(embed["description"], "Message")
        self.assertEqual(embed["color"], 0x3498db)  # Blue

    def test_no_channel_set(self):
        manager = NotificationManager(channel=None)
        result = manager.send_status("Title", "Message")
        self.assertFalse(result)

    def test_channel_send_failure(self):
        fail_channel = MockNotificationChannel(should_succeed=False)
        manager = NotificationManager(channel=fail_channel)
        result = manager.send_trade("BUY", "BTCUSDT", 50000, 0.1)
        self.assertFalse(result)


class TestDiscordNotificationChannel(unittest.TestCase):
    def setUp(self):
        self.webhook_url = "https://discord.com/api/webhooks/test"
        self.channel = DiscordNotificationChannel(webhook_url=self.webhook_url)

    @patch('urllib.request.urlopen')
    def test_send_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = self.channel.send({"embeds": [{"title": "Test"}]})

        self.assertTrue(result)
        self.assertTrue(mock_urlopen.called)

    @patch('urllib.request.urlopen')
    def test_send_http_error(self, mock_urlopen):
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError(
            url=self.webhook_url, code=400, msg="Bad Request",
            hdrs=None, fp=MagicMock(read=MagicMock(return_value=b"error"))
        )

        result = self.channel.send({"embeds": [{"title": "Test"}]})
        self.assertFalse(result)

    def test_no_webhook_url(self):
        channel = DiscordNotificationChannel(webhook_url=None)
        result = channel.send({"embeds": [{"title": "Test"}]})
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
