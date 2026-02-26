"""
Trade Journal Tests — docs/TRADE_JOURNAL_DESIGN.md compliance
"""
import unittest
import json
import os
import shutil
import tempfile
from src.utils.journal import TradeJournal


class TestJournalEntry(unittest.TestCase):
    """[가] 기본 정보 + [나] 전략 기록: 진입 시 자동 기록 검증"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.journal = TradeJournal(journal_dir=self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_entry_creates_active_trade(self):
        tid = self.journal.record_entry(
            symbol="BTCUSDT", direction="LONG", entry_price=87500,
            unit_size=0.1, n_value=1250, system_mode="S1",
            entry_trigger="20일 고가 돌파 (dc_20_high: 87200)",
            ema_200=82300, skip_rule_applied=False,
            volatility_cap_applied=False, balance=100000
        )
        trade = self.journal.active_trade
        self.assertIsNotNone(trade)
        self.assertTrue(tid.startswith("T-"))
        self.assertEqual(trade["symbol"], "BTCUSDT")
        self.assertEqual(trade["direction"], "LONG")
        self.assertEqual(trade["entry_price"], 87500)
        self.assertEqual(trade["total_units"], 1)

    def test_entry_strategy_fields(self):
        self.journal.record_entry(
            symbol="BTCUSDT", direction="LONG", entry_price=87500,
            unit_size=0.1, n_value=1250, system_mode="S1",
            entry_trigger="20일 고가 돌파", ema_200=82300,
            skip_rule_applied=False, volatility_cap_applied=False, balance=100000
        )
        trade = self.journal.active_trade
        self.assertEqual(trade["system"], "S1")
        self.assertEqual(trade["n_at_entry"], 1250)
        self.assertEqual(trade["stop_loss_level"], 87500 - 2 * 1250)  # 85000
        self.assertEqual(trade["ema_200_at_entry"], 82300)
        self.assertFalse(trade["volatility_cap"])
        self.assertFalse(trade["skip_rule"])

    def test_entry_review_fields_null(self):
        """[라] 회고 항목은 진입 시 null로 생성되어야 한다."""
        self.journal.record_entry(
            symbol="BTCUSDT", direction="LONG", entry_price=87500,
            unit_size=0.1, n_value=1250, system_mode="S1",
            entry_trigger="돌파", ema_200=82300,
            skip_rule_applied=False, volatility_cap_applied=False, balance=100000
        )
        trade = self.journal.active_trade
        self.assertIsNone(trade["what_went_well"])
        self.assertIsNone(trade["what_to_improve"])


class TestJournalPyramid(unittest.TestCase):
    """[나] 피라미딩 기록 검증"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.journal = TradeJournal(journal_dir=self.tmpdir)
        self.journal.record_entry(
            symbol="BTCUSDT", direction="LONG", entry_price=87500,
            unit_size=0.1, n_value=1250, system_mode="S1",
            entry_trigger="돌파", ema_200=82300,
            skip_rule_applied=False, volatility_cap_applied=False, balance=100000
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_pyramid_increments_units(self):
        self.journal.record_pyramid(88125, new_n=1250)
        trade = self.journal.active_trade
        self.assertEqual(trade["total_units"], 2)
        self.assertEqual(trade["max_units"], 2)
        self.assertEqual(len(trade["pyramid_entries"]), 2)

    def test_pyramid_updates_stop_loss(self):
        """피라미딩 시 손절가는 마지막 진입가 - 2N으로 갱신"""
        self.journal.record_pyramid(88125, new_n=1250)
        trade = self.journal.active_trade
        self.assertEqual(trade["stop_loss_level"], 88125 - 2 * 1250)  # 85625

    def test_multiple_pyramids(self):
        self.journal.record_pyramid(88125, new_n=1250)
        self.journal.record_pyramid(88750, new_n=1250)
        self.journal.record_pyramid(89375, new_n=1250)
        trade = self.journal.active_trade
        self.assertEqual(trade["total_units"], 4)
        self.assertEqual(len(trade["pyramid_entries"]), 4)


class TestJournalExit(unittest.TestCase):
    """[가] 청산 정보 + [다] 규칙 준수 자동 판정"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.journal = TradeJournal(journal_dir=self.tmpdir)
        self.journal.record_entry(
            symbol="BTCUSDT", direction="LONG", entry_price=87500,
            unit_size=0.1, n_value=1250, system_mode="S1",
            entry_trigger="돌파", ema_200=82300,
            skip_rule_applied=False, volatility_cap_applied=False, balance=100000
        )

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_exit_calculates_pnl(self):
        result = self.journal.record_exit(
            exit_price=92100,
            exit_trigger="10일 저가 이탈",
            fees=12.5
        )
        self.assertIsNotNone(result)
        # PnL = (92100 - 87500) * 0.1 * 1 = 460
        self.assertEqual(result["pnl"], 460.0)
        self.assertEqual(result["fees"], 12.5)

    def test_exit_calculates_holding_period(self):
        result = self.journal.record_exit(exit_price=90000, exit_trigger="청산")
        self.assertIsNotNone(result["holding_period"])

    def test_exit_persists_to_file(self):
        """청산 시 월별 JSON 파일에 저장되는지 확인"""
        self.journal.record_exit(exit_price=90000, exit_trigger="청산")
        files = os.listdir(self.tmpdir)
        self.assertTrue(any(f.endswith('.json') for f in files))

        json_file = [f for f in files if f.endswith('.json')][0]
        with open(os.path.join(self.tmpdir, json_file), "r") as f:
            entries = json.load(f)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["symbol"], "BTCUSDT")

    def test_exit_clears_active_trade(self):
        self.journal.record_exit(exit_price=90000, exit_trigger="청산")
        self.assertIsNone(self.journal.active_trade)

    def test_exit_signal_deviation(self):
        """[다] 규칙 불일치 시 사유 기록"""
        result = self.journal.record_exit(
            exit_price=90000, exit_trigger="수동 청산",
            signal_followed=False, deviation_reason="API 오류로 진입 지연"
        )
        self.assertFalse(result["signal_followed"])
        self.assertEqual(result["deviation_reason"], "API 오류로 진입 지연")

    def test_exit_pnl_with_pyramids(self):
        """피라미딩 포함 PnL 계산 (평균 단가 기반)"""
        self.journal.record_pyramid(88125, new_n=1250)
        result = self.journal.record_exit(exit_price=90000, exit_trigger="청산")
        # avg_entry = (87500 + 88125) / 2 = 87812.5
        # PnL = (90000 - 87812.5) * 0.1 * 2 = 437.5
        self.assertAlmostEqual(result["pnl"], 437.5)
        self.assertEqual(result["total_units"], 2)


class TestJournalReview(unittest.TestCase):
    """[라] 회고: 수동 입력 후 저장 검증"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.journal = TradeJournal(journal_dir=self.tmpdir)
        self.tid = self.journal.record_entry(
            symbol="BTCUSDT", direction="LONG", entry_price=87500,
            unit_size=0.1, n_value=1250, system_mode="S1",
            entry_trigger="돌파", ema_200=82300,
            skip_rule_applied=False, volatility_cap_applied=False, balance=100000
        )
        self.journal.record_exit(exit_price=90000, exit_trigger="청산")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_add_review(self):
        ok = self.journal.add_review(
            self.tid,
            what_went_well="S1 스킵 후 S2 진입으로 큰 추세를 잡았다",
            what_to_improve="피라미딩 3번째에서 주저하여 30초 지연 진입"
        )
        self.assertTrue(ok)

        # Verify persisted
        files = [f for f in os.listdir(self.tmpdir) if f.endswith('.json')]
        with open(os.path.join(self.tmpdir, files[0]), "r") as f:
            entries = json.load(f)
        self.assertEqual(entries[0]["what_went_well"], "S1 스킵 후 S2 진입으로 큰 추세를 잡았다")
        self.assertEqual(entries[0]["what_to_improve"], "피라미딩 3번째에서 주저하여 30초 지연 진입")

    def test_review_nonexistent_trade(self):
        ok = self.journal.add_review("T-FAKE-999", "good", "bad")
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main(verbosity=2)
