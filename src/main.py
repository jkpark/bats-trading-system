import os
import sys
import logging
import yaml

# Ensure the project root is in sys.path for direct execution
# This allows running 'python3 src/main.py' from the project root without PYTHONPATH
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.utils import load_config
from src.main_loop import MainLoop
from src.core import ExchangeProvider, BinanceExecutionEngine, TechnicalAnalysisEngine, RiskManager, TurtleSignalManager

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger

def main():
    setup_logging()
    
    logging.info("==========================================")
    logging.info(" BATS TRADING SYSTEM - STARTING")
    logging.info("==========================================")
    
    # Load config using layered approach (Priority: config.local.yaml > config.yaml)
    config = load_config()
    if not config:
        logging.error("Failed to load configuration.")
        sys.exit(1)
    
    test_mode = config.get('system', {}).get('test_mode', True)
    
    # Core Components Initialization
    try:
        exchange = ExchangeProvider(testnet=test_mode)
        execution = BinanceExecutionEngine(exchange.client)
        logging.info("Successfully initialized Binance Exchange Provider and Execution Engine")
    except Exception as e:
        logging.error(f"Failed to initialize core components: {e}")
        sys.exit(1)

    ta = TechnicalAnalysisEngine()
    
    # Strategy parameters from config
    strategy_config = config.get('strategies', [{}])[0]
    strategy_params = strategy_config.get('strategy_params', {
        'use_s1': False,
        'use_s2': False,
        'use_s3': True,
        'adx_filter_threshold': 25.0,
        'stop_n_multiplier': 5.0
    })
    
    signal_manager = TurtleSignalManager(**strategy_params)
    risk = RiskManager()
    
    loop_config = config.copy()
    # Add flattened access for convenience in MainLoop.run_once if needed, 
    # but MainLoop seems to expect some keys at top level and some nested.
    # To maintain compatibility with existing MainLoop.run_once logic:
    loop_config['symbol'] = config['strategies'][0]['symbol']
    loop_config['interval'] = config['strategies'][0]['timeframe']
    loop_config['polling_interval'] = config['system']['polling_interval']
    loop_config['max_heat'] = config['risk']['max_portfolio_heat']
    
    # Start Main Loop
    bot = MainLoop(loop_config, exchange, ta, signal_manager, risk, execution)
    
    # Start bot (Signal handling is now internal to MainLoop)
    bot.start()

if __name__ == "__main__":
    main()
