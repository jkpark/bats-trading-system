import os
import json
import hmac
import hashlib
import time
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from src.core.modules_impl_lite import TechnicalAnalysisEngine, RiskManager
from src.core.signal_manager import TurtleSignalManager

class LiteBacktester:
    def __init__(self, symbol="BTCUSDT", interval="1h", initial_balance=10000):
        self.symbol = symbol
        self.interval = interval
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.units_held = 0
        self.entry_prices = []
        self.state = {
            'units_held': 0,
            'entry_prices': [],
            'last_trade_result': None,
            'current_n': 0,
            'system_mode': 'S1'
        }
        self.trades = []

    def fetch_data(self, limit=1000):
        print(f"Fetching {limit} candles for {self.symbol}...")
        url = f"https://api.binance.com/api/v3/klines?symbol={self.symbol}&interval={self.interval}&limit={limit}"
        with urlopen(url) as response:
            data = json.loads(response.read().decode())
            # Convert to list of dicts
            klines = []
            for k in data:
                klines.append({
                    'timestamp': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                })
            return klines

    def run(self):
        data = self.fetch_data()
        ta = TechnicalAnalysisEngine()
        analyzed_data = ta.calculate_indicators(data)
        
        signal_manager = TurtleSignalManager()
        risk_manager = RiskManager()
        
        print("Starting simulation...")
        # Start from index 55 to ensure indicators (like Donchian 55) are ready
        for i in range(55, len(analyzed_data)):
            current_bar = analyzed_data[i]
            # Use data up to the PREVIOUS bar for signals to avoid look-ahead bias
            # In our implementation, analyzed_data[i] already has DC calculated from range(i-20, i)
            # So it's safe to use current_bar's indicators with current_bar's price.
            
            price = current_bar['close']
            self.state['current_n'] = current_bar['N']
            
            # The signal manager needs the "dataframe" (list) and current price
            # We pass analyzed_data[:i+1] to simulate the historical view
            signal = signal_manager.generate_signal(analyzed_data[:i+1], price, self.state)
            
            if signal in ["BUY", "PYRAMID"]:
                n_value = current_bar['N']
                if n_value > 0:
                    unit_size_notional = (self.balance * 0.01) / n_value * price
                    
                    if self.balance >= unit_size_notional and self.state['units_held'] < 4:
                        self.balance -= unit_size_notional
                        self.state['units_held'] += 1
                        # Track price and notional separately
                        if 'notionals' not in self.state: self.state['notionals'] = []
                        self.state['entry_prices'].append(price)
                        self.state['notionals'].append(unit_size_notional)
                        self.trades.append({'type': signal, 'price': price, 'time': current_bar['timestamp']})
            
            elif signal == "EXIT":
                if self.state['units_held'] > 0:
                    total_return_from_position = 0
                    for i_pos in range(len(self.state['entry_prices'])):
                        entry_price = self.state['entry_prices'][i_pos]
                        notional = self.state['notionals'][i_pos]
                        trade_return = notional * (price / entry_price)
                        total_return_from_position += trade_return
                    
                    gain = total_return_from_position - sum(self.state['notionals'])
                    self.balance += total_return_from_position
                    
                    self.state['last_trade_result'] = 'win' if gain > 0 else 'loss'
                    print(f"EXIT at {price}: Gain {gain:.2f} USDT, New Balance: {self.balance:.2f} USDT")
                    self.trades.append({'type': 'EXIT', 'price': price, 'time': current_bar['timestamp'], 'gain': gain})
                    
                    self.state['units_held'] = 0
                    self.state['entry_prices'] = []
                    self.state['notionals'] = []

        self.report()

    def report(self):
        print("\n=== Backtest Report ===")
        print(f"Symbol: {self.symbol} ({self.interval})")
        print(f"Initial Balance: {self.initial_balance:.2f} USDT")
        print(f"Final Balance: {self.balance:.2f} USDT")
        total_return = (self.balance - self.initial_balance) / self.initial_balance * 100
        print(f"Total Return: {total_return:.2f}%")
        print(f"Total Trades: {len(self.trades)}")
        
        if len(self.trades) > 0:
            wins = len([t for t in self.trades if t.get('gain', 0) > 0])
            exits = len([t for t in self.trades if t['type'] == 'EXIT'])
            win_rate = (wins / exits * 100) if exits > 0 else 0
            print(f"Win Rate: {win_rate:.2f}%")

if __name__ == "__main__":
    tester = LiteBacktester(symbol="BTCUSDT", interval="1d")
    tester.run()
