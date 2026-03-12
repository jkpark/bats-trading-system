# BATS Daily Report Procedure

## 1. Status Check
- Run `ps aux | grep "src/main.py" | grep -v grep` to ensure the process is alive.
- Check `bats_new.log` for recent heartbeats or errors.

## 2. Trade Summary
- Use `python3 src/backtest_cli.py --report` to get the latest performance metrics (if applicable) or check `state.json` for current positions.
- Summarize:
  - System Uptime/Status
  - Current Position (BTC Amount, Entry Price, PnL)
  - Daily/Total Profit (if available from logs/state)
  - Next anticipated action based on Turtle signals (S1/S2/S3)

## 3. Reporting
- Deliver to Discord channel: `channel:1475130555648446514`
- Tone: Concise, Technical, Architect style.
