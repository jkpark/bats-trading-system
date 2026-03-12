import os
import sys
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

def get_bats_report():
    bats_dir = "/Users/jkpark/.openclaw/workspace-jeff/bats-trading-system"
    os.chdir(bats_dir)
    sys.path.append(os.path.join(bats_dir, "src"))

    load_dotenv(dotenv_path=".env")
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    testnet = os.getenv('BINANCE_TESTNET', 'True') == 'True'

    client = Client(api_key, api_secret, testnet=testnet)

    try:
        # 1. 핑 체크 (연결 확인)
        client.ping()

        # 2. 현재가
        ticker = client.get_symbol_ticker(symbol='BTCUSDT')
        current_price = float(ticker['price'])

        # 3. 계정 정보 & 잔고
        account = client.get_account()
        balances = {b['asset']: float(b['free']) for b in account['balances'] if float(b['free']) > 0}
        
        btc_balance = balances.get('BTC', 0.0)
        usdt_balance = balances.get('USDT', 0.0)
        
        # 4. 최근 24시간 체결 내역
        trades = client.get_my_trades(symbol='BTCUSDT', limit=5)

        print(f"### BATS 실시간 거래 현황 보고 (Testnet: {testnet})")
        print(f"- **현재 시각**: {os.popen('date').read().strip()}")
        print(f"- **BTCUSDT 현재가**: ${current_price:,.2f}")
        print(f"- **지갑 잔고**: BTC: {btc_balance:.6f} / USDT: {usdt_balance:,.2f}")
        
        if btc_balance > 0.0001:
            print(f"- **포지션**: LONG 유지 중 (대략 ${btc_balance * current_price:,.2f} 상당)")
        else:
            print("- **포지션**: 무포지션 (Cash)")

        print("\n### 최근 체결 내역 (Last 5)")
        if not trades:
            print("- 최근 체결 내역 없음 (또는 24시간 이내 거래 없음)")
        for t in trades:
            side = "BUY" if t['isBuyer'] else "SELL"
            print(f"- [{side}] {t['qty']} BTC @ ${float(t['price']):,.2f} (Fee: {t['commission']} {t['commissionAsset']})")

    except BinanceAPIException as e:
        print(f"Binance API Error: {e.status_code} {e.message}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_bats_report()
