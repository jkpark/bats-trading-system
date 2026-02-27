import os
import yaml
import logging
import sys
from src.main_loop import MainLoop
from src.core.exchange_provider import ExchangeProvider
from src.core.modules_impl import BinanceExecutionEngine
from src.core.modules_impl import TechnicalAnalysisEngine, RiskManager
from src.core.signal_manager import TurtleSignalManager

def setup_logging(log_file=None):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger

def main():
    log_file = "bats.log" if "--daemon" in sys.argv else None
    setup_logging(log_file)
    
    logging.info("==========================================")
    logging.info(" BATS TRADING SYSTEM - STARTING")
    logging.info("==========================================")
    
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    test_mode = config.get('system', {}).get('test_mode', True)
    
    # Binance library is mandatory
    try:
        exchange = ExchangeProvider(testnet=test_mode)
        execution = BinanceExecutionEngine(exchange.client)
        logging.info("Successfully initialized Binance Exchange Provider and Execution Engine")
    except Exception as e:
        logging.error(f"Failed to initialize core components: {e}")
        sys.exit(1)

    ta = TechnicalAnalysisEngine()
    signal = TurtleSignalManager(
        use_s1=config.get('strategies', [{}])[0].get('use_s1', True),
        use_s2=config.get('strategies', [{}])[0].get('use_s2', True)
    )
    risk = RiskManager()
    
    loop_config = {
        'symbol': config['strategies'][0]['symbol'],
        'interval': config['strategies'][0]['timeframe'],
        'polling_interval': config['system']['polling_interval'],
        'max_heat': config['risk']['max_portfolio_heat']
    }
    
    bot = MainLoop(loop_config, exchange, ta, signal, risk, execution)
    
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.stop()

if __name__ == "__main__":
    main()
