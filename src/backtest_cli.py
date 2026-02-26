import argparse
import os
import sys
from src.backtest.engine import BacktestEngine
from src.backtest.report import BacktestReporter

def main():
    parser = argparse.ArgumentParser(description="BATS Backtest CLI")
    parser.add_argument("--config", type=str, default="src/backtest/config_template.json", help="Path to backtest config JSON")
    parser.add_argument("--output", type=str, help="Path to save results JSON")
    parser.add_argument("--report", type=str, help="Display report from a results JSON file")
    
    args = parser.parse_args()

    if args.report:
        if os.path.exists(args.report):
            BacktestReporter.display(args.report)
        else:
            print(f"Error: Result file not found: {args.report}")
        return

    if not os.path.exists(args.config):
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)

    try:
        engine = BacktestEngine(args.config)
        results = engine.run()
        output_path = engine.save_results(results, args.output)
        
        # Automatically show report
        BacktestReporter.display(output_path)
        
    except Exception as e:
        print(f"An error occurred during backtest: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
