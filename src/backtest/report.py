import json
from datetime import datetime

class BacktestReporter:
    @staticmethod
    def display(results_path):
        with open(results_path, 'r') as f:
            data = json.load(f)
        
        summary = data['summary']
        config = data['config']
        
        print("\n" + "="*50)
        print(" BATS TRADING SYSTEM - BACKTEST REPORT ".center(50, "="))
        print("="*50)
        
        print(f"\n[CONFIGURATION]")
        print(f"  Symbol:          {config['symbol']}")
        print(f"  Interval:        {config['interval']}")
        print(f"  Initial Balance: {config['initial_balance']:,.2f} USDT")
        print(f"  Risk per Trade:  {config['risk_per_trade']*100:.1f}%")
        
        print(f"\n[SUMMARY]")
        print(f"  Final Equity:    {summary['final_equity']:,.2f} USDT")
        print(f"  Total Return:    {summary['total_return_pct']:.2f}%")
        print(f"  Max Drawdown:    {summary['max_drawdown_pct']:.2f}%")
        print(f"  Win Rate:        {summary['win_rate_pct']:.2f}% ({summary['total_exits']} closed trades)")
        print(f"  Total Actions:   {summary['total_trades']}")
        
        print(f"\n[TRADE DETAILS]")
        print(f"  {'Timestamp':<20} | {'Symbol':<10} | {'Type':<8} | {'Price':<10} | {'Detail'}")
        print("-" * 78)
        
        for t in data['trades']:
            ts = datetime.fromtimestamp(t['timestamp']/1000).strftime('%Y-%m-%d %H:%M')
            sym = t.get('symbol', config['symbol'])
            if t['type'] == 'EXIT':
                detail = f"Gain: {t['gain']:>+10.2f} USDT"
            elif t.get('type') in ['BUY', 'PYRAMID']:
                detail = f"Unit: {t.get('units_held', '?')}, Bal: {t['balance']:,.2f}"
            else:
                detail = f"Bal: {t['balance']:,.2f}"
            print(f"  {ts:<20} | {sym:<10} | {t['type']:<8} | {t['price']:<10.2f} | {detail}")
            
        print("\n" + "="*50)
        print(" END OF REPORT ".center(50, "="))
        print("="*50 + "\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        BacktestReporter.display(sys.argv[1])
    else:
        print("Usage: python report.py <results_json_path>")
