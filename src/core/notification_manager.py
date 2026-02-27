import logging
from src.core.notification_channel import NotificationChannel


class NotificationManager:
    """
    Manages all system notifications.
    Uses DI pattern to receive a NotificationChannel implementation.
    """

    def __init__(self, channel: NotificationChannel = None):
        self.channel = channel
        self.logger = logging.getLogger("NotificationManager")
        if not self.channel:
            self.logger.warning("NotificationChannel is not set. Notifications will be disabled.")

    def _send_payload(self, payload):
        if not self.channel:
            return False

        try:
            return self.channel.send(payload)
        except Exception as e:
            self.logger.error(f"Notification Error: {e}")
            return False

    def send_trade(self, side, symbol, price, quantity, status="SUCCESS"):
        """매매 체결 알림 (Embed 형식)"""
        color = 0x00ff00 if side.upper() == "BUY" else 0xff0000
        if status != "SUCCESS":
            color = 0x808080  # Gray for failed

        embed = {
            "title": f"Trade Notification: {status}",
            "color": color,
            "fields": [
                {"name": "Symbol", "value": f"`{symbol}`", "inline": True},
                {"name": "Side", "value": f"**{side.upper()}**", "inline": True},
                {"name": "Price", "value": f"{price}", "inline": True},
                {"name": "Quantity", "value": f"{quantity}", "inline": True},
            ],
            "footer": {"text": "BATS Trading System | Notification Manager"}
        }

        payload = {"embeds": [embed]}
        return self._send_payload(payload)

    def send_error(self, error_msg):
        """에러 발생 시 긴급 알림"""
        embed = {
            "title": "🚨 System Error Alert",
            "description": f"```{error_msg}```",
            "color": 0xff0000,
            "footer": {"text": "BATS Trading System | Notification Manager"}
        }

        payload = {"embeds": [embed]}
        return self._send_payload(payload)

    def send_status(self, title, message):
        """일반 상태 알림"""
        embed = {
            "title": title,
            "description": message,
            "color": 0x3498db,  # Blue
            "footer": {"text": "BATS Trading System | Notification Manager"}
        }
        payload = {"embeds": [embed]}
        return self._send_payload(payload)
