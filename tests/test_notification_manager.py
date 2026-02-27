import unittest
from unittest.mock import patch, MagicMock
from src.core.notification_manager import NotificationManager

class TestNotificationManager(unittest.TestCase):
    def setUp(self):
        self.webhook_url = "https://discord.com/api/webhooks/test"
        self.manager = NotificationManager(webhook_url=self.webhook_url)

    @patch('urllib.request.urlopen')
    def test_send_trade_success(self, mock_urlopen):
        # Mock response object
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = self.manager.send_trade("BUY", "BTCUSDT", 50000, 0.1)
        
        self.assertTrue(result)
        self.assertTrue(mock_urlopen.called)

    @patch('urllib.request.urlopen')
    def test_send_error_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = self.manager.send_error("Test Error Message")
        
        self.assertTrue(result)
        self.assertTrue(mock_urlopen.called)

    def test_no_webhook_url(self):
        manager = NotificationManager(webhook_url=None)
        with patch.dict('os.environ', {}, clear=True):
             manager.webhook_url = None
             result = manager.send_status("Title", "Message")
             self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
