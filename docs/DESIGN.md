# Binance Automated Trading System Design (BATS)

## 1. 개요 (Overview)
본 프로젝트는 바이낸스 REST API를 활용하여 전략 기반 암호화폐 자동매매를 수행하는 시스템입니다. **Strategy Pattern**을 통한 유연한 전략 교체와 **N-based Unit Sizing**을 통한 정교한 리스크 관리를 핵심 가치로 합니다.

## 2. 핵심 설계 원칙
- **Modularization**: 거래소 통신, 전략 연산, 리스크 관리, 주문 실행 로직을 엄격히 분리합니다.
- **Strategy Pluggability**: 모든 전략은 동일한 인터페이스를 상속받아 설정 변경만으로 교체 가능해야 합니다.
- **Safety First**: 모든 주문은 실행 전 리스크 관리 모듈의 검증을 통과해야 합니다.
- **Dynamic Config**: 시스템 재시작 없이 런타임 중에 폴링 주기 등 주요 설정을 변경할 수 있어야 합니다.

## 3. 시스템 아키텍처 (Layered Architecture)

### 3.1. Layer 구성
1.  **Data Provider Layer**: 실시간 가격 모니터링 및 전략별 타임프레임 데이터 수집.
2.  **Strategy Layer**: 기술적 분석을 통한 매수/매도 시그널 생성.
3.  **Risk Management Layer**: 유닛 사이즈 계산, 포트폴리오 열기(Heat) 제어 및 리스크 검증.
4.  **Execution Layer**: 바이낸스 API를 통한 실제 주문 집행.
5.  **Configuration Module**: 런타임 설정 관리.

---

## 4. 핵심 기능 및 I/O 정의

### 4.1. `ConfigManager` (설정 관리)
- **역할**: 외부 설정 파일(YAML/JSON)을 감시하고 런타임에 설정을 갱신합니다.
- **주요 설정**: `POLLING_INTERVAL` (초 단위), `MAX_PORTFOLIO_HEAT` (%), `DEFAULT_LEVERAGE` 등.

### 4.2. `ExchangeProvider` (데이터 공급자)
- **기능: `get_realtime_price(symbol)`**
    - **역할**: 단기 급락 대응을 위해 가능한 실시간에 가깝게 시세를 확인합니다.
    - **Input**: `symbol`
    - **Output**: `float` (Current Price)
- **기능: `get_ohlcv(symbol, interval)`**
    - **역할**: 전략 분석용 히스토리컬 데이터를 가져옵니다.

### 4.3. `RiskManager` (고급 리스크 관리)
- **기능: `calculate_unit_size(symbol, volatility_n)`**
    - **역할**: 계좌 잔고와 변동성($N$, ATR 등)을 바탕으로 1개 유닛의 크기를 계산합니다.
    - **Input**: `balance`, `N`
    - **Output**: `float` (Position Size)
- **기능: `check_portfolio_heat()`**
    - **역할**: 현재 진입된 모든 포지션의 총 리스크 합계가 한도(Heat limit)를 넘지 않는지 검증합니다.
    - **Output**: `bool` (진입 가능 여부)

### 4.4. `StrategyInterface` (전략 추상 클래스)
- **기능: `evaluate(data, current_price)`**
    - **Input**: `DataFrame` (분석용), `float` (실시간 가격)
    - **Output**: `Signal` (BUY/SELL/HOLD/EXIT)
    - **특이사항**: 중장기 전략이라도 `current_price`를 통해 실시간 급락 시 손절(Exit) 시그널을 발생시킬 수 있어야 합니다.

---

## 5. 데이터 및 제어 흐름 (Control Flow)
1.  **Main Loop**: `ConfigManager`에서 정의된 `POLLING_INTERVAL` 주기로 실행됩니다.
2.  **Data Fetch**: `ExchangeProvider`가 실시간 가격과 전략별 주기에 맞는 데이터를 가져옵니다.
3.  **Strategy Evaluation**: 전략이 시그널을 생성합니다. 장기 전략도 실시간 가격을 체크하여 비상 대응 로직을 수행합니다.
4.  **Risk Verification**:
    - `RiskManager`가 변동성($N$)을 기반으로 유닛 크기를 결정합니다.
    - 현재 포트폴리오의 전체 리스크(Heat)가 한도 내에 있는지 확인합니다.
5.  **Execution**: 모든 검증을 통과하면 `OrderExecutor`가 주문을 실행합니다.

## 6. 보안 및 환경 설정
- **API Key**: `.env` 파일 관리.
- **Config Monitoring**: 설정 파일의 변경을 감지하는 Watchdog 패턴 적용 권장.

## 7. 향후 확장 고려 사항
- 실시간성 강화를 위한 WebSocket 통합.
- 텔레그램 기반 원격 설정 변경 및 알림.
