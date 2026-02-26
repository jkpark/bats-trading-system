import sys
import os

# src 폴더를 경로에 추가 (직접 실행 시 대비)
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from utils.notifier import DiscordNotifier

def main():
    # .env.local이 있는 루트 디렉토리로 이동하여 실행
    os.chdir(os.path.join(os.path.dirname(__file__), '..'))
    
    notifier = DiscordNotifier()
    
    # 1. 매매 성공 테스트 (Buy)
    print("Testing Buy Notification...")
    res = notifier.send_trade_notification("BUY", "BTCUSDT", 65432.10, 0.001)
    print(f"Result: {res}")
    
    # 2. 매매 성공 테스트 (Sell)
    print("Testing Sell Notification...")
    res = notifier.send_trade_notification("SELL", "ETHUSDT", 3456.78, 0.1)
    print(f"Result: {res}")

    # 3. 에러 알림 테스트
    print("Testing Error Notification...")
    res = notifier.send_error_notification("Sample error message for testing notification system.")
    print(f"Result: {res}")

if __name__ == "__main__":
    main()
