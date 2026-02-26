"""
BATS Design Compliance Tests
Verifies all features specified in docs/DESIGN.md and docs/TECHNICAL_DESIGN.md
are correctly implemented.
"""
import unittest
import json
import os
import tempfile
from unittest.mock import MagicMock, patch, call
from src.core.modules_impl_lite import TechnicalAnalysisEngine, RiskManager
from src.core.signal_manager import TurtleSignalManager
from src.utils.persistence import JSONPersistence
from src.main_loop import MainLoop


# ============================================================
# Helper: Mock DataFrame that behaves like pandas for signal_manager
# ============================================================
class MockDF:
    """Simulates a pandas-like DataFrame with columns and .iloc[-1] access."""
    def __init__(self, data_dict):
        self._data = data_dict
        self.columns = list(data_dict.keys())

    def __getitem__(self, key):
        return MockSeries(self._data[key])

    def __contains__(self, key):
        return key in self._data


class MockSeries:
    def __init__(self, values):
        self._values = values if isinstance(values, list) else [values]

    @property
    def iloc(self):
        return self

    def __getitem__(self, idx):
        return self._values[idx]


# ============================================================
# [DESIGN.md 2.2] Technical Analysis Engine
# ============================================================
class TestTA_Indicators(unittest.TestCase):
    """Verify: N (ATR-20), Donchian 20/55/10/20, EMA-200"""

    def setUp(self):
        self.ta = TechnicalAnalysisEngine()

    def test_n_value_calculated(self):
        data = [{'high': 110, 'low': 90, 'close': 100}] * 30
        result = self.ta.calculate_indicators(data)
        self.assertIn('N', result[-1])
        self.assertGreater(result[-1]['N'], 0)

    def test_donchian_20_high(self):
        data = [{'high': 100, 'low': 80, 'close': 90}] * 30
        result = self.ta.calculate_indicators(data)
        self.assertIn('dc_20_high', result[-1])

    def test_donchian_55_high(self):
        """TECHNICAL_DESIGN 2.2: 55-day Donchian required for S2 entry."""
        data = [{'high': 100, 'low': 80, 'close': 90}] * 60
        result = self.ta.calculate_indicators(data)
        self.assertIn('dc_55_high', result[-1])

    def test_donchian_10_low(self):
        """TECHNICAL_DESIGN 2.2: 10-day low required for S1 exit."""
        data = [{'high': 100, 'low': 80, 'close': 90}] * 30
        result = self.ta.calculate_indicators(data)
        self.assertIn('dc_10_low', result[-1])

    def test_donchian_20_low(self):
        """TECHNICAL_DESIGN 2.2: 20-day low required for S2 exit."""
        data = [{'high': 100, 'low': 80, 'close': 90}] * 30
        result = self.ta.calculate_indicators(data)
        self.assertIn('dc_20_low', result[-1])

    def test_ema_200(self):
        """TECHNICAL_DESIGN 2.2: 200-day EMA trend filter."""
        data = [{'high': 100, 'low': 80, 'close': 90}] * 210
        result = self.ta.calculate_indicators(data)
        self.assertIn('ema_200', result[-1])


# ============================================================
# [DESIGN.md 2.4] Risk Manager
# ============================================================
class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager()

    def test_unit_sizing_basic(self):
        """Unit = (Balance * 0.01) / N"""
        unit = self.rm.calculate_unit_size(10000, 100, 50000)
        self.assertAlmostEqual(unit, 1.0)

    def test_volatility_cap(self):
        """TECHNICAL_DESIGN 2.4: N > 1.5x avg → unit halved."""
        normal = self.rm.calculate_unit_size(10000, 100, 50000, n_avg_20=50)
        # 100 > 50*1.5=75, so cap should trigger → halved
        self.assertAlmostEqual(normal, 0.5)

    def test_volatility_cap_not_triggered(self):
        """When N is within normal range, no reduction."""
        unit = self.rm.calculate_unit_size(10000, 100, 50000, n_avg_20=100)
        # 100 <= 100*1.5=150, so no cap
        self.assertAlmostEqual(unit, 1.0)

    def test_mdd_risk_reduction(self):
        """TECHNICAL_DESIGN 2.4: MDD-based virtual equity reduction.
        10% drawdown from peak → reduce equity by 20%."""
        peak = 100000
        current = 90000  # 10% drawdown
        unit = self.rm.calculate_unit_size_with_mdd(current, 100, 50000, peak_equity=peak)
        # Virtual equity = 90000 * 0.8 = 72000, unit = 72000*0.01/100 = 7.2
        self.assertAlmostEqual(unit, 7.2)

    def test_portfolio_heat(self):
        """TECHNICAL_DESIGN 2.4: Portfolio heat limit control."""
        self.assertTrue(self.rm.can_entry(0.1, 0.2))
        self.assertFalse(self.rm.can_entry(0.2, 0.2))
        self.assertFalse(self.rm.can_entry(0.25, 0.2))


