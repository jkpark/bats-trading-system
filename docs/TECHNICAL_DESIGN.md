# BATS (Binance Automated Trading System) - Technical Design

## 1. 개요 (Overview)
본 문서는 터틀 트레이딩 시스템(Turtle Trading System)의 기계적 규칙을 현대적으로 재해석하여 바이낸스 거래소에 적용하기 위한 기술 설계서입니다. 관심사 분리(SoC) 원칙을 준수하여 5개의 핵심 모듈로 구성합니다.

## 2. 핵심 기능 모듈 (Core Modules)

### 2.1. 데이터 핸들러 (Market Data Handler)
- **역할**: 바이낸스 REST/WebSocket API를 통한 데이터 수집 및 정규화.
- **I/O**: 
  - Input: Symbol, Interval (5m, 1h, 1d)
  - Output: OHLCV DataFrame

### 2.2. 기술적 분석 엔진 (Technical Analysis Engine)
- **지표 계산**:
  - **Volatility ($N$)**: 20일 ATR (Average True Range).
  - **Donchian Channels**: 20일/55일(진입용), 10일/20일(청산용) 채널.
  - **Trend Filter**: 200일 EMA (장기 추세 필터).

### 2.3. 신호 생성 및 상태 관리자 (Signal & State Manager)
- **진입 로직**:
  - **S1 (System 1)**: 20일 고가 돌파. (직전 매매 수익 시 Skip 규칙 적용)
  - **S2 (System 2)**: 55일 고가 돌파. (무조건 수용)
- **상태 관리**: 직전 매매 결과(승/패) 및 현재 보유 유닛 상태를 영속적으로 관리.

### 2.4. 리스크 및 자금 관리 모듈 (Risk & Position Sizer)
- **유닛 계산**: $Unit = \frac{Account\ Equity \times 0.01}{N \times Price\ per\ Point}$
- **현대적 보완**:
  - **Volatility Cap**: ATR이 최근 20일 평균의 1.5배 초과 시 유닛 50% 축소.
  - **Risk Reduction**: MDD 발생 시 가상 자산 규모 축소 적용.
  - **Portfolio Heat**: 전체 포트폴리오 리스크 노출 한도 제어.

### 2.5. 주문 실행 엔진 (Order Execution Engine)
- **기능**:
  - **Pyramiding**: $0.5N$ 상승 시마다 추가 진입 (최대 4유닛).
  - **Stop Loss**: 마지막 진입가 기준 $2N$ 하단 설정.
  - **Trailing Stop**: S1(10일 저가), S2(20일 저가) 이탈 시 전량 청산.

## 3. 데이터 영속성 (Persistence)
- **저장소**: SQLite 또는 JSON 기반 상태 저장 (로컬 환경 우선).
- **저장 항목**: 현재 보유 유닛 수, 평균 단가, S1 Skip 여부, $N$ 값 등.

## 4. 보안 및 설정
- `.env`: API Key 및 Secret 관리.
- `config.yaml`: 폴링 주기, 리스크 한도 등 런타임 매개변수 관리.
