import json
import sys
from datetime import datetime

class BacktestReporter:
    @staticmethod
    def print_report(results):
        config = results.get('config', {})
        summary = results.get('summary', {})
        trades = results.get('trades', [])
        
        # Period Calculation
        start_ts = trades[0]['timestamp'] if trades else 0
        end_ts = trades[-1]['timestamp'] if trades else 0
        start_date = datetime.fromtimestamp(start_ts / 1000).strftime('%Y-%m-%d') if start_ts else "N/A"
        end_date = datetime.fromtimestamp(end_ts / 1000).strftime('%Y-%m-%d') if end_ts else "N/A"

        print("\n" + "="*50)
        print("===== BATS TRADING SYSTEM - BACKTEST REPORT =====")
        print("="*50)

        print("\n[CONFIGURATION]")
        print(f"  Symbol:          {config.get('symbol')}")
        print(f"  Interval:        {config.get('interval')}")
        print(f"  Period:          {start_date} ~ {end_date}")
        print(f"  Strategy:        {config.get('strategy')}")
        
        strategy_params = config.get('strategy_params', {})
        params_str = ", ".join([f"{k}={v}" for k, v in strategy_params.items()])
        print(f"  Strategy Params: {params_str}")

        print("\n[SUMMARY]")
        print(f"  Initial Balance: {summary.get('initial_balance', 0):,.2f} USDT")
        print(f"  Final Equity:    {summary.get('final_equity', 0):,.2f} USDT")
        print(f"  Total Return:    {summary.get('total_return_pct', 0):.2f}%")
        print(f"  Max Drawdown:    {summary.get('max_drawdown_pct', 0):.2f}%")
        print(f"  Win Rate:        {summary.get('win_rate_pct', 0):.2f}% ({summary.get('total_exits', 0)} closed trades)")
        print(f"  Total Actions:   {summary.get('total_trades', 0)}")

        print("\n[TRADE DETAILS]")
        print(f"{'Timestamp':<20} | {'Type':<8} | {'Price':<10} | {'Units':<5} | {'Result'}")
        print("-" * 75)
        
        for trade in trades:
            ts = datetime.fromtimestamp(trade['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M')
            ttype = trade['type']
            price = f"{trade['price']:.2f}"
            units = str(trade.get('units_held', '-'))
            
            result = ""
            if ttype == 'EXIT':
                gain = trade.get('gain', 0)
                result = f"{gain:+.2f} USDT"
                units = "0"
            
            print(f"{ts:<20} | {ttype:<8} | {price:<10} | {units:<5} | {result}")

        print("\n" + "="*50)
        print("================= END OF REPORT ==================")
        print("="*50 + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
            BacktestReporter.print_report(data)
