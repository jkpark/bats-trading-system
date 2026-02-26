import os
import yaml
import logging
from src.main_loop import MainLoop
from src.core.exchange_provider import ExchangeProvider
from src.core.modules_impl_lite import TechnicalAnalysisEngine, RiskManager
from src.core.modules_impl import BinanceExecutionEngine
from src.core.signal_manager import TurtleSignalManager

# Simplified Execution Engine for Demo
class MockExecutionEngine:
    def execute_order(self, symbol, side, quantity):
        print(f"!!! MOCK ORDER EXECUTED: {side} {quantity} {symbol} !!!")

def main():
    # 1. Load Config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # 2. Initialize Modules
    # Use test_mode from config
    test_mode = config.get('system', {}).get('test_mode', True)
    exchange = ExchangeProvider(testnet=test_mode)
    ta = TechnicalAnalysisEngine()
    signal = TurtleSignalManager()
    risk = RiskManager()
    
    # Use real execution engine if configured, else mock
    if config.get('system', {}).get('real_execution', False):
        execution = BinanceExecutionEngine(exchange.client)
    else:
        execution = MockExecutionEngine()
    
    # 3. Setup Main Loop
    # Flatten config for main loop
    loop_config = {
        'symbol': config['strategies'][0]['symbol'],
        'interval': config['strategies'][0]['timeframe'],
        'polling_interval': config['system']['polling_interval'],
        'max_heat': config['risk']['max_portfolio_heat']
    }
    
    bot = MainLoop(loop_config, exchange, ta, signal, risk, execution)
    
    # 4. Start
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.stop()

if __name__ == "__main__":
    main()
