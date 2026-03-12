import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.main_loop import MainLoop

class TestApiOptimization(unittest.TestCase):
    def setUp(self):
        # Cleanup state.json to avoid contamination
        if os.path.exists('state.json'):
            os.remove('state.json')
        if os.path.exists('test_state.json'):
            os.remove('test_state.json')
            
        self.config = {
            'symbols': [
                {'name': 'BTCUSDT', 'enabled': True, 'timeframe': '1h'},
                {'name': 'ETHUSDT', 'enabled': True, 'timeframe': '1h'}
            ],
            'risk': {
                'unit_risk_percent': 0.01,
                'max_portfolio_heat': 0.2
            },
            'system': {
                'polling_interval': 60
            }
        }
        self.exchange = MagicMock()
        self.ta = MagicMock()
        self.signal_manager = MagicMock()
        self.risk = MagicMock()
        self.execution = MagicMock()
        
        # Default mock returns
        self.exchange.get_market_data.return_value = MagicMock()
        self.exchange.get_realtime_price.return_value = 50000.0
        self.exchange.get_asset_balance.return_value = 1000.0
        
        # Mock TA to return N and N_avg_20
        import pandas as pd
        df_mock = pd.DataFrame({'N': [1.0] * 30})
        self.ta.calculate_indicators.return_value = df_mock
        
        # Mock Signal Manager to return BUY to trigger balance check
        self.signal_manager.generate_signal.return_value = "BUY"
        
        # Mock Risk Manager
        self.risk.calculate_total_heat.return_value = 0.0
        self.risk.calculate_unit_size.return_value = 10.0
        self.risk.can_entry.return_value = True

    def test_run_once_calls_balance_minimum_times(self):
        # Initialize MainLoop
        main_loop = MainLoop(self.config, self.exchange, self.ta, self.signal_manager, self.risk, self.execution)
        
        # Clear mock call history
        self.exchange.get_asset_balance.reset_mock()
        
        # Run once
        main_loop.run_once()
        
        # Before optimization, it might be called twice (once per symbol if both signal BUY)
        call_count = self.exchange.get_asset_balance.call_count
        print(f"get_asset_balance call count: {call_count}")
        
        # The goal is to have it called exactly once (or a small constant number)
        # regardless of the number of symbols.
        self.assertEqual(call_count, 1, "get_asset_balance should be called exactly once per run_once")

if __name__ == '__main__':
    unittest.main()
