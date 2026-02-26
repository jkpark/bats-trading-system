import yaml
from src.core.exchange_provider import ExchangeProvider

def verify_data_fetch():
    try:
        # Load config to see test_mode
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
        test_mode = config.get('system', {}).get('test_mode', False)
        
        print(f"Initializing ExchangeProvider (testnet={test_mode})...")
        exchange = ExchangeProvider(testnet=test_mode)
        
        symbol = "BTCUSDT"
        interval = "1h"
        print(f"Fetching last 5 candles for {symbol} {interval}...")
        
        df = exchange.get_market_data(symbol, interval, limit=5)
        
        if df is not None and not df.empty:
            print("✅ Market data fetched successfully!")
            print(df)
            return True
        else:
            print("❌ Failed to fetch market data.")
            return False
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    verify_data_fetch()
