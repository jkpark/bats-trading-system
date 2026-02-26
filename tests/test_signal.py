import unittest
from unittest.mock import MagicMock
from src.core.signal_manager import TurtleSignalManager

class TestTurtleSignal(unittest.TestCase):
    def setUp(self):
        self.manager = TurtleSignalManager()
        # Mock DataFrame-like object
        self.df = MagicMock()
        self.df.columns = ['dc_20_high', 'dc_55_high', 'dc_10_low', 'dc_20_low', 'ema_200']
        
    def set_mock_values(self, dc20h, dc55h, dc10l, ema200):
        # Helper to set mock return values for .iloc[-1]
        self.df.__getitem__.return_value.iloc.__getitem__.side_effect = lambda x: {
            'dc_20_high': dc20h,
            'dc_55_high': dc55h,
            'dc_10_low': dc10l,
            'ema_200': ema200
        }[self.df.__getitem__.call_args[0][0]]

    def test_s1_entry_after_loss(self):
        self.set_mock_values(dc20h=100, dc55h=150, dc10l=80, ema200=50)
        state = {"last_trade_result": "loss", "units_held": 0}
        
        # Price 110 breaks 20-day high (100)
        signal = self.manager.generate_signal(self.df, 110, state)
        self.assertEqual(signal, "BUY")

    def test_s1_skip_after_win(self):
        self.set_mock_values(dc20h=100, dc55h=150, dc10l=80, ema200=50)
        state = {"last_trade_result": "win", "units_held": 0}
        
        # Price 110 breaks 20-day high (100) but last was win
        signal = self.manager.generate_signal(self.df, 110, state)
        self.assertEqual(signal, "HOLD")

    def test_s2_entry_even_after_win(self):
        self.set_mock_values(dc20h=100, dc55h=150, dc10l=80, ema200=50)
        state = {"last_trade_result": "win", "units_held": 0}
        
        # Price 160 breaks 55-day high (150)
        signal = self.manager.generate_signal(self.df, 160, state)
        self.assertEqual(signal, "BUY")

    def test_exit_logic(self):
        self.set_mock_values(dc20h=100, dc55h=150, dc10l=80, ema200=50)
        state = {"last_trade_result": "loss", "units_held": 1}
        
        # Price 70 breaks 10-day low (80)
        signal = self.manager.generate_signal(self.df, 70, state)
        self.assertEqual(signal, "EXIT")

if __name__ == '__main__':
    unittest.main()
