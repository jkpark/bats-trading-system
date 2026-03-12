import json
import os
import logging

logger = logging.getLogger("BATS-Persistence")

class JSONPersistence:
    """
    Handles saving and loading the trading state to/from a JSON file.
    """
    def __init__(self, filepath="state.json"):
        self.filepath = filepath
        self.default_state = {
            "total_heat": 0.0,
            "symbols": {}
        }

    def get_symbol_state(self, state, symbol):
        """Helper to get a symbol's state or create it with defaults."""
        if "symbols" not in state:
            state["symbols"] = {}
        
        if symbol not in state["symbols"]:
            state["symbols"][symbol] = {
                "last_trade_result": "loss",
                "units_held": 0,
                "entry_prices": [],
                "system_mode": "S1",
                "current_n": 0
            }
        return state["symbols"][symbol]

    def load(self):
        if not os.path.exists(self.filepath):
            logger.info(f"No state file found at {self.filepath}, using defaults.")
            return self.default_state
        
        try:
            with open(self.filepath, "r") as f:
                state = json.load(f)
                logger.info(f"State loaded from {self.filepath}: {state}")
                return state
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return self.default_state

    def save(self, state):
        try:
            with open(self.filepath, "w") as f:
                json.dump(state, f, indent=4)
            logger.debug(f"State saved to {self.filepath}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
