import unittest
from unittest.mock import MagicMock, patch
from src.main_loop import MainLoop

class TestMainLoop(unittest.TestCase):
    def setUp(self):
        self.config = {'symbol': 'BTCUSDT', 'interval': '1h', 'polling_interval': 1, 'max_heat': 0.2}
        self.exchange = MagicMock()
        self.ta = MagicMock()
        self.signal = MagicMock()
        self.risk = MagicMock()
        self.execution = MagicMock()

    def _make_loop(self, mock_persistence):
        mock_p = MagicMock()
        mock_p.load.return_value = {"last_trade_result": "loss", "units_held": 0, "entry_prices": [], "system_mode": "S1"}
        mock_persistence.return_value = mock_p
        return MainLoop(self.config, self.exchange, self.ta, self.signal, self.risk, self.execution)

    @patch('src.main_loop.JSONPersistence')
    def test_run_once_buy_flow(self, MockP):
        loop = self._make_loop(MockP)

        mock_df = MagicMock()
        mock_df.__getitem__.return_value.iloc.__getitem__.return_value = 1000

        self.exchange.get_market_data.return_value = mock_df
        self.exchange.get_realtime_price.return_value = 50500
        self.exchange.get_asset_balance.return_value = 10000
        self.ta.calculate_indicators.return_value = mock_df
        self.signal.generate_signal.return_value = "BUY"
        self.risk.calculate_unit_size.return_value = 0.1
        self.risk.can_entry.return_value = True

        loop.run_once()

        self.exchange.get_market_data.assert_called_with('BTCUSDT', '1h')
        self.execution.execute_order.assert_called_with('BTCUSDT', 'BUY', 0.1)
        self.assertEqual(loop.state['units_held'], 1)

    @patch('src.main_loop.JSONPersistence')
    def test_run_once_hold_flow(self, MockP):
        loop = self._make_loop(MockP)

        self.exchange.get_market_data.return_value = MagicMock()
        self.exchange.get_realtime_price.return_value = 50000
        self.signal.generate_signal.return_value = "HOLD"

        loop.run_once()
        self.execution.execute_order.assert_not_called()

if __name__ == '__main__':
    unittest.main()
