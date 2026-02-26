import os
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

class ExchangeProvider:
    """
    Binance API Wrapper for Market Data and Account Info.
    """
    def __init__(self, testnet=True):
        load_dotenv()
        api_key = os.getenv('BINANCE_API_KEY')
        api_secret = os.getenv('BINANCE_API_SECRET')
        
        self.client = Client(api_key, api_secret, testnet=testnet)
        
    def get_market_data(self, symbol, interval, limit=100):
        """
        Fetch OHLCV data and return as a pandas DataFrame.
        """
        try:
            klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'
            ])
            
            # Type Conversion
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        except BinanceAPIException as e:
            print(f"Error fetching market data: {e}")
            return None

    def get_realtime_price(self, symbol):
        """
        Fetch the latest price for a symbol.
        """
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            print(f"Error fetching realtime price: {e}")
            return None

    def get_asset_balance(self, asset):
        """
        Fetch available balance for a specific asset.
        """
        try:
            account = self.client.get_account()
            for balance in account['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            return 0.0
        except BinanceAPIException as e:
            print(f"Error fetching balance: {e}")
            return 0.0

if __name__ == "__main__":
    # Quick test if keys are present
    provider = ExchangeProvider(testnet=True)
    print("Provider initialized.")
