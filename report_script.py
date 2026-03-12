import os
import sys
import yaml
import json
import logging
import pandas as pd
from datetime import datetime, timezone

# BATS 경로 추가
bats_dir = "/Users/jkpark/.openclaw/workspace-jeff/bats-trading-system"
os.chdir(bats_dir)
sys.path.append(os.path.join(bats_dir, "src"))

from src.utils import load_config, JSONPersistence
from src.core import ExchangeProvider, TechnicalAnalysisEngine, AdvancedTurtleManager

def get_bats_report():
    # 1. Config & State Load
    config = load_config()
    persistence = JSONPersistence()
    state = persistence.load()
    
    test_mode = config.get('system', {}).get('test_mode', True)
    symbol = config['strategies'][0]['symbol']
    interval = config['strategies'][0]['timeframe']
    
    # 2. Exchange Data
    try:
        exchange = ExchangeProvider(testnet=test_mode)
        df = exchange.get_market_data(symbol, interval)
        current_price = exchange.get_realtime_price(symbol)
        
        if df is None or current_price is None:
            print("Error: Failed to fetch market data.")
            return

        # 3. Indicator Calculation
        ta = TechnicalAnalysisEngine()
        df_analyzed = ta.calculate_indicators(df)
        last_row = df_analyzed.iloc[-1]
        
        # 4. Strategy Logic (AdvancedTurtleManager)
        strategy_config = config.get('strategies', [{}])[0]
        strategy_params = strategy_config.get('strategy_params', {})
        # AdvancedTurtleManager의 기본값이나 config에서 가져옴
        manager = AdvancedTurtleManager(**strategy_params)
        
        # Next Signal Preview
        next_sig = manager.generate_signal(df_analyzed, current_price, state.copy())

        # 5. Output Report
        print(f"### BATS Daily Report (Mode: {'TESTNET' if test_mode else 'REAL'})")
        print(f"- **현재 시각**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"- **대상 심볼**: {symbol} ({interval})")
        print(f"- **현재 가격**: ${current_price:,.2f}")
        print(f"\n#### [1] 시스템 상태 (state.json)")
        print(f"- **모드**: {state.get('system_mode', 'N/A')}")
        print(f"- **보유 유닛**: {state.get('units_held', 0)} / 4")
        print(f"- **진입 가격**: {state.get('entry_prices', [])}")
        print(f"- **직전 결과**: {state.get('last_trade_result', 'N/A')}")
        
        print(f"\n#### [2] 주요 기술 지표")
        print(f"- **N (ATR 20)**: {last_row['N']:.2f}")
        print(f"- **ADX (14)**: {last_row['ADX']:.2f} (Threshold: {strategy_params.get('adx_filter_threshold', 30)})")
        print(f"- **RSI (14)**: {last_row['rsi_14']:.2f} (Threshold: 55)")
        print(f"- **EMA 200**: ${last_row['ema_200']:,.2f}")
        print(f"- **Donchian (90H)**: ${last_row['dc_90_high']:,.2f}")
        print(f"- **Donchian (45L)**: ${last_row['dc_45_low']:,.2f} (S3 Exit)")
        
        print(f"\n#### [3] 전략 분석")
        if state.get('units_held', 0) > 0:
            last_entry = state['entry_prices'][-1]
            stop_multiplier = strategy_params.get('stop_n_multiplier', 3.0)
            hard_stop = last_entry - (stop_multiplier * state.get('current_n', 0))
            print(f"- **현재 포지션**: LONG 유지 중")
            print(f"- **Hard Stop (Last Entry - {stop_multiplier}N)**: ${hard_stop:,.2f}")
            print(f"- **Trailing Stop (DC 45L)**: ${last_row['dc_45_low']:,.2f}")
        else:
            print(f"- **현재 포지션**: 무포지션 (Cash)")
            
        print(f"- **다음 예상 시그널**: **{next_sig}**")
        
        # Log File Status
        log_size = os.path.getsize("bats_real.log")
        print(f"\n#### [4] 시스템 로그 상황")
        print(f"- `bats_real.log` 크기: {log_size} bytes")
        print(f"- 시스템 프로세스: {'RUNNING' if os.popen('ps aux | grep src/main.py | grep -v grep').read() else 'STOPPED'}")

    except Exception as e:
        print(f"Error generating report: {e}")

if __name__ == "__main__":
    get_bats_report()
