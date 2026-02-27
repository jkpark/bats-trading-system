from abc import ABC, abstractmethod


class NotificationChannel(ABC):
    """
    Abstract base class for notification channels.
    Implementations handle sending messages to specific platforms (Discord, Slack, etc.)
    """

    @abstractmethod
    def send(self, payload: dict) -> bool:
        """메시지 페이로드를 전송한다.

        Args:
            payload: 전송할 메시지 데이터 (dict)

        Returns:
            bool: 전송 성공 여부
        """
        pass
