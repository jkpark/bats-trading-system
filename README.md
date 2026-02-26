# BATS (Binance Automated Trading System)

BATS는 Binance API를 기반으로 한 암호화폐 자동 매매 시스템입니다. 현재 터틀 트레이딩(Turtle Trading) 전략을 기본으로 하며, 강력한 백테스트 엔진과 리포트 기능을 갖추고 있습니다.

## Project Structure
- `src/`: Source code
  - `core/`: Exchange provider, Risk manager, Signal manager (Turtle)
  - `backtest/`: Backtest engine, Reporter, Configurations
  - `strategies/`: Strategy implementations
  - `utils/`: Configuration and logging utilities
- `docs/`: Design and API documentation
- `config.yaml`: Runtime configuration
- `tests/`: Unit tests and integration tests

## Backtest (백테스트)
시스템에는 시뮬레이션을 위한 백테스트 엔진이 포함되어 있습니다.

### 실행 방법
```bash
# 기본 설정으로 실행
PYTHONPATH=. python3 src/backtest_cli.py --config src/backtest/config_template.json

# 특정 설정 파일로 실행
PYTHONPATH=. python3 src/backtest_cli.py --config src/backtest/config_btc_1d.json

# 기존 결과 리포트 출력
PYTHONPATH=. python3 src/backtest_cli.py --report backtest_results_YYYYMMDD_HHMMSS.json
```

### 설정 항목 (JSON)
백테스트 설정은 `src/backtest/*.json` 파일에서 관리합니다.
- `symbol`: 거래 쌍 (예: "BTCUSDT")
- `interval`: 캔들 타임프레임 ("1h", "1d" 등)
- `limit`: 분석할 과거 데이터 개수 (최대 1000)
- `initial_balance`: 초기 자본 (USDT)
- `risk_per_trade`: 회당 리스크 비율 (0.01 = 1%)

## Setup
1. `.env.local` 파일에 Binance API 및 Discord Webhook을 설정합니다.
   ```env
   BINANCE_API_KEY=your_key
   BINANCE_API_SECRET=your_secret
   DISCORD_WEBHOOK_URL=your_webhook_url
   ```
2. 의존성 설치: `pip install -r requirements.txt`
3. 시스템 실행: `python src/main.py` (실제 매매 모드)

## Notifications
Discord Webhook을 통한 실시간 매매 알림 기능이 내장되어 있습니다.
- **Trade Alerts**: 매매 체결 시 종목, 가격, 수량 알림.
- **System Logs**: 에러 발생 시 즉시 알림.
- 상세 내용은 [docs/notifier.md](docs/notifier.md)를 참고하세요.

## License
이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 실제 투자 손실에 대한 책임은 사용자에게 있습니다.
