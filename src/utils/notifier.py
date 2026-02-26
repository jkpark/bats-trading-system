import os
import json
from urllib import request, error
def load_env_local(file_path=".env.local"):
    """dotenv 라이브러리 없이 .env.local 로드"""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line or line.startswith("#"):
                    continue
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

# .env.local 로드 (현재 디렉토리 기준)
load_env_local()

class DiscordNotifier:
    def __init__(self, webhook_url=None):
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        if not self.webhook_url:
            print("Warning: DISCORD_WEBHOOK_URL is not set.")

    def _send_payload(self, payload):
        if not self.webhook_url:
            return False
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = request.Request(
                self.webhook_url, 
                data=data, 
                headers={'Content-Type': 'application/json', 'User-Agent': 'OpenClaw-Notifier/1.0'}
            )
            with request.urlopen(req) as response:
                return response.status == 204
        except error.HTTPError as e:
            print(f"Discord API Error: {e.code} - {e.read().decode()}")
            return False
        except Exception as e:
            print(f"Discord Notification Error: {e}")
            return False

    def send_trade_notification(self, side, symbol, price, quantity, status="SUCCESS"):
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
            "footer": {"text": "BATS Trading System | Powered by OpenClaw"}
        }
        
        payload = {"embeds": [embed]}
        return self._send_payload(payload)

    def send_error_notification(self, error_msg):
        """에러 발생 시 긴급 알림"""
        embed = {
            "title": "🚨 System Error Alert",
            "description": f"```{error_msg}```",
            "color": 0xff0000,
            "footer": {"text": "BATS Trading System | Urgent"}
        }
        
        payload = {"embeds": [embed]}
        return self._send_payload(payload)

if __name__ == "__main__":
    # 간단한 자체 테스트 (환경 변수 로드 확인용)
    notifier = DiscordNotifier()
    if notifier.webhook_url:
        print(f"Webhook URL found: {notifier.webhook_url[:15]}...")
    else:
        print("Webhook URL NOT found.")
