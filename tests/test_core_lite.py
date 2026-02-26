import unittest
from src.core.modules_impl_lite import TechnicalAnalysisEngine, RiskManager

class TestBATSLite(unittest.TestCase):
    def setUp(self):
        self.ta = TechnicalAnalysisEngine()
        self.rm = RiskManager()
        self.data = [{'high': 120, 'low': 100, 'close': 110}] * 30

    def test_ta_lite(self):
        results = self.ta.calculate_indicators(self.data)
        last = results[-1]
        self.assertIn('N', last)
        self.assertEqual(last['N'], 20.0) # (120-100) = 20
        self.assertEqual(last['dc_20_high'], 120)
        print("TA Lite Test: Passed")

    def test_risk_lite(self):
        # Balance: 10000, N: 20
        # (10000 * 0.01) / 20 = 5.0
        unit = self.rm.calculate_unit_size(10000, 20, 50000)
        self.assertEqual(unit, 5.0)
        print("Risk Lite Test: Passed")

    def test_integration_lite(self):
        results = self.ta.calculate_indicators(self.data)
        current_n = results[-1]['N']
        unit = self.rm.calculate_unit_size(10000, current_n, 50000)
        self.assertEqual(unit, 5.0)
        print(f"Integration Lite Test: Passed (Unit: {unit})")

if __name__ == '__main__':
    unittest.main()
