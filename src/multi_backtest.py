import json
import os
import sys
import pandas as pd
from datetime import datetime
from src.backtest import BacktestEngine, BacktestReporter

class MultiSymbolBacktestEngine:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.symbols = self.config.get('symbols', ['BTCUSDT'])
        self.interval = self.config.get('interval', '4h')
        self.limit = self.config.get('limit', 1000)
        self.initial_balance = self.config.get('initial_balance', 10000)
        self.risk_per_trade = self.config.get('risk_per_trade', 0.01)
        self.max_portfolio_heat = self.config.get('max_portfolio_heat', 0.2)
        
        self.balance = self.initial_balance
        # Individual symbol states
        self.symbol_states = {symbol: {
            'units_held': 0,
            'entry_prices': [],
            'notionals': [],
            'last_trade_result': None,
            'current_n': 0,
            'system_mode': 'S3'
        } for symbol in self.symbols}
        
        self.trades = []
        self.equity_curve = []

    def run(self):
        # 1. Fetch and align data for all symbols
        symbol_data = {}
        from src.core import TechnicalAnalysisEngine
        ta = TechnicalAnalysisEngine()

        for symbol in self.symbols:
            # Manually fetch data using the logic from BacktestEngine to avoid init error
            all_klines = []
            limit_per_request = 1000
            total_needed = self.limit
            interval_ms = 3600000 # Default 1h
            if self.interval == '4h': interval_ms *= 4
            elif self.interval == '1d': interval_ms *= 24
            
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = (end_time - (total_needed * interval_ms))
            
            from urllib.request import urlopen
            current_start = start_time
            print(f"Fetching data for {symbol}...")
            while len(all_klines) < total_needed:
                fetch_limit = min(limit_per_request, total_needed - len(all_klines))
                url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={self.interval}&startTime={current_start}&limit={fetch_limit}"
                try:
                    with urlopen(url) as response:
                        data = json.loads(response.read().decode())
                        if not data: break
                        all_klines.extend(data)
                        current_start = data[-1][0] + interval_ms
                        if len(data) < fetch_limit: break
                except: break
            
            formatted_data = [{'timestamp': k[0], 'open': float(k[1]), 'high': float(k[2]), 'low': float(k[3]), 'close': float(k[4]), 'volume': float(k[5])} for k in all_klines]
            symbol_data[symbol] = ta.calculate_indicators(pd.DataFrame(formatted_data))

        print("Starting Multi-Symbol Backtest...")
        
        from src.core import TurtleSignalManager, AdvancedTurtleManager
        strategy_params = self.config.get('strategy_params', {})
        strategy_class = AdvancedTurtleManager if self.config.get('strategy') == 'AdvancedTurtleManager' else TurtleSignalManager
        managers = {symbol: strategy_class(**strategy_params) for symbol in self.symbols}

        # Find common timestamps or use the first one's length
        length = min(len(df) for df in symbol_data.values())
        
        for i in range(90, length):
            current_total_heat = sum(s['units_held'] * self.risk_per_trade for s in self.symbol_states.values())
            
            # Process each symbol in the same time step
            for symbol in self.symbols:
                df = symbol_data[symbol]
                current_bar = df.iloc[i]
                price = current_bar['close']
                state = self.symbol_states[symbol]
                state['current_n'] = current_bar['N']
                
                signal = managers[symbol].generate_signal(df.iloc[:i+1], price, state)
                
                if signal in ["BUY", "PYRAMID"]:
                    if (current_total_heat + self.risk_per_trade) <= self.max_portfolio_heat:
                        # Handle buy
                        unit_size_notional = (self.balance * self.risk_per_trade) / current_bar['N'] * price
                        if self.balance >= unit_size_notional:
                            self.balance -= unit_size_notional
                            state['units_held'] += 1
                            state['entry_prices'].append(price)
                            state['notionals'].append(unit_size_notional)
                            current_total_heat += self.risk_per_trade
                            self.trades.append({
                                'timestamp': str(current_bar['timestamp']),
                                'symbol': symbol,
                                'type': signal,
                                'price': price,
                                'units_held': state['units_held'],
                                'balance': self.balance
                            })
                elif signal == "EXIT":
                    if state['units_held'] > 0:
                        total_return = 0
                        for i_pos in range(len(state['entry_prices'])):
                            entry_price = state['entry_prices'][i_pos]
                            notional = state['notionals'][i_pos]
                            total_return += notional * (price / entry_price)
                        
                        gain = total_return - sum(state['notionals'])
                        self.balance += total_return
                        state['last_trade_result'] = 'win' if gain > 0 else 'loss'
                        
                        self.trades.append({
                            'timestamp': str(current_bar['timestamp']),
                            'symbol': symbol,
                            'type': 'EXIT',
                            'price': price,
                            'gain': gain,
                            'balance': self.balance
                        })
                        
                        current_total_heat -= (state['units_held'] * self.risk_per_trade)
                        state['units_held'] = 0
                        state['entry_prices'] = []
                        state['notionals'] = []

            # Equity recording (cash + value of all open positions)
            current_equity = self.balance
            for symbol, state in self.symbol_states.items():
                if state['units_held'] > 0:
                    current_price = symbol_data[symbol].iloc[i]['close']
                    for i_pos in range(len(state['entry_prices'])):
                        entry_price = state['entry_prices'][i_pos]
                        notional = state['notionals'][i_pos]
                        current_equity += notional * (current_price / entry_price)
            
            self.equity_curve.append({
                'timestamp': str(symbol_data[self.symbols[0]].iloc[i]['timestamp']),
                'equity': current_equity
            })

        return self._generate_results()

    def _generate_results(self):
        final_equity = self.equity_curve[-1]['equity'] if self.equity_curve else self.balance
        return {
            'summary': {
                'initial_balance': self.initial_balance,
                'final_equity': final_equity,
                'total_return_pct': (final_equity - self.initial_balance) / self.initial_balance * 100
            },
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }

if __name__ == "__main__":
    config_path = sys.argv[1]
    engine = MultiSymbolBacktestEngine(config_path)
    results = engine.run()
    
    print("\n" + "="*50)
    print("MULTI-SYMBOL BACKTEST REPORT (1000 DAYS)")
    print("="*50)
    print(f"Initial: {results['summary']['initial_balance']:.2f}")
    print(f"Final:   {results['summary']['final_equity']:.2f}")
    print(f"Return:  {results['summary']['total_return_pct']:.2f}%")
    print("\n[TRADE LOG]")
    print(f"{'Timestamp':<25} | {'Symbol':<10} | {'Type':<8} | {'Price':<10} | {'Result/Gain'}")
    print("-" * 75)
    for t in results['trades']:
        res = f"{t.get('gain', ''):.2f}" if 'gain' in t else "-"
        print(f"{t['timestamp']:<25} | {t['symbol']:<10} | {t['type']:<8} | {t['price']:<10.2f} | {res}")
