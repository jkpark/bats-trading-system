import os
import yaml
import logging
import json
import hashlib
import hmac
import time
import sys
from urllib import request, error
from src.core.modules_impl_lite import TechnicalAnalysisEngine, RiskManager
from src.core.signal_manager import TurtleSignalManager
from src.utils.persistence import JSONPersistence
from src.utils.notifier import DiscordNotifier

def setup_logging(log_file=None):
    """
    데몬 모드(log_file 지정)와 포그라운드 모드에 따른 로깅 설정
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    # Console Handler (Foreground)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (Daemon/File log)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        print(f"Logging to file: {log_file}")

    return logger

# --- Lite Exchange Provider (No Pandas/Binance-library dependency) ---
class LiteExchangeProvider:
    def __init__(self, api_key, api_secret, testnet=True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = 'https://testnet.binancefuture.com' if testnet else 'https://fapi.binance.com'
        self.logger = logging.getLogger("Exchange")

    def get_market_data(self, symbol, interval, limit=200):
        url = f"{self.base_url}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
        self.logger.info(f"API Request: GET {url}")
        try:
            with request.urlopen(url) as res:
                data = json.loads(res.read().decode())
                self.logger.info(f"API Response: Received {len(data)} klines for {symbol}")
                return [{
                    'timestamp': k[0],
                    'open': float(k[1]),
                    'high': float(k[2]),
                    'low': float(k[3]),
                    'close': float(k[4]),
                    'volume': float(k[5])
                } for k in data]
        except Exception as e:
            self.logger.error(f"Market Data Error: {e}")
            return None

    def get_realtime_price(self, symbol):
        url = f"{self.base_url}/fapi/v1/ticker/price?symbol={symbol}"
        try:
            with request.urlopen(url) as res:
                data = json.loads(res.read().decode())
                price = float(data['price'])
                self.logger.info(f"API Response: Current {symbol} price: {price}")
                return price
        except Exception as e:
            self.logger.error(f"Price Error: {e}")
            return None

    def get_asset_balance(self, asset):
        endpoint = '/fapi/v2/account'
        timestamp = int(time.time() * 1000)
        query = f"timestamp={timestamp}"
        signature = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        url = f"{self.base_url}{endpoint}?{query}&signature={signature}"
        
        self.logger.info(f"API Request: GET {endpoint} (Asset: {asset})")
        req = request.Request(url)
        req.add_header('X-MBX-APIKEY', self.api_key)
        try:
            with request.urlopen(req) as res:
                data = json.loads(res.read().decode())
                for a in data['assets']:
                    if a['asset'] == asset:
                        balance = float(a['walletBalance'])
                        self.logger.info(f"Balance Check: {asset} = {balance}")
                        return balance
        except Exception as e:
            self.logger.error(f"Balance Error: {e}")
        return 0.0

# --- Lite Execution Engine ---
class LiteExecutionEngine:
    def __init__(self, api_key, api_secret, testnet=True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = 'https://testnet.binancefuture.com' if testnet else 'https://fapi.binance.com'
        self.logger = logging.getLogger("Execution")

    def execute_order(self, symbol, side, quantity):
        endpoint = '/fapi/v1/order'
        timestamp = int(time.time() * 1000)
        query = f"symbol={symbol}&side={side.upper()}&type=MARKET&quantity={round(quantity, 3)}&timestamp={timestamp}"
        signature = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        url = f"{self.base_url}{endpoint}?{query}&signature={signature}"
        
        self.logger.info(f"TRADE EXECUTION: {side} {quantity} {symbol}")
        req = request.Request(url, method='POST')
        req.add_header('X-MBX-APIKEY', self.api_key)
        try:
            with request.urlopen(req) as res:
                result = json.loads(res.read().decode())
                self.logger.info(f"TRADE SUCCESS: OrderID {result.get('orderId')}, Status {result.get('status')}")
                return result
        except error.HTTPError as e:
            err_msg = e.read().decode()
            self.logger.error(f"TRADE ERROR: {e.code} - {err_msg}")
        return None

# --- Custom Main Loop ---
class LiteMainLoop:
    def __init__(self, config, exchange, ta, signal, risk, execution):
        self.config = config
        self.exchange = exchange
        self.ta = ta
        self.signal = signal
        self.risk = risk
        self.execution = execution
        self.persistence = JSONPersistence()
        self.state = self.persistence.load()
        self.notifier = DiscordNotifier()
        self.logger = logging.getLogger("MainLoop")

    def run_once(self):
        try:
            symbol = self.config['symbol']
            interval = self.config['interval']
            
            self.logger.info(f"--- Tick Start: {symbol} ({interval}) ---")
            
            data = self.exchange.get_market_data(symbol, interval)
            current_price = self.exchange.get_realtime_price(symbol)
            if not data or not current_price: 
                self.logger.warning("Skipping tick due to missing data.")
                return

            self.logger.info("Function: Calculating Indicators")
            analyzed = self.ta.calculate_indicators(data)
            n_val = analyzed[-1]['N']
            n_avg_20 = sum(d['N'] for d in analyzed[-20:]) / 20

            self.logger.info(f"Function: Generating Signal (Price: {current_price}, N: {n_val:.2f})")
            sig = self.signal.generate_signal(analyzed, current_price, self.state)
            
            if sig == "HOLD": 
                self.logger.info("Signal: HOLD - No action required.")
                return

            self.logger.info(f"SIGNAL CAPTURED: {sig}")
            if sig in ["BUY", "PYRAMID"]:
                balance = self.exchange.get_asset_balance("USDT")
                unit_size = self.risk.calculate_unit_size(balance, n_val, current_price, n_avg_20)
                self.logger.info(f"Function: Risk Check (Balance: {balance}, UnitSize: {unit_size})")
                
                if unit_size > 0:
                    res = self.execution.execute_order(symbol, "BUY", unit_size)
                    if res:
                        self.state['units_held'] = self.state.get('units_held', 0) + 1
                        if 'entry_prices' not in self.state: self.state['entry_prices'] = []
                        self.state['entry_prices'].append(current_price)
                        self.state['current_n'] = n_val
                        self.persistence.save(self.state)
                        self.notifier.send_trade_notification(sig, symbol, current_price, unit_size)
            elif sig == "EXIT":
                self.logger.info("Function: Executing EXIT")
                self.execution.execute_order(symbol, "SELL", 0) 
                self.state['units_held'] = 0
                self.state['entry_prices'] = []
                self.persistence.save(self.state)
                self.notifier.send_trade_notification("EXIT", symbol, current_price, 0)
                
            self.logger.info("--- Tick End ---")
        except Exception as e:
            self.logger.error(f"Loop Uncaught Exception: {e}", exc_info=True)
            self.notifier.send_error_notification(str(e))

    def start(self):
        self.logger.info("BATS Lite Mode Initialized - Market Watching Started")
        while True:
            self.run_once()
            time.sleep(self.config.get('polling_interval', 60))

def main():
    # CLI Argument check for daemon mode
    log_file = None
    if "--daemon" in sys.argv:
        log_file = "bats.log"
    
    logger = setup_logging(log_file)
    logger.info("==========================================")
    logger.info(" BATS TRADING SYSTEM - STARTING")
    logger.info("==========================================")
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    env = {}
    if os.path.exists('.env.local'):
        with open('.env.local', 'r') as f:
            for line in f:
                line = line.strip()
                if not line or '=' not in line or line.startswith('#'): continue
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()

    api_key = env.get('BINANCE_API_KEY')
    api_secret = env.get('BINANCE_API_SECRET')
    test_mode = config['system']['test_mode']

    exchange = LiteExchangeProvider(api_key, api_secret, testnet=test_mode)
    ta = TechnicalAnalysisEngine()
    signal = TurtleSignalManager(use_s1=True, use_s2=True, use_s3=True)
    risk = RiskManager()
    execution = LiteExecutionEngine(api_key, api_secret, testnet=test_mode)
    
    loop_config = {
        'symbol': config['strategies'][0]['symbol'],
        'interval': config['strategies'][0]['timeframe'],
        'polling_interval': config['system']['polling_interval']
    }
    
    bot = LiteMainLoop(loop_config, exchange, ta, signal, risk, execution)
    bot.start()

if __name__ == "__main__":
    main()
