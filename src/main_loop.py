import time
import logging
from src.core.interfaces import ExchangeProviderInterface, TechnicalAnalysisInterface, SignalManagerInterface, RiskManagerInterface, ExecutionEngineInterface
from src.utils.persistence import JSONPersistence
from src.utils.notifier import DiscordNotifier

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BATS-Main")

class MainLoop:
    def __init__(self, config, exchange, ta, signal, risk, execution):
        self.config = config
        self.exchange = exchange
        self.ta = ta
        self.signal = signal
        self.risk = risk
        self.execution = execution
        self.persistence = JSONPersistence()
        self.state = self.persistence.load()
        self.is_running = False
        self.notifier = DiscordNotifier()

    def run_once(self):
        """A single iteration of the trading loop."""
        try:
            symbol = self.config.get('symbol', 'BTCUSDT')
            interval = self.config.get('interval', '1h')
            
            # 1. Fetch Market Data
            df = self.exchange.get_market_data(symbol, interval)
            current_price = self.exchange.get_realtime_price(symbol)
            
            if df is None or current_price is None:
                logger.error("Failed to fetch data, skipping this tick.")
                return

            # 2. Technical Analysis
            df_analyzed = self.ta.calculate_indicators(df)
            
            # N_avg_20 for Volatility Cap (Pandas or Lite list)
            if hasattr(df_analyzed, 'iloc'): # Pandas
                n_value = df_analyzed['N'].iloc[-1]
                n_avg_20 = df_analyzed['N'].rolling(20).mean().iloc[-1]
            else: # Lite (List of Dicts)
                n_value = df_analyzed[-1]['N']
                n_avg_20 = sum(d['N'] for d in df_analyzed[-20:]) / len(df_analyzed[-20:])

            # 3. Signal Generation
            signal = self.signal.generate_signal(df_analyzed, current_price, self.state)
            
            if signal == "HOLD":
                return

            logger.info(f"Signal Generated: {signal} at {current_price}")

            # 4. Risk Management & Execution
            if signal in ["BUY", "PYRAMID"]:
                balance = self.exchange.get_asset_balance("USDT")
                unit_size = self.risk.calculate_unit_size(balance, n_value, current_price, n_avg_20)
                
                # Simple logic for current heat: units_held / 4 (max 4)
                current_heat = (self.state['units_held'] * 0.01) # Assuming each unit is 1% risk
                
                if unit_size > 0 and self.risk.can_entry(current_heat, self.config.get('max_heat', 0.2)):
                    self.execution.execute_order(symbol, "BUY", unit_size)
                    self.state['units_held'] += 1
                    
                    # Set system mode based on which breakout was hit (S1 or S2)
                    # For simplicity, we can check the price against DC channels here or pass it from signal
                    if signal == "BUY":
                        # If it's the first unit, we need to know if it was S1 or S2
                        # This is a bit tricky without modifying generate_signal return value.
                        # For now, let's assume S1 if not specified.
                        if 'system_mode' not in self.state:
                             self.state['system_mode'] = 'S1'
                    
                    # Track entry price for future Stop Loss/Pyramiding
                    if 'entry_prices' not in self.state: self.state['entry_prices'] = []
                    self.state['entry_prices'].append(current_price)
                    self.state['current_n'] = n_value # Store N for stop loss
                    self.persistence.save(self.state)
                    logger.info(f"Executed {signal}: {unit_size} units at {current_price}")
                    self.notifier.send_trade_notification(signal, symbol, current_price, unit_size)
            
            elif signal == "EXIT":
                if self.state['units_held'] > 0:
                    # In a real system, we'd calculate total quantity to sell
                    self.execution.execute_order(symbol, "SELL", 0) 
                    
                    # Calculate win/loss for Skip Rule
                    last_entry = self.state['entry_prices'][-1] if self.state['entry_prices'] else current_price
                    trade_result = "win" if current_price > last_entry else "loss"
                    self.state['last_trade_result'] = trade_result
                    
                    self.state['units_held'] = 0
                    self.state['entry_prices'] = []
                    self.state['current_n'] = 0
                    self.persistence.save(self.state)
                    logger.info(f"Executed EXIT at {current_price} (Result: {trade_result})")
                    self.notifier.send_trade_notification("EXIT", symbol, current_price, 0, status=f"RESULT: {trade_result.upper()}")

        except Exception as e:
            logger.error(f"Error in main loop iteration: {e}")
            self.notifier.send_error_notification(f"Main Loop Error: {str(e)}")

    def start(self):
        self.is_running = True
        logger.info("Starting BATS Main Loop...")
        while self.is_running:
            self.run_once()
            sleep_time = self.config.get('polling_interval', 60)
            time.sleep(sleep_time)

    def stop(self):
        self.is_running = False
        logger.info("Stopping BATS Main Loop...")
