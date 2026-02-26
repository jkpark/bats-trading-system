import pandas as pd
import numpy as np

class TechnicalAnalysisEngine:
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df
        
        # 1. True Range & N (ATR 20)
        df['h_l'] = df['high'] - df['low']
        df['h_pc'] = abs(df['high'] - df['close'].shift(1))
        df['l_pc'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
        df['N'] = df['tr'].ewm(span=20, adjust=False).mean()
        
        # 2. Donchian Channels
        df['dc_20_high'] = df['high'].shift(1).rolling(window=20).max()
        df['dc_10_low'] = df['low'].shift(1).rolling(window=10).min()
        df['dc_55_high'] = df['high'].shift(1).rolling(window=55).max()
        df['dc_20_low'] = df['low'].shift(1).rolling(window=20).min()
        
        # 3. Trend Filter (EMA 200)
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        return df

class RiskManager:
    def calculate_unit_size(self, balance: float, n_value: float, price: float) -> float:
        if n_value == 0: return 0.0
        # Formula: (Balance * 0.01) / (N * Price_per_point)
        # Assuming Dollars per Point is 1 for crypto
        unit_size = (balance * 0.01) / n_value
        return round(unit_size, 6)

    def can_entry(self, current_heat: float, max_heat: float) -> bool:
        return current_heat < max_heat

class BinanceExecutionEngine:
    def __init__(self, client):
        self.client = client

    def execute_order(self, symbol: str, side: str, quantity: float):
        try:
            if side == "BUY":
                order = self.client.create_order(
                    symbol=symbol,
                    side='BUY',
                    type='MARKET',
                    quantity=quantity
                )
            elif side == "SELL":
                # For SELL, if quantity is 0, we sell the entire balance of the base asset
                if quantity == 0:
                    base_asset = symbol.replace("USDT", "") # Simple heuristic
                    balance = self.client.get_asset_balance(asset=base_asset)
                    quantity = float(balance['free'])
                
                if quantity > 0:
                    order = self.client.create_order(
                        symbol=symbol,
                        side='SELL',
                        type='MARKET',
                        quantity=quantity
                    )
            return True
        except Exception as e:
            print(f"Order Execution Failed: {e}")
            return False
