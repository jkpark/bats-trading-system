import pandas as pd
import numpy as np

class TechnicalAnalysisEngine:
    def calculate_indicators(self, data) -> pd.DataFrame:
        if data is None:
            return pd.DataFrame()
            
        if not isinstance(data, pd.DataFrame):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        if df.empty:
            return df
        
        # 1. True Range & N (ATR 20)
        df['h_l'] = df['high'] - df['low']
        df['h_pc'] = abs(df['high'] - df['close'].shift(1))
        df['l_pc'] = abs(df['low'] - df['close'].shift(1))
        df['tr'] = df[['h_l', 'h_pc', 'l_pc']].max(axis=1)
        df['N'] = df['tr'].ewm(span=20, adjust=False).mean()
        
        # 2. ADX-14 (Required by SignalManager)
        high = df['high']
        low = df['low']
        tr = df['tr']
        up_move = high.diff()
        down_move = low.shift(1) - low
        
        dm_plus = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        dm_minus = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        def wilders_smoothing(series, period):
            return series.ewm(alpha=1/period, adjust=False).mean()

        smooth_tr = wilders_smoothing(tr, 14)
        smooth_dm_plus = wilders_smoothing(pd.Series(dm_plus), 14)
        smooth_dm_minus = wilders_smoothing(pd.Series(dm_minus), 14)
        
        di_plus = 100 * (smooth_dm_plus / smooth_tr)
        di_minus = 100 * (smooth_dm_minus / smooth_tr)
        dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus)
        df['ADX'] = wilders_smoothing(dx, 14)

        # 3. Donchian Channels
        df['dc_90_high'] = df['high'].shift(1).rolling(window=90).max()
        df['dc_55_high'] = df['high'].shift(1).rolling(window=55).max()
        df['dc_20_high'] = df['high'].shift(1).rolling(window=20).max()
        
        df['dc_45_low'] = df['low'].shift(1).rolling(window=45).min()
        df['dc_20_low'] = df['low'].shift(1).rolling(window=20).min()
        df['dc_10_low'] = df['low'].shift(1).rolling(window=10).min()
        
        # 4. Trend Filter (EMA 200)
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()

        # 5. RSI(14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))

        # 6. Volume Filter (SMA 20)
        df['vol_sma_20'] = df['volume'].rolling(window=20).mean()
        
        return df

class RiskManager:
    def calculate_unit_size(self, balance: float, n_value: float, price: float, n_avg_20=None) -> float:
        if n_value == 0 or np.isnan(n_value): return 0.0
        # Unit size is balance * 1% / N
        unit_size = (balance * 0.01) / n_value

        # Volatility Cap: Reduce by 50% if current N is 1.5x of 20-day average N
        if n_avg_20 and n_value > (n_avg_20 * 1.5):
            unit_size *= 0.5

        return round(float(unit_size), 6)

    def calculate_total_heat(self, symbols_state: dict, unit_risk_percent: float = 0.01) -> float:
        """
        Calculate total portfolio heat (Σ units_held * unit_risk_percent).
        """
        total_units = sum(s.get('units_held', 0) for s in symbols_state.values())
        return total_units * unit_risk_percent

    def can_entry(self, current_heat: float, max_heat: float, new_unit_risk: float = 0.01) -> bool:
        """
        Check if adding a new unit will keep total heat within limits.
        """
        return (current_heat + new_unit_risk) <= max_heat

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
                if quantity == 0:
                    base_asset = symbol.replace("USDT", "")
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