# ============================================================
# [DESIGN.md 2.3] Signal Manager
# ============================================================
class TestSignalManager(unittest.TestCase):
    def setUp(self):
        self.sm = TurtleSignalManager()

    def _make_df(self, dc20h=100, dc55h=150, dc10l=80, dc20l=70, ema200=50):
        return MockDF({
            'dc_20_high': dc20h,
            'dc_55_high': dc55h,
            'dc_10_low': dc10l,
            'dc_20_low': dc20l,
            'ema_200': ema200,
        })

    def test_s1_entry_after_loss(self):
        df = self._make_df()
        state = {"last_trade_result": "loss", "units_held": 0, "system_mode": "S1"}
        self.assertEqual(self.sm.generate_signal(df, 110, state), "BUY")

    def test_s1_skip_after_win(self):
        df = self._make_df()
        state = {"last_trade_result": "win", "units_held": 0, "system_mode": "S1"}
        self.assertEqual(self.sm.generate_signal(df, 110, state), "HOLD")

    def test_s2_entry_always(self):
        df = self._make_df()
        state = {"last_trade_result": "win", "units_held": 0, "system_mode": "S1"}
        self.assertEqual(self.sm.generate_signal(df, 160, state), "BUY")

    def test_ema_filter_blocks_buy(self):
        """DESIGN.md 4.4: Price below EMA-200 should block entry."""
        df = self._make_df(ema200=200)
        state = {"last_trade_result": "loss", "units_held": 0}
        self.assertEqual(self.sm.generate_signal(df, 110, state), "HOLD")

    def test_s1_exit_10day_low(self):
        """TECHNICAL_DESIGN 2.5: S1 trailing stop at 10-day low."""
        df = self._make_df(dc10l=80)
        state = {"units_held": 1, "system_mode": "S1", "entry_prices": [100]}
        self.assertEqual(self.sm.generate_signal(df, 70, state), "EXIT")

    def test_s2_exit_20day_low(self):
        """TECHNICAL_DESIGN 2.5: S2 trailing stop at 20-day low (NOT 10-day)."""
        df = self._make_df(dc10l=60, dc20l=80)
        state = {"units_held": 1, "system_mode": "S2", "entry_prices": [100]}
        # Price 75: above 10-day low (60) but below 20-day low (80) → S2 should EXIT
        self.assertEqual(self.sm.generate_signal(df, 75, state), "EXIT")

    def test_hard_stop_2n(self):
        """TECHNICAL_DESIGN 2.5: Stop Loss at last entry - 2N."""
        df = self._make_df(dc10l=50, dc20l=40)
        n_value = 10
        state = {"units_held": 1, "system_mode": "S1", "entry_prices": [100], "current_n": n_value}
        # last entry 100 - 2*10 = 80. Price 78 should trigger hard stop.
        self.assertEqual(self.sm.generate_signal(df, 78, state), "EXIT")

    def test_pyramiding_signal(self):
        """TECHNICAL_DESIGN 2.5: Pyramiding at +0.5N from last entry, max 4 units."""
        df = self._make_df(dc10l=50)
        n_value = 10
        state = {"units_held": 1, "system_mode": "S1", "entry_prices": [100], "current_n": n_value}
        # last entry 100 + 0.5*10 = 105. Price 106 should trigger PYRAMID.
        self.assertEqual(self.sm.generate_signal(df, 106, state), "PYRAMID")

    def test_pyramiding_max_4_units(self):
        """TECHNICAL_DESIGN 2.5: Max 4 units per instrument."""
        df = self._make_df(dc10l=50)
        n_value = 10
        state = {"units_held": 4, "system_mode": "S1", "entry_prices": [100, 105, 110, 115], "current_n": n_value}
        # Already 4 units held, should NOT pyramid further.
        result = self.sm.generate_signal(df, 121, state)
        self.assertNotEqual(result, "PYRAMID")


