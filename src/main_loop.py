import time
import logging
import signal
from src.utils.persistence import JSONPersistence
from src.core.notification_manager import NotificationManager
from src.core.discord_notification_channel import DiscordNotificationChannel

logger = logging.getLogger("BATS-Main")

class MainLoop:
    def __init__(self, config, exchange, ta, signal_manager, risk, execution):
        self.config = config
        self.exchange = exchange
        self.ta = ta
        self.signal_manager = signal_manager
        self.risk = risk
        self.execution = execution
        self.persistence = JSONPersistence()
        self.state = self.persistence.load()
        self.is_running = False
        self.notifier = self._create_notifier()
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        logger.info(f"Received signal {signum}. Initiating safe shutdown...")
        self.stop()

    def _create_notifier(self):
        """config.yaml의 notification 설정을 기반으로 NotificationManager를 생성한다."""
        notification_config = self.config.get('notification')
        if not notification_config:
            return NotificationManager(channel=None)

        channel_config = notification_config.get('channel', {})
        channel_type = channel_config.get('type')
        if not channel_type:
            return NotificationManager(channel=None)

        channel = None
        if channel_type == 'discord':
            webhook_url = channel_config.get('webhook_url')
            channel = DiscordNotificationChannel(webhook_url=webhook_url)
        else:
            logger.warning(f"Unknown notification channel type: {channel_type}")

        return NotificationManager(channel=channel)

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
            sig = self.signal_manager.generate_signal(df_analyzed, current_price, self.state)
            
            if sig == "HOLD":
                return

            logger.info(f"Signal Generated: {sig} at {current_price}")

            # 4. Risk Management & Execution
            if sig in ["BUY", "PYRAMID"]:
                balance = self.exchange.get_asset_balance("USDT")
                unit_size = self.risk.calculate_unit_size(balance, n_value, current_price, n_avg_20)
                
                # Simple logic for current heat: units_held / 4 (max 4)
                current_heat = (self.state.get('units_held', 0) * 0.01) # Assuming each unit is 1% risk
                
                if unit_size > 0 and self.risk.can_entry(current_heat, self.config.get('max_heat', 0.2)):
                    self.execution.execute_order(symbol, "BUY", unit_size)
                    self.state['units_held'] = self.state.get('units_held', 0) + 1
                    
                    if sig == "BUY":
                        if 'system_mode' not in self.state:
                             self.state['system_mode'] = 'S1'
                    
                    if 'entry_prices' not in self.state: self.state['entry_prices'] = []
                    self.state['entry_prices'].append(current_price)
                    self.state['current_n'] = n_value
                    self.persistence.save(self.state)
                    logger.info(f"Executed {sig}: {unit_size} units at {current_price}")
                    self.notifier.send_trade(sig, symbol, current_price, unit_size)
            
            elif sig == "EXIT":
                if self.state.get('units_held', 0) > 0:
                    self.execution.execute_order(symbol, "SELL", 0) 
                    
                    last_entry = self.state['entry_prices'][-1] if self.state.get('entry_prices') else current_price
                    trade_result = "win" if current_price > last_entry else "loss"
                    self.state['last_trade_result'] = trade_result
                    
                    self.state['units_held'] = 0
                    self.state['entry_prices'] = []
                    self.state['current_n'] = 0
                    self.persistence.save(self.state)
                    logger.info(f"Executed EXIT at {current_price} (Result: {trade_result})")
                    self.notifier.send_trade("EXIT", symbol, current_price, 0, status=f"RESULT: {trade_result.upper()}")

        except Exception as e:
            logger.error(f"Error in main loop iteration: {e}")
            self.notifier.send_error(f"Main Loop Error: {str(e)}")

    def start(self):
        self.is_running = True
        logger.info("Starting BATS Main Loop...")
        try:
            while self.is_running:
                self.run_once()
                
                # Responsive sleep: check is_running every second
                polling_interval = self.config.get('polling_interval', 60)
                for _ in range(polling_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
        finally:
            self.shutdown()

    def stop(self):
        self.is_running = False
        logger.info("Stopping BATS Main Loop...")

    def shutdown(self):
        """Final cleanup and persistence before exiting."""
        logger.info("Performing final shutdown tasks...")
        try:
            # 1. Save final state
            self.persistence.save(self.state)
            logger.info("Final state saved successfully.")
            
            # 2. Notify shutdown
            self.notifier.send_status("System Offline", "BATS Trading System has been shut down safely.")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("BATS System shutdown complete.")
