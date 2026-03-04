class TurtleSignalManager:
    """
    Improved Turtle Trading Signal Generator:
    - S1: 20-day breakout (with Skip Rule) -> Optional
    - S2: 55-day breakout -> Optional
    - S3: 90-day breakout (New Default)
    - Pyramiding: +0.5N from last entry, max 4 units
    - Hard Stop: last entry - 5N (Improved from 2N)
    - Trailing Stop: S1 (10), S2 (20), S3 (45 - Improved)
    - Trend Filter: Price > 200 EMA
    - Regime Filter: ADX > 25 (Improved)
    """
    def __init__(self, use_s1=False, use_s2=False, use_s3=True, 
                 adx_filter_threshold=25.0, stop_n_multiplier=5.0):
        self.use_s1 = use_s1
        self.use_s2 = use_s2
        self.use_s3 = use_s3
        self.adx_filter_threshold = adx_filter_threshold
        self.stop_n_multiplier = stop_n_multiplier

    def generate_signal(self, df, current_price, state):
        units_held = state.get('units_held', 0)
        system_mode = state.get('system_mode', 'S3')
        entry_prices = state.get('entry_prices', [])
        current_n = state.get('current_n', 0)

        # Helper to get indicator values regardless of df type
        def get_val(key):
            if hasattr(df, 'iloc'): # Pandas
                return df[key].iloc[-1]
            else: # List of dicts
                return df[-1][key]

        # ── 1. Exit Logic (position open) ──
        if units_held > 0:
            # 1a. Hard Stop: last entry - 5N (Improved priority)
            if entry_prices and current_n > 0:
                last_entry = entry_prices[-1]
                hard_stop = last_entry - (self.stop_n_multiplier * current_n)
                if current_price < hard_stop:
                    return "EXIT"

            # 1b. Trailing Stop (system-dependent)
            if system_mode == 'S3':
                exit_threshold = get_val('dc_45_low')
            elif system_mode == 'S2':
                exit_threshold = get_val('dc_20_low')
            else:  # S1 default
                exit_threshold = get_val('dc_10_low')

            if current_price < exit_threshold:
                return "EXIT"

            # 1c. Pyramiding: +0.5N from last entry, max 4 units
            if entry_prices and current_n > 0 and units_held < 4:
                last_entry = entry_prices[-1]
                pyramid_threshold = last_entry + (0.5 * current_n)
                if current_price > pyramid_threshold:
                    return "PYRAMID"

            return "HOLD"

        # ── 2. Entry Logic (no position) ──
        # 2a. Regime Filter: ADX
        adx = get_val('ADX')
        if adx < self.adx_filter_threshold:
            return "HOLD"

        # 2b. Trend Filter: EMA 200
        ema_200 = get_val('ema_200')
        if ema_200 and current_price < ema_200:
            return "HOLD"

        # S3 Entry (90-day, highest priority)
        if self.use_s3 and current_price > get_val('dc_90_high'):
            state['system_mode'] = 'S3'
            return "BUY"

        # S2 Entry (always accepted)
        if self.use_s2 and current_price > get_val('dc_55_high'):
            state['system_mode'] = 'S2'
            return "BUY"

        # S1 Entry (with Skip Rule)
        if self.use_s1 and current_price > get_val('dc_20_high'):
            if state.get('last_trade_result') == 'win':
                return "HOLD"
            state['system_mode'] = 'S1'
            return "BUY"

        return "HOLD"

class AdvancedTurtleManager(TurtleSignalManager):
    """
    Advanced Turtle Trading Signal Generator:
    - Inherits from TurtleSignalManager
    - ADX Filter Threshold: 30 (Default)
    - Hard Stop Multiplier: 3.0 (Default)
    - Additional Filter: RSI(14) > 55
    - Additional Filter: Volume > 20-day Volume SMA
    """
    def __init__(self, use_s1=False, use_s2=False, use_s3=True, 
                 adx_filter_threshold=30.0, stop_n_multiplier=3.0, 
                 rsi_threshold=55.0, volume_filter=True):
        super().__init__(use_s1, use_s2, use_s3, adx_filter_threshold, stop_n_multiplier)
        self.rsi_threshold = rsi_threshold
        self.volume_filter = volume_filter

    def generate_signal(self, df, current_price, state):
        # 1. Exit Logic (Inherit)
        units_held = state.get('units_held', 0)
        if units_held > 0:
            return super().generate_signal(df, current_price, state)

        # 2. Entry Logic (Extended)
        def get_val(key):
            if hasattr(df, 'iloc'): # Pandas
                return df[key].iloc[-1]
            else: # List of dicts
                return df[-1][key]

        # 2c. Additional Filter: RSI
        rsi = get_val('rsi_14')
        if rsi < self.rsi_threshold:
            return "HOLD"

        # 2d. Additional Filter: Volume
        if self.volume_filter:
            volume = get_val('volume')
            vol_sma = get_val('vol_sma_20')
            if volume < vol_sma:
                return "HOLD"

        # 3. Call Base Signal for ADX, EMA, Breakout
        return super().generate_signal(df, current_price, state)
