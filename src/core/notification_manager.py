import os
import json
import logging
from urllib import request, error

class NotificationManager:
    """
    Manages all system notifications (Discord, etc.)
    """
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.logger = logging.getLogger("NotificationManager")
        if not self.webhook_url:
            self.logger.warning("DISCORD_WEBHOOK_URL is not set. Notifications will be disabled.")

    def _send_payload(self, payload):
        if not self.webhook_url:
            return False
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = request.Request(
                self.webhook_url, 
                data=data, 
                headers={'Content-Type': 'application/json', 'User-Agent': 'BATS-Notifier/1.0'}
            )
            with request.urlopen(req) as response:
                return response.status == 204
        except error.HTTPError as e:
            self.logger.error(f"Discord API Error: {e.code} - {e.read().decode()}")
            return False
        except Exception as e:
            self.logger.error(f"Discord Notification Error: {e}")
            return False

    def send_trade(self, side, symbol, price, quantity, status="SUCCESS"):
        """매매 체결 알림 (Embed 형식)"""
        color = 0x00ff00 if side.upper() == "BUY" else 0xff0000
        if status != "SUCCESS":
            color = 0x808080 # Gray for failed
            
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
            "color": 0x3498db, # Blue
            "footer": {"text": "BATS Trading System | Notification Manager"}
        }
        payload = {"embeds": [embed]}
        return self._send_payload(payload)
