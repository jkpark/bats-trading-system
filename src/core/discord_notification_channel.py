import json
import logging
from urllib import request, error

from src.core.notification_channel import NotificationChannel


class DiscordNotificationChannel(NotificationChannel):
    """
    Discord Webhook을 통해 메시지를 전송하는 NotificationChannel 구현체.
    """

    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        self.logger = logging.getLogger("DiscordNotificationChannel")
        if not self.webhook_url:
            self.logger.warning("Discord webhook_url is not set. Discord notifications will be disabled.")

    def send(self, payload: dict) -> bool:
        """Discord Webhook API로 페이로드를 전송한다.

        Args:
            payload: Discord Embed 형식의 메시지 데이터

        Returns:
            bool: 전송 성공 여부 (HTTP 204 시 True)
        """
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
