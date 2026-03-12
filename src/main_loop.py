import time
import logging
import signal
from src.utils import JSONPersistence
from src.core import NotificationManager, DiscordNotificationChannel

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
        """A single iteration of the trading loop for all symbols."""
        try:
            symbols_config = self.config.get('symbols', [])
            if not symbols_config:
                logger.warning("No symbols configured, skipping iteration.")
                return

            # 1. Configuration & Global State (Optimization: Pull common configs out of loop)
            risk_cfg = self.config.get('risk', {})
            unit_risk_percent = risk_cfg.get('unit_risk_percent', 0.01)
            max_portfolio_heat = risk_cfg.get('max_portfolio_heat', 0.2)
            
            # 2. Global API Calls (Optimization: Fetch balance once per loop)
            usdt_balance = self.exchange.get_asset_balance("USDT")

            # 3. Update Portfolio-level Total Heat
            if 'symbols' not in self.state:
                self.state['symbols'] = {}
            
            total_heat = self.risk.calculate_total_heat(self.state['symbols'], unit_risk_percent)
            self.state['total_heat'] = total_heat

            for symbol_cfg in symbols_config:
                if not symbol_cfg.get('enabled', True):
                    continue
                
                symbol = symbol_cfg['name']
                interval = symbol_cfg.get('timeframe', '1h')
                
                # Get or create symbol-specific state
                sym_state = self.persistence.get_symbol_state(self.state, symbol)
                
                # 4. Fetch Market Data
                df = self.exchange.get_market_data(symbol, interval)
                current_price = self.exchange.get_realtime_price(symbol)
                
                if df is None or current_price is None:
                    logger.error(f"[{symbol}] Failed to fetch data, skipping.")
                    continue

                # 5. Technical Analysis
                df_analyzed = self.ta.calculate_indicators(df)
                
                # N_avg_20 for Volatility Cap
                if hasattr(df_analyzed, 'iloc'):
                    if df_analyzed.empty or 'N' not in df_analyzed.columns:
                        logger.warning(f"[{symbol}] Indicators not calculated correctly.")
                        continue
                    n_value = df_analyzed['N'].iloc[-1]
                    n_avg_20 = df_analyzed['N'].rolling(20).mean().iloc[-1]
                else:
                    n_value = df_analyzed[-1]['N']
                    n_avg_20 = sum(d['N'] for d in df_analyzed[-20:]) / len(df_analyzed[-20:])

                # 6. Signal Generation
                sig = self.signal_manager.generate_signal(df_analyzed, current_price, sym_state)
                
                if sig == "HOLD":
                    continue

                logger.info(f"[{symbol}] Signal Generated: {sig} at {current_price}")

                # 7. Risk Management & Execution
                if sig in ["BUY", "PYRAMID"]:
                    # Optimization: Shared usdt_balance used here
                    unit_size = self.risk.calculate_unit_size(usdt_balance, n_value, current_price, n_avg_20)
                    
                    if unit_size > 0 and self.risk.can_entry(self.state['total_heat'], max_portfolio_heat, unit_risk_percent):
                        success = self.execution.execute_order(symbol, "BUY", unit_size)
                        if success:
                            sym_state['units_held'] += 1
                            if 'entry_prices' not in sym_state: sym_state['entry_prices'] = []
                            sym_state['entry_prices'].append(current_price)
                            sym_state['current_n'] = n_value
                            
                            # Update total heat for next symbol in same iteration
                            self.state['total_heat'] += unit_risk_percent
                            self.persistence.save(self.state)
                            
                            logger.info(f"[{symbol}] Executed {sig}: {unit_size} units at {current_price}")
                            self.notifier.send_trade(sig, symbol, current_price, unit_size)
                        else:
                            logger.error(f"[{symbol}] Order execution failed.")
                    else:
                        logger.info(f"[{symbol}] Entry blocked by Risk Manager (Heat: {self.state['total_heat']:.2f})")
                
                elif sig == "EXIT":
                    if sym_state.get('units_held', 0) > 0:
                        success = self.execution.execute_order(symbol, "SELL", 0)
                        if success:
                            last_entry = sym_state['entry_prices'][-1] if sym_state.get('entry_prices') else current_price
                            trade_result = "win" if current_price > last_entry else "loss"
                            sym_state['last_trade_result'] = trade_result
                            
                            units_freed = sym_state['units_held']
                            sym_state['units_held'] = 0
                            sym_state['entry_prices'] = []
                            sym_state['current_n'] = 0
                            
                            # Update total heat
                            self.state['total_heat'] -= (units_freed * unit_risk_percent)
                            self.persistence.save(self.state)
                            
                            logger.info(f"[{symbol}] Executed EXIT at {current_price} (Result: {trade_result})")
                            self.notifier.send_trade("EXIT", symbol, current_price, 0, status=f"RESULT: {trade_result.upper()}")
                        else:
                            logger.error(f"[{symbol}] Exit order execution failed.")

        except Exception as e:
            logger.error(f"Error in main loop iteration: {e}")
            self.notifier.send_error(f"Main Loop Error: {str(e)}")

    def start(self):
        self.is_running = True
        logger.info("Starting BATS Main Loop (Multi-Symbol Mode)...")
        self.notifier.send_status(
            "System Online",
            "BATS Trading System has started successfully in Multi-Symbol mode."
        )
        try:
            while self.is_running:
                self.run_once()
                
                # Responsive sleep: check is_running every second
                system_cfg = self.config.get('system', {})
                polling_interval = system_cfg.get('polling_interval', 60)
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
