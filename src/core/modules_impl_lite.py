class TechnicalAnalysisEngine:
    def calculate_indicators(self, data):
        """
        Input: List of dicts or pandas DataFrame
        Calculates: N (ATR-20), Donchian 20/55/10/20, EMA-200
        """
        if data is None or (hasattr(data, 'empty') and data.empty):
            return []
            
        # Convert DataFrame to list of dicts for processing
        if hasattr(data, 'to_dict'):
            data_list = data.to_dict('records')
        else:
            data_list = data
        
        results = []
        ema_200 = None

        for i, d in enumerate(data_list):
            # 1. True Range & N (ATR-20 SMA)
            tr = d['high'] - d['low']
            if i > 0:
                prev_close = data_list[i-1]['close']
                tr = max(d['high'] - d['low'],
                         abs(d['high'] - prev_close),
                         abs(d['low'] - prev_close))

            prev_trs = [r['tr'] for r in results[-19:]] + [tr]
            n_val = sum(prev_trs) / len(prev_trs)
            
            # 2. Donchian Channels (using shifted window: exclude current bar)
            # Entry channels
            window_20h = [data_list[j]['high'] for j in range(max(0, i-20), i)]
            window_55h = [data_list[j]['high'] for j in range(max(0, i-55), i)]
            # Exit channels
            window_10l = [data_list[j]['low'] for j in range(max(0, i-10), i)]
            window_20l = [data_list[j]['low'] for j in range(max(0, i-20), i)]

            dc_20_high = max(window_20h) if window_20h else d['high']
            dc_55_high = max(window_55h) if window_55h else d['high']
            dc_10_low = min(window_10l) if window_10l else d['low']
            dc_20_low = min(window_20l) if window_20l else d['low']

            # 3. EMA-200
            k = 2 / (200 + 1)
            if ema_200 is None:
                ema_200 = d['close']
            else:
                ema_200 = d['close'] * k + ema_200 * (1 - k)

            res = d.copy()
            res['tr'] = tr
            res['N'] = n_val
            res['dc_20_high'] = dc_20_high
            res['dc_55_high'] = dc_55_high
            res['dc_10_low'] = dc_10_low
            res['dc_20_low'] = dc_20_low
            res['ema_200'] = ema_200
            results.append(res)

        return results


class RiskManager:
    def calculate_unit_size(self, balance, n_value, price, n_avg_20=None):
        if n_value == 0: return 0.0
        unit_size = (balance * 0.01) / n_value

        # Volatility Cap: Reduce by 50% if current N is 1.5x of 20-day average N
        if n_avg_20 and n_value > (n_avg_20 * 1.5):
            unit_size *= 0.5

        return round(unit_size, 6)

    def calculate_unit_size_with_mdd(self, current_equity, n_value, price, peak_equity=None):
        """
        MDD Risk Reduction (TECHNICAL_DESIGN 2.4):
        For every 10% drawdown from peak, reduce virtual equity by 20%.
        """
        if n_value == 0: return 0.0

        virtual_equity = current_equity
        if peak_equity and peak_equity > 0:
            drawdown_pct = (peak_equity - current_equity) / peak_equity
            # Number of 10% drawdown steps
            reduction_steps = int(drawdown_pct / 0.10)
            for _ in range(reduction_steps):
                virtual_equity *= 0.8

        unit_size = (virtual_equity * 0.01) / n_value
        return round(unit_size, 6)

    def can_entry(self, current_heat, max_heat):
        return current_heat < max_heat