# ============================================================
# [DESIGN.md 3] Persistence
# ============================================================
class TestPersistence(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name
        try:
            p = JSONPersistence(filepath=path)
            state = {"units_held": 2, "last_trade_result": "win", "entry_prices": [100, 105], "system_mode": "S1"}
            p.save(state)
            loaded = p.load()
            self.assertEqual(loaded['units_held'], 2)
            self.assertEqual(loaded['last_trade_result'], "win")
            self.assertEqual(loaded['entry_prices'], [100, 105])
            self.assertEqual(loaded['system_mode'], "S1")
        finally:
            os.unlink(path)

    def test_load_default_on_missing_file(self):
        p = JSONPersistence(filepath="/tmp/nonexistent_bats_state.json")
        state = p.load()
        self.assertEqual(state['units_held'], 0)
        self.assertEqual(state['last_trade_result'], "loss")


# ============================================================
# [DESIGN.md 5] Main Loop Integration
# ============================================================
class TestMainLoopIntegration(unittest.TestCase):
    def setUp(self):
        self.config = {'symbol': 'BTCUSDT', 'interval': '1h', 'polling_interval': 1, 'max_heat': 0.2}
        self.exchange = MagicMock()
        self.ta = MagicMock()
        self.signal = MagicMock()
        self.risk = MagicMock()
        self.execution = MagicMock()

    @patch('src.main_loop.JSONPersistence')
    def test_buy_saves_state(self, MockPersistence):
        mock_p = MagicMock()
        mock_p.load.return_value = {"last_trade_result": "loss", "units_held": 0, "entry_prices": [], "system_mode": "S1"}
        MockPersistence.return_value = mock_p

        mock_df = MagicMock()
        mock_df.__getitem__ = MagicMock(return_value=MagicMock(iloc=MagicMock(__getitem__=MagicMock(return_value=100))))
        self.exchange.get_market_data.return_value = mock_df
        self.exchange.get_realtime_price.return_value = 50000
        self.exchange.get_asset_balance.return_value = 10000
        self.ta.calculate_indicators.return_value = mock_df
        self.signal.generate_signal.return_value = "BUY"
        self.risk.calculate_unit_size.return_value = 0.1
        self.risk.can_entry.return_value = True

        loop = MainLoop(self.config, self.exchange, self.ta, self.signal, self.risk, self.execution)
        loop.run_once()

        self.execution.execute_order.assert_called_with('BTCUSDT', 'BUY', 0.1)
        mock_p.save.assert_called()

    @patch('src.main_loop.JSONPersistence')
    def test_exit_saves_state(self, MockPersistence):
        mock_p = MagicMock()
        mock_p.load.return_value = {"last_trade_result": "loss", "units_held": 1, "entry_prices": [100], "system_mode": "S1"}
        MockPersistence.return_value = mock_p

        mock_df = MagicMock()
        mock_df.__getitem__ = MagicMock(return_value=MagicMock(iloc=MagicMock(__getitem__=MagicMock(return_value=100))))
        self.exchange.get_market_data.return_value = mock_df
        self.exchange.get_realtime_price.return_value = 50000
        self.ta.calculate_indicators.return_value = mock_df
        self.signal.generate_signal.return_value = "EXIT"

        loop = MainLoop(self.config, self.exchange, self.ta, self.signal, self.risk, self.execution)
        loop.run_once()

        self.execution.execute_order.assert_called()
        mock_p.save.assert_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
