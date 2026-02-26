# 전략 개선: 터틀 트레이딩 최적화 및 필터 강화

## 1. 룩백 기간 및 타임프레임 최적화
- **배경**: 암호화폐 시장의 높은 변동성과 노이즈를 제거하기 위해 더 긴 호흡의 설정이 필요함.
- **요구사항**:
    - 기본 타임프레임을 일봉(1d)으로 권장.
    - 진입(Entry): 90일 신고가 돌파 시 진입 (기존 20일/55일에서 확장).
    - 청산(Exit): 45일 저가 붕괴 시 청산 (기존 10일/20일에서 확장).

## 2. 시장 상황 필터 (Regime Filter) 추가
- **배경**: 횡보장에서의 잦은 손절(Whipsaw)을 방지하고 '추세의 질'을 검증.
- **요구사항**:
    - **ADX 필터**: ADX(Average Directional Index) 지표가 25 이상일 때만 돌파 신호를 신뢰. ADX 20 미만 구간은 매매 중단.
    - **200일 EMA 필터**: 현재 가격이 200일 EMA 위에 있을 때만 매수 신호 수용 (장기 상승 추세 확인).

## 3. 리스크 관리 최적화 (손절 폭 확대)
- **배경**: 암호화폐 특유의 높은 변동성으로 인해 기존 2N 손절은 너무 타이트함.
- **요구사항**:
    - 하드 손절(Hard Stop) 범위를 기존 **2N**에서 **5N**으로 확대.

## 4. 기능 인터페이스 정의 (Technical Requirements)
- `TechnicalAnalysisInterface`에 ADX 계산 로직 추가.
- `TurtleSignalManager`에 ADX 및 EMA 필터링 로직 통합.
- 전략 파라미터(Entry/Exit Window, Stop multiplier)를 설정 가능하도록 구조화.

---

## TDD 및 구현 결과 (2026-02-26)

### 1. 기술적 지표 확장
- `TechnicalAnalysisEngine`에 ADX(14), EMA(200), Donchian Channel(90/45) 계산 로직 추가 완료.
- ADX Smoothing 알고리즘 적용 (Wilder's Smoothing 방식).

### 2. 시그널 매니저 고도화
- `TurtleSignalManager`에 `S3`(90일 돌파) 모드 추가 및 기본 설정화.
- ADX 필터(기본 25) 및 EMA 200 트렌드 필터 적용.
- 손절 배수(Stop Multiplier)를 5N으로 확장하여 변동성 대응력 강화.

### 3. 검증 결과
- **테스트 코드**: `tests/test_strategy_upgrade.py`를 통해 ADX 계산, 5N 손절 로직, ADX 필터링 기능 검증 완료 (All Tests Passed).
- **백테스트 검증**: BTCUSDT 1일봉 기준, 개선된 전략 적용 시 승률 및 수익 안정성 향상 확인.
