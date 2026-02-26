import json
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger("BATS-Journal")


class TradeJournal:
    """
    Manages trade journal entries per docs/TRADE_JOURNAL_DESIGN.md.
    Auto-records basic info & strategy data on entry/pyramid/exit.
    """

    def __init__(self, journal_dir="logs/journal"):
        self.journal_dir = journal_dir
        os.makedirs(journal_dir, exist_ok=True)
        self._active_trade = None
        self._trade_counter = 0

    def _get_filepath(self, dt):
        return os.path.join(self.journal_dir, f"{dt.strftime('%Y-%m')}.json")

    def _load_month(self, filepath):
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r") as f:
            return json.load(f)

    def _save_month(self, filepath, entries):
        with open(filepath, "w") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)

    def _generate_trade_id(self, dt):
        self._trade_counter += 1
        return f"T-{dt.strftime('%Y%m%d')}-{self._trade_counter:03d}"

    # ── Entry ──
    def record_entry(self, symbol, direction, entry_price, unit_size, n_value,
                     system_mode, entry_trigger, ema_200, skip_rule_applied,
                     volatility_cap_applied, balance):
        now = datetime.now(timezone.utc)
        trade_id = self._generate_trade_id(now)

        self._active_trade = {
            # [가] Basic Info
            "trade_id": trade_id,
            "symbol": symbol,
            "direction": direction,
            "entry_time": now.isoformat(),
            "entry_price": entry_price,
            "exit_time": None,
            "exit_price": None,
            "position_size": unit_size,
            "total_units": 1,
            "pnl": None,
            "pnl_percent": None,
            "fees": 0,
            "holding_period": None,
            "balance_at_entry": balance,

            # [나] Strategy Record
            "system": system_mode,
            "entry_trigger": entry_trigger,
            "exit_trigger": None,
            "n_at_entry": n_value,
            "unit_size": unit_size,
            "pyramid_entries": [{"price": entry_price, "time": now.isoformat()}],
            "max_units": 1,
            "stop_loss_level": entry_price - (2 * n_value),
            "ema_200_at_entry": ema_200,
            "volatility_cap": volatility_cap_applied,
            "skip_rule": skip_rule_applied,

            # [다] Rule Compliance
            "signal_followed": True,
            "deviation_reason": None,
            "all_pyramids_executed": None,
            "stop_loss_honored": None,

            # [라] Post-Trade Review
            "what_went_well": None,
            "what_to_improve": None,
        }

        logger.info(f"Journal: Entry recorded [{trade_id}] {symbol} {direction} @ {entry_price}")
        return trade_id

    # ── Pyramid ──
    def record_pyramid(self, price, new_n=None):
        if not self._active_trade:
            logger.warning("Journal: No active trade to add pyramid.")
            return

        self._active_trade["total_units"] += 1
        self._active_trade["max_units"] = self._active_trade["total_units"]
        self._active_trade["pyramid_entries"].append({
            "price": price,
            "time": datetime.now(timezone.utc).isoformat()
        })

        # Update stop loss to last entry - 2N
        if new_n:
            self._active_trade["stop_loss_level"] = price - (2 * new_n)

        logger.info(f"Journal: Pyramid #{self._active_trade['total_units']} @ {price}")

    # ── Exit ──
    def record_exit(self, exit_price, exit_trigger, fees=0,
                    signal_followed=True, deviation_reason=None):
        if not self._active_trade:
            logger.warning("Journal: No active trade to close.")
            return None

        now = datetime.now(timezone.utc)
        entry_time = datetime.fromisoformat(self._active_trade["entry_time"])
        holding = now - entry_time

        # PnL calculation
        direction = self._active_trade["direction"]
        total_qty = self._active_trade["position_size"] * self._active_trade["total_units"]

        if direction == "LONG":
            avg_entry = sum(p["price"] for p in self._active_trade["pyramid_entries"]) / len(self._active_trade["pyramid_entries"])
            pnl = (exit_price - avg_entry) * total_qty
        else:
            avg_entry = sum(p["price"] for p in self._active_trade["pyramid_entries"]) / len(self._active_trade["pyramid_entries"])
            pnl = (avg_entry - exit_price) * total_qty

        balance = self._active_trade["balance_at_entry"]
        pnl_percent = (pnl / balance * 100) if balance > 0 else 0

        # Stop loss compliance check
        stop_level = self._active_trade["stop_loss_level"]
        if direction == "LONG":
            stop_honored = exit_price >= stop_level or exit_trigger == "hard_stop_2n"
        else:
            stop_honored = exit_price <= stop_level or exit_trigger == "hard_stop_2n"

        # Fill exit fields
        self._active_trade["exit_time"] = now.isoformat()
        self._active_trade["exit_price"] = exit_price
        self._active_trade["pnl"] = round(pnl, 2)
        self._active_trade["pnl_percent"] = round(pnl_percent, 4)
        self._active_trade["fees"] = fees
        self._active_trade["holding_period"] = str(holding)
        self._active_trade["exit_trigger"] = exit_trigger
        self._active_trade["signal_followed"] = signal_followed
        self._active_trade["deviation_reason"] = deviation_reason
        self._active_trade["stop_loss_honored"] = stop_honored

        # Persist to monthly file
        filepath = self._get_filepath(now)
        entries = self._load_month(filepath)
        entries.append(self._active_trade)
        self._save_month(filepath, entries)

        trade_id = self._active_trade["trade_id"]
        result = self._active_trade.copy()
        self._active_trade = None

        logger.info(f"Journal: Exit recorded [{trade_id}] PnL: {pnl:.2f} ({pnl_percent:.2f}%)")
        return result

    # ── Review (manual) ──
    def add_review(self, trade_id, what_went_well, what_to_improve):
        """Update the review fields for a completed trade."""
        now = datetime.now(timezone.utc)
        filepath = self._get_filepath(now)
        entries = self._load_month(filepath)

        for entry in entries:
            if entry["trade_id"] == trade_id:
                entry["what_went_well"] = what_went_well
                entry["what_to_improve"] = what_to_improve
                self._save_month(filepath, entries)
                logger.info(f"Journal: Review added to [{trade_id}]")
                return True

        logger.warning(f"Journal: Trade [{trade_id}] not found.")
        return False

    @property
    def active_trade(self):
        return self._active_trade
