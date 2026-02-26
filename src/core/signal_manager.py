from src.core.interfaces import SignalManagerInterface

class TurtleSignalManager(SignalManagerInterface):
    """
    Turtle Trading Signal Generator:
    - S1: 20-day breakout (with Skip Rule)
    - S2: 55-day breakout (always accepted)
    - Pyramiding: +0.5N from last entry, max 4 units
    - Hard Stop: last entry - 2N
    - Trailing Stop: S1 → 10-day low, S2 → 20-day low
    - Trend Filter: Price > 200 EMA
    """
    def __init__(self, use_s1=True, use_s2=True):
        self.use_s1 = use_s1
        self.use_s2 = use_s2

    def generate_signal(self, df, current_price, state):
        units_held = state.get('units_held', 0)
        system_mode = state.get('system_mode', 'S1')
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
            # 1a. Hard Stop: last entry - 2N (highest priority)
            if entry_prices and current_n > 0:
                last_entry = entry_prices[-1]
                hard_stop = last_entry - (2 * current_n)
                if current_price < hard_stop:
                    return "EXIT"

            # 1b. Trailing Stop (system-dependent)
            if system_mode == 'S2':
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
        # Trend Filter
        ema_200 = get_val('ema_200')
        if ema_200 and current_price < ema_200:
            return "HOLD"

        # S2 Entry (always accepted, checked first for priority)
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
