# BATS (Binance Automated Trading System)

BATS는 Binance API를 기반으로 한 암호화폐 자동 매매 시스템입니다. 터틀 트레이딩(Turtle Trading) 전략을 기본으로 하며, 강력한 백테스트 엔진과 안정적인 백그라운드 서비스 운영 환경을 갖추고 있습니다.

## 주요 특징

### 1. 서비스 아키텍처 (`src/main.py`, `src/main_loop.py`)
- **Main Loop 중심 설계**: `src/main_loop.py`에서 시장 감시, 지표 계산, 신호 생성, 리스크 관리, 체결 로직을 총괄합니다.
- **Graceful Shutdown**: `SIGINT`, `SIGTERM` 시그널을 처리하여 안전하게 상태를 저장하고 시스템을 종료합니다.
- **Notification Manager**: Discord 등 다양한 채널로 실시간 매매 현황 및 시스템 상태 알림을 전송합니다.

### 2. 전략 및 리스크 관리 (`src/core/`)
- **Indicator Engine**: ATR($N$), Donchian Channels, EMA-200, ADX 등을 계산합니다.
- **Risk Manager**: 1% 리스크 모델, Volatility Cap, 포트폴리오 열기(Heat) 제한 로직이 구현되어 있습니다.
- **Signal Manager**: Turtle S1/S2 시스템 및 필터링 로직을 담당합니다.

## 설치 및 설정 (Setup)

### 1. 설정 파일 관리
BATS는 계층형 설정 방식을 사용합니다. (우선순위: `config.local.yaml` > `config.yaml`)
1. `config.local.yaml.example` 파일을 복사하여 `config.local.yaml`을 생성합니다.
2. `config.local.yaml`에 Binance API Key, Secret 및 Discord Webhook URL을 설정합니다.

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 시스템 서비스 등록 (Linux systemd)
시스템 부팅 시 자동 실행 및 안정적인 운영을 위해 `setup_service.sh`를 제공합니다.
```bash
# 서비스 등록 및 시작 (sudo 권한 필요)
./setup_service.sh
```

## 운영 및 실행

### 서비스 관리 (`run.sh`)
서비스 재시작, 의존성 체크, 빌드 아티팩트 정리를 한 번에 수행하는 `run.sh`를 사용하세요.
```bash
./run.sh
```

### 실시간 모니터링
로그 파일을 통해 시스템 동작을 실시간으로 확인할 수 있습니다.
```bash
tail -f bats.log
```

## 백테스트 (Backtest)
과거 데이터를 기반으로 전략의 수익성을 시뮬레이션할 수 있습니다.

### 실행 방법
```bash
# 기본 설정으로 실행
PYTHONPATH=. python3 src/backtest_cli.py --config src/backtest/config_template.json

# 특정 설정 파일로 실행
PYTHONPATH=. python3 src/backtest_cli.py --config src/backtest/config_btc_1d.json

# 기존 결과 리포트 출력
PYTHONPATH=. python3 src/backtest_cli.py --report backtest_results_YYYYMMDD_HHMMSS.json
```

## Documentation
- [DESIGN.md](docs/DESIGN.md): 시스템 설계 원칙 및 구조
- [STRATEGY_UPGRADE.md](docs/STRATEGY_UPGRADE.md): 전략 개선 사항
- [notifier.md](docs/notifier.md): 알림 시스템 상세 설정

## License
이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 실제 투자 손실에 대한 책임은 사용자에게 있습니다.
