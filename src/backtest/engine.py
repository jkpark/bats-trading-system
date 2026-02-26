import json
import os
from datetime import datetime
from urllib.request import urlopen
from src.core.modules_impl_lite import TechnicalAnalysisEngine, RiskManager
from src.core.signal_manager import TurtleSignalManager

class BacktestEngine:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.symbol = self.config.get('symbol', 'BTCUSDT')
        self.interval = self.config.get('interval', '1h')
        self.limit = self.config.get('limit', 1000)
        self.start_time = self.config.get('start_time')
        self.end_time = self.config.get('end_time')
        self.initial_balance = self.config.get('initial_balance', 10000)
        self.risk_per_trade = self.config.get('risk_per_trade', 0.01)
        self.max_units = self.config.get('max_units', 4)
        
        self.balance = self.initial_balance
        self.state = {
            'units_held': 0,
            'entry_prices': [],
            'notionals': [],
            'last_trade_result': None,
            'current_n': 0,
            'system_mode': 'S3'
        }
        self.trades = []
        self.equity_curve = []

    def fetch_data(self):
        print(f"Fetching data for {self.symbol}...")
        all_klines = []
        current_start = self.start_time if self.start_time else (int(datetime.now().timestamp() * 1000) - (self.limit * 24 * 60 * 60 * 1000))
        end_target = self.end_time if self.end_time else int(datetime.now().timestamp() * 1000)
        
        while current_start < end_target:
            url = f"https://api.binance.com/api/v3/klines?symbol={self.symbol}&interval={self.interval}&startTime={current_start}&limit=1000"
            if self.end_time:
                url += f"&endTime={self.end_time}"
                
            with urlopen(url) as response:
                data = json.loads(response.read().decode())
                if not data:
                    break
                all_klines.extend(data)
                # Move start time to the next candle
                current_start = data[-1][0] + 1
                if len(data) < 1000:
                    break
        
        klines = []
        for k in all_klines:
            klines.append({
                'timestamp': k[0],
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5])
            })
        print(f"Total candles fetched: {len(klines)}")
        return klines

    def run(self):
        raw_data = self.fetch_data()
        ta = TechnicalAnalysisEngine()
        analyzed_data = ta.calculate_indicators(raw_data)
        
        strategy_params = self.config.get('strategy_params', {})
        signal_manager = TurtleSignalManager(**strategy_params)
        
        print(f"Starting backtest for {self.symbol} ({self.interval})...")
        
        # Determine the starting index based on the longest lookback (e.g., 55 for S2)
        start_idx = 55 
        
        for i in range(start_idx, len(analyzed_data)):
            current_bar = analyzed_data[i]
            price = current_bar['close']
            self.state['current_n'] = current_bar['N']
            
            # Generate signal based on data up to now
            signal = signal_manager.generate_signal(analyzed_data[:i+1], price, self.state)
            
            self._handle_signal(signal, price, current_bar)
            
            # Record equity
            current_equity = self.balance
            if self.state['units_held'] > 0:
                for i_pos in range(len(self.state['entry_prices'])):
                    entry_price = self.state['entry_prices'][i_pos]
                    notional = self.state['notionals'][i_pos]
                    current_equity += notional * (price / entry_price) - notional
            
            self.equity_curve.append({
                'timestamp': current_bar['timestamp'],
                'equity': current_equity
            })

        results = self._generate_results()
        return results

    def _handle_signal(self, signal, price, current_bar):
        if signal in ["BUY", "PYRAMID"]:
            n_value = current_bar['N']
            if n_value > 0 and self.state['units_held'] < self.max_units:
                # Calculate unit size: (balance * risk%) / N
                # This is a simplified version of the Turtle risk management
                unit_size_notional = (self.balance * self.risk_per_trade) / n_value * price
                
                if self.balance >= unit_size_notional:
                    self.balance -= unit_size_notional
                    self.state['units_held'] += 1
                    self.state['entry_prices'].append(price)
                    self.state['notionals'].append(unit_size_notional)
                    self.trades.append({
                        'timestamp': current_bar['timestamp'],
                        'symbol': self.symbol,
                        'type': signal,
                        'price': price,
                        'units_held': self.state['units_held'],
                        'balance': self.balance
                    })
        
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
                
                self.trades.append({
                    'timestamp': current_bar['timestamp'],
                    'symbol': self.symbol,
                    'type': 'EXIT',
                    'price': price,
                    'gain': gain,
                    'balance': self.balance
                })
                
                self.state['units_held'] = 0
                self.state['entry_prices'] = []
                self.state['notionals'] = []

    def _generate_results(self):
        final_equity = self.equity_curve[-1]['equity'] if self.equity_curve else self.balance
        total_return = (final_equity - self.initial_balance) / self.initial_balance * 100
        
        exits = [t for t in self.trades if t['type'] == 'EXIT']
        wins = [t for t in exits if t['gain'] > 0]
        win_rate = (len(wins) / len(exits) * 100) if exits else 0
        
        # Calculate Max Drawdown
        max_equity = self.initial_balance
        max_drawdown = 0
        for point in self.equity_curve:
            if point['equity'] > max_equity:
                max_equity = point['equity']
            drawdown = (max_equity - point['equity']) / max_equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return {
            'config': self.config,
            'summary': {
                'initial_balance': self.initial_balance,
                'final_equity': final_equity,
                'total_return_pct': total_return,
                'max_drawdown_pct': max_drawdown * 100,
                'total_trades': len(self.trades),
                'total_exits': len(exits),
                'win_rate_pct': win_rate
            },
            'trades': self.trades,
            'equity_curve': self.equity_curve
        }

    def save_results(self, results, output_path=None):
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"backtest_results_{timestamp}.json"
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {output_path}")
        return output_path
