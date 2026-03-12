import json
import os
import pandas as pd
from datetime import datetime
from urllib.request import urlopen
from src.core import TechnicalAnalysisEngine, RiskManager, TurtleSignalManager

class MultiSymbolBacktestEngine:
    def __init__(self, config):
        self.symbols_config = config.get('symbols', [])
        self.initial_balance = config.get('initial_balance', 10000)
        self.unit_risk_percent = config.get('unit_risk_percent', 0.01)
        self.max_portfolio_heat = config.get('max_portfolio_heat', 0.2)
        self.limit = config.get('limit', 500)
        self.interval = config.get('interval', '4h')
        
        self.balance = self.initial_balance
        self.symbols_state = {}
        for s in self.symbols_config:
            self.symbols_state[s['name']] = {
                "last_trade_result": "loss",
                "units_held": 0,
                "entry_prices": [],
                "notionals": [],
                "system_mode": "S1",
                "current_n": 0
            }
        self.trades = []
        self.equity_curve = []
        self.ta = TechnicalAnalysisEngine()
        self.risk = RiskManager()
        
        strategy_params = config.get('strategy_params', {
            'use_s3': True,
            'adx_filter_threshold': 25.0,
            'stop_n_multiplier': 5.0
        })
        self.signal_manager = TurtleSignalManager(**strategy_params)

    def fetch_data(self, symbol):
        print(f"Fetching data for {symbol}...")
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={self.interval}&limit={self.limit}"
        try:
            with urlopen(url) as response:
                data = json.loads(response.read().decode())
                formatted = []
                for k in data:
                    formatted.append({
                        'timestamp': k[0],
                        'open': float(k[1]),
                        'high': float(k[2]),
                        'low': float(k[3]),
                        'close': float(k[4]),
                        'volume': float(k[5])
                    })
                return pd.DataFrame(formatted)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return None

    def run(self):
        symbols_df = {}
        for s in self.symbols_config:
            name = s['name']
            df = self.fetch_data(name)
            if df is not None:
                symbols_df[name] = self.ta.calculate_indicators(df)

        # Align timestamps (take intersection)
        common_timestamps = None
        for name, df in symbols_df.items():
            if common_timestamps is None:
                common_timestamps = set(df['timestamp'])
            else:
                common_timestamps &= set(df['timestamp'])
        
        sorted_timestamps = sorted(list(common_timestamps))
        print(f"Running multi-symbol backtest on {len(sorted_timestamps)} bars...")

        start_idx = 90 # Lookback
        for ts in sorted_timestamps[start_idx:]:
            current_total_heat = self.risk.calculate_total_heat(self.symbols_state, self.unit_risk_percent)
            
            current_bar_equity = self.balance
            
            for name in symbols_df:
                df = symbols_df[name]
                bar = df[df['timestamp'] == ts].iloc[0]
                price = bar['close']
                sym_state = self.symbols_state[name]
                
                # Signal Generation (Pass sub-dataframe up to current bar)
                df_to_now = df[df['timestamp'] <= ts]
                sig = self.signal_manager.generate_signal(df_to_now, price, sym_state)
                
                # Handle Signal
                if sig in ["BUY", "PYRAMID"]:
                    if self.risk.can_entry(current_total_heat, self.max_portfolio_heat, self.unit_risk_percent):
                        n_value = bar['N']
                        # Simplified unit size calculation for backtest
                        unit_size_notional = (self.balance * self.unit_risk_percent) / n_value * price
                        
                        if self.balance >= unit_size_notional:
                            self.balance -= unit_size_notional
                            sym_state['units_held'] += 1
                            sym_state['entry_prices'].append(price)
                            sym_state['notionals'].append(unit_size_notional)
                            current_total_heat += self.unit_risk_percent
                            self.trades.append({
                                'timestamp': ts,
                                'symbol': name,
                                'type': sig,
                                'price': price,
                                'units': sym_state['units_held']
                            })
                
                elif sig == "EXIT":
                    if sym_state['units_held'] > 0:
                        total_return = 0
                        for i in range(len(sym_state['entry_prices'])):
                            notional = sym_state['notionals'][i]
                            entry_price = sym_state['entry_prices'][i]
                            total_return += notional * (price / entry_price)
                        
                        gain = total_return - sum(sym_state['notionals'])
                        self.balance += total_return
                        
                        sym_state['last_trade_result'] = 'win' if gain > 0 else 'loss'
                        self.trades.append({
                            'timestamp': ts,
                            'symbol': name,
                            'type': 'EXIT',
                            'price': price,
                            'gain': gain
                        })
                        
                        current_total_heat -= (sym_state['units_held'] * self.unit_risk_percent)
                        sym_state['units_held'] = 0
                        sym_state['entry_prices'] = []
                        sym_state['notionals'] = []
                
                # Update current bar equity
                if sym_state['units_held'] > 0:
                    for i in range(len(sym_state['entry_prices'])):
                        notional = sym_state['notionals'][i]
                        entry_price = sym_state['entry_prices'][i]
                        current_bar_equity += notional * (price / entry_price)

            self.equity_curve.append({
                'timestamp': ts,
                'equity': current_bar_equity
            })

        return self._generate_results()

    def _generate_results(self):
        final_equity = self.equity_curve[-1]['equity'] if self.equity_curve else self.balance
        total_return = (final_equity - self.initial_balance) / self.initial_balance * 100
        
        exits = [t for t in self.trades if t['type'] == 'EXIT']
        wins = [t for t in exits if t['gain'] > 0]
        win_rate = (len(wins) / len(exits) * 100) if exits else 0
        
        return {
            'summary': {
                'initial_balance': self.initial_balance,
                'final_equity': final_equity,
                'total_return_pct': total_return,
                'total_trades': len(self.trades),
                'win_rate_pct': win_rate
            }
        }

if __name__ == "__main__":
    config = {
        "symbols": [{"name": "BTCUSDT"}, {"name": "ETHUSDT"}],
        "initial_balance": 10000,
        "unit_risk_percent": 0.01,
        "max_portfolio_heat": 0.2,
        "limit": 500,
        "interval": "4h"
    }
    engine = MultiSymbolBacktestEngine(config)
    results = engine.run()
    print(json.dumps(results, indent=2))
