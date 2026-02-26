import unittest
from src.core.modules_impl_lite import TechnicalAnalysisEngine
from src.core.signal_manager import TurtleSignalManager

class TestStrategyUpgrade(unittest.TestCase):
    def setUp(self):
        self.ta = TechnicalAnalysisEngine()
        # Mock data for testing (simplified)
        self.data = []
        for i in range(300):
            # Create a simple uptrend
            price = 10000 + (i * 10)
            self.data.append({
                'timestamp': i,
                'open': price,
                'high': price + 50,
                'low': price - 50,
                'close': price,
                'volume': 1000
            })

    def test_adx_calculation(self):
        analyzed = self.ta.calculate_indicators(self.data)
        self.assertIn('ADX', analyzed[-1])
        # ADX should be positive in an uptrend
        self.assertGreater(analyzed[-1]['ADX'], 0)

    def test_5n_stop_loss(self):
        # Initial state with a position
        state = {
            'units_held': 1,
            'entry_prices': [10000],
            'current_n': 100,
            'system_mode': 'S3'
        }
        
        # Original 2N stop would be at 10000 - 200 = 9800
        # New 5N stop should be at 10000 - 500 = 9500
        
        manager = TurtleSignalManager(use_s3=True, stop_n_multiplier=5.0)
        
        # Test 1: Price at 9700 (between 2N and 5N)
        # In old 2N it would EXIT, in new 5N it should HOLD
        analyzed = self.ta.calculate_indicators(self.data)
        # To avoid trailing stop exit, make sure price is above dc_45_low
        analyzed[-1]['dc_45_low'] = 9000 
        
        signal = manager.generate_signal(analyzed, 9700, state)
        self.assertEqual(signal, "HOLD")
        
        # Test 2: Price at 9400 (below 5N)
        signal = manager.generate_signal(analyzed, 9400, state)
        self.assertEqual(signal, "EXIT")

    def test_adx_filter(self):
        # If ADX is low (e.g., 10), it should not generate a BUY signal even if breakout occurs
        manager = TurtleSignalManager(use_s3=True, adx_filter_threshold=25.0)
        
        # Mocking low ADX in the last bar
        analyzed = self.ta.calculate_indicators(self.data)
        analyzed[-1]['ADX'] = 15.0 
        
        # Price is at high (breakout for S3/90)
        price = analyzed[-1]['dc_90_high'] + 100
        
        state = {'units_held': 0}
        signal = manager.generate_signal(analyzed, price, state)
        self.assertEqual(signal, "HOLD")

if __name__ == '__main__':
    unittest.main()
