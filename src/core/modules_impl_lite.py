from src.core.interfaces import SignalManagerInterface
import pandas as pd
import numpy as np

class TechnicalAnalysisEngine:
    def calculate_indicators(self, data):
        """
        Input: List of dicts or pandas DataFrame
        Calculates: N (ATR-20), Donchian 20/55/90/10/20/45, EMA-200, ADX-14
        """
        if data is None:
            return pd.DataFrame()
            
        if not isinstance(data, pd.DataFrame):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        if df.empty:
            return df

        # 1. True Range & N (ATR-20)
        # N = (19 * previous N + current TR) / 20
        high = df['high']
        low = df['low']
        close_prev = df['close'].shift(1)
        
        tr = pd.concat([
            high - low,
            (high - close_prev).abs(),
            (low - close_prev).abs()
        ], axis=1).max(axis=1)
        
        df['tr'] = tr
        # Initial N is simple average of TR
        df['N'] = tr.rolling(window=20).mean()
        
        # 2. ADX-14
        up_move = high.diff()
        down_move = low.shift(1) - low
        
        dm_plus = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        dm_minus = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        # Wilders Smoothing
        def wilders_smoothing(series, period):
            return series.ewm(alpha=1/period, adjust=False).mean()

        smooth_tr = wilders_smoothing(tr, 14)
        smooth_dm_plus = wilders_smoothing(pd.Series(dm_plus), 14)
        smooth_dm_minus = wilders_smoothing(pd.Series(dm_minus), 14)
        
        di_plus = 100 * (smooth_dm_plus / smooth_tr)
        di_minus = 100 * (smooth_dm_minus / smooth_tr)
        dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus)
        df['ADX'] = wilders_smoothing(dx, 14)

        # 3. Donchian Channels (Shifted to exclude current bar)
        df['dc_20_high'] = high.shift(1).rolling(window=20).max()
        df['dc_55_high'] = high.shift(1).rolling(window=55).max()
        df['dc_90_high'] = high.shift(1).rolling(window=90).max()
        
        df['dc_10_low'] = low.shift(1).rolling(window=10).min()
        df['dc_20_low'] = low.shift(1).rolling(window=20).min()
        df['dc_45_low'] = low.shift(1).rolling(window=45).min()

        # 4. EMA-200
        df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()

        return df


class RiskManager:
    def calculate_unit_size(self, balance, n_value, price, n_avg_20=None):
        if n_value == 0 or np.isnan(n_value): return 0.0
        unit_size = (balance * 0.01) / n_value

        # Volatility Cap: Reduce by 50% if current N is 1.5x of 20-day average N
        if n_avg_20 and n_value > (n_avg_20 * 1.5):
            unit_size *= 0.5

        return round(float(unit_size), 6)

    def calculate_unit_size_with_mdd(self, current_equity, n_value, price, peak_equity=None):
        """
        MDD Risk Reduction (TECHNICAL_DESIGN 2.4):
        For every 10% drawdown from peak, reduce virtual equity by 20%.
        """
        if n_value == 0 or np.isnan(n_value): return 0.0

        virtual_equity = current_equity
        if peak_equity and peak_equity > 0:
            drawdown_pct = (peak_equity - current_equity) / peak_equity
            reduction_steps = int(drawdown_pct / 0.10)
            for _ in range(reduction_steps):
                virtual_equity *= 0.8

        unit_size = (virtual_equity * 0.01) / n_value
        return round(float(unit_size), 6)

    def can_entry(self, current_heat, max_heat):
        return current_heat < max_heat
