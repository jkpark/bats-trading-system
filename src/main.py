import os
import sys
import logging
import yaml

# Ensure the project root is in sys.path for direct execution
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
    logging.info(" BATS TRADING SYSTEM - MULTI-SYMBOL")
    logging.info("==========================================")
    
    # Load config using layered approach
    config = load_config()
    if not config:
        logging.error("Failed to load configuration.")
        sys.exit(1)
    
    system_cfg = config.get('system', {})
    test_mode = system_cfg.get('test_mode', True)
    
    # Core Components Initialization
    try:
        exchange = ExchangeProvider(testnet=test_mode)
        execution = BinanceExecutionEngine(exchange.client)
        logging.info(f"Initialized Binance Exchange Provider (Testnet: {test_mode})")
    except Exception as e:
        logging.error(f"Failed to initialize core components: {e}")
        sys.exit(1)

    ta = TechnicalAnalysisEngine()
    
    # Strategy parameters from config
    strategy_params = config.get('strategy_params', {
        'use_s1': False,
        'use_s2': False,
        'use_s3': True,
        'adx_filter_threshold': 25.0,
        'stop_n_multiplier': 5.0
    })
    
    signal_manager = TurtleSignalManager(**strategy_params)
    risk = RiskManager()
    
    # Start Main Loop
    bot = MainLoop(config, exchange, ta, signal_manager, risk, execution)
    
    # Start bot
    bot.start()

if __name__ == "__main__":
    main()
