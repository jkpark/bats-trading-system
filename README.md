# BATS (Binance Automated Trading System)

BATS는 Binance API를 기반으로 한 암호화폐 자동 매매 시스템입니다. 터틀 트레이딩(Turtle Trading) 전략을 기본으로 하며, 강력한 백테스트 엔진과 안정적인 다중 심볼(Multi-Symbol) 운영 환경을 갖추고 있습니다.

## 주요 특징

### 1. 서비스 아키텍처 (`src/main.py`, `src/main_loop.py`)
- **다중 심볼 오케스트레이션**: `MainLoop`가 설정된 여러 코인(BTC, ETH 등)을 순회하며 독립적으로 상태를 관리하고 매매를 집행합니다.
- **API 호출 최적화**: 루프당 잔고 조회를 1회로 통합하여 API Rate Limit를 방지하고 처리 속도를 극대화했습니다.
- **Graceful Shutdown**: `SIGINT`, `SIGTERM` 시그널 처리로 안전한 상태 저장 및 종료를 보장합니다.
- **Notification Manager**: Discord를 통해 실시간 매매 현황 및 시스템 상태 알림을 전송합니다.

### 2. 전략 및 리스크 관리 (`src/core/`)
- **Advanced Turtle Strategy**: ATR($N$), Donchian Channels, EMA-200, ADX 필터에 RSI 및 거래량 필터를 결합한 고도화된 전략을 지원합니다.
- **포트폴리오 리스크 제어**: 개별 유닛 리스크 관리와 더불어 전체 포트폴리오 노출도(Total Heat)를 제한하는 기능을 포함합니다.
- **Volatility Cap**: 변동성 급증 시 유닛 사이즈를 자동으로 조절하여 자산을 보호합니다.

## 설치 및 설정 (Setup)

### 1. 설정 파일 관리
BATS는 계층형 설정 방식을 사용합니다. (우선순위: `config.local.yaml` > `config.yaml`)
1. `config.local.yaml.example` 파일을 복사하여 `config.local.yaml`을 생성합니다.
2. `config.local.yaml`에 Binance API Key, Secret 및 Discord Webhook URL을 설정합니다.
3. `config.yaml`의 `symbols` 섹션에 거래할 코인 리스트를 추가합니다.

### 2. 의존성 설치
```bash
python3 -m pip install -r requirements.txt
```

## 운영 및 실행

### 서비스 관리 (`run.sh`)
서비스 재시작, 의존성 체크, 빌드 아티팩트 정리를 수행하는 `run.sh`를 사용하세요.
```bash
./run.sh
```

### 실시간 모니터링
로그 파일을 통해 시스템 동작을 실시간으로 확인할 수 있습니다.
```bash
tail -f bats.log
```

## 백테스트 (Backtest)
다중 심볼 구성을 포함한 과거 데이터 시뮬레이션을 지원합니다.

### 실행 방법
```bash
# 다중 심볼 통합 백테스트 실행
PYTHONPATH=. python3 src/multi_backtest.py src/backtest/config_multi_1000d.json
```

## Documentation
- [MULTI_SYMBOL_DESIGN.md](docs/MULTI_SYMBOL_DESIGN.md): 다중 심볼 확장 설계 원칙
- [DAILY_REPORT.md](docs/DAILY_REPORT.md): 정기 보고 절차 및 가이드
- [DESIGN.md](docs/DESIGN.md): 시스템 기본 아키텍처

## License
이 프로젝트는 교육 및 연구 목적으로 제작되었습니다. 실제 투자 손실에 대한 책임은 사용자에게 있습니다.
