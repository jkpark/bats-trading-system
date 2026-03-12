import unittest
from unittest.mock import MagicMock
import pandas as pd
from src.core.modules_impl import RiskManager
from src.utils import JSONPersistence
from src.main_loop import MainLoop

class TestMultiSymbol(unittest.TestCase):
    def setUp(self):
        self.risk = RiskManager()
        self.persistence = JSONPersistence("test_state.json")
        self.config = {
            "system": {"polling_interval": 1},
            "risk": {
                "max_portfolio_heat": 0.2,
                "unit_risk_percent": 0.01
            },
            "symbols": [
                {"name": "BTCUSDT", "enabled": True, "timeframe": "4h"},
                {"name": "ETHUSDT", "enabled": True, "timeframe": "4h"}
            ]
        }

    def test_total_heat_calculation(self):
        symbols_state = {
            "BTCUSDT": {"units_held": 2},
            "ETHUSDT": {"units_held": 1}
        }
        # 3 units * 0.01 = 0.03
        total_heat = self.risk.calculate_total_heat(symbols_state, 0.01)
        self.assertEqual(total_heat, 0.03)

    def test_risk_manager_can_entry(self):
        # Current heat 0.19, max 0.2, new unit 0.01 -> True
        self.assertTrue(self.risk.can_entry(0.19, 0.2, 0.01))
        # Current heat 0.2, max 0.2, new unit 0.01 -> False
        self.assertFalse(self.risk.can_entry(0.20, 0.2, 0.01))

    def test_persistence_symbol_state(self):
        state = {"symbols": {}}
        sym_state = self.persistence.get_symbol_state(state, "BTCUSDT")
        self.assertEqual(sym_state["units_held"], 0)
        self.assertIn("BTCUSDT", state["symbols"])

    def test_main_loop_iteration_flow(self):
        # Mock dependencies
        exchange = MagicMock()
        ta = MagicMock()
        signal_manager = MagicMock()
        execution = MagicMock()
        
        # Setup mock data
        exchange.get_market_data.return_value = MagicMock() # Non-empty df
        exchange.get_realtime_price.return_value = 50000.0
        exchange.get_asset_balance.return_value = 10000.0
        
        # Mock indicators using real Pandas DataFrame for simplicity
        df_analyzed = pd.DataFrame({'N': [100.0] * 30})
        ta.calculate_indicators.return_value = df_analyzed
        
        # Signal: BUY for first symbol, HOLD for others
        calls = []
        def sig_gen(df, price, state):
            if not calls:
                calls.append(True)
                return "BUY"
            return "HOLD"
        signal_manager.generate_signal.side_effect = sig_gen
        
        execution.execute_order.return_value = True
        
        loop = MainLoop(self.config, exchange, ta, signal_manager, self.risk, execution)
        # Clear state file if exists
        import os
        if os.path.exists("test_state.json"): os.remove("test_state.json")
        loop.state = loop.persistence.load()
        
        loop.run_once()
        
        # Verify BTC state updated (Assuming BTC is first)
        self.assertEqual(loop.state['symbols']['BTCUSDT']['units_held'], 1)
        # Verify ETH state remains 0
        self.assertEqual(loop.state['symbols']['ETHUSDT']['units_held'], 0)
        # Verify total heat
        self.assertAlmostEqual(loop.state['total_heat'], 0.01)

if __name__ == "__main__":
    unittest.main()
