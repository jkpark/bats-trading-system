# BATS Multi-Symbol Design 초안

이 문서는 BATS(Binance Automated Trading System)를 단일 심볼에서 다중 심볼(Multi-symbol) 지원 구조로 확장하기 위한 설계 초안을 다룹니다.

## 1. 설정 파일 (config.yaml) 구조 제안

기존의 단일 심볼 설정을 `symbols` 리스트 구조로 확장하여 여러 자산에 대한 설정을 유연하게 관리합니다.

```yaml
system:
  polling_interval: 60
  real_execution: true

risk:
  max_portfolio_heat: 0.2  # 포트폴리오 전체 최대 리스크 (20%)
  unit_risk_percent: 0.01   # 유닛당 기본 리스크 (1%)

# 다중 심볼 리스트
symbols:
  - name: "BTCUSDT"
    enabled: true
    leverage: 10
    timeframe: "4h"
    strategy: "TurtleTrendFollowing"
  - name: "ETHUSDT"
    enabled: true
    leverage: 10
    timeframe: "4h"
    strategy: "TurtleTrendFollowing"

notification:
  # ... (기존과 동일)
```

## 2. 상태 관리 (state.json) 구조

각 심볼의 독립적인 상태를 관리하기 위해 `symbols` 키 아래에 심볼별 상태를 딕셔너리 형태로 저장합니다.

```json
{
  "total_heat": 0.01,
  "symbols": {
    "BTCUSDT": {
      "units_held": 1,
      "entry_prices": [65000.5],
      "last_trade_result": "win",
      "system_mode": "S1",
      "current_n": 120.5
    },
    "ETHUSDT": {
      "units_held": 0,
      "entry_prices": [],
      "last_trade_result": "loss",
      "system_mode": "S1",
      "current_n": 0
    }
  }
}
```

## 3. MainLoop 로직 흐름

`MainLoop`의 `run_once`는 전체 포트폴리오의 리스크를 먼저 계산한 후, 설정된 심볼 리스트를 순회하며 각 심볼을 처리합니다.

### 처리 흐름:
1.  **Total Heat 계산**: 모든 심볼의 `units_held`를 기반으로 현재 총 리스크 노출도(Total Heat)를 산출합니다.
2.  **심볼 순회**: `config.symbols` 리스트를 반복문으로 순회합니다.
3.  **심볼별 독립 처리**:
    *   해당 심볼의 마켓 데이터 및 기술 지표 계산.
    *   심볼 전용 상태(`state['symbols'][symbol]`)를 기반으로 시그널 생성.
4.  **리스크 제어 및 실행**:
    *   새로운 진입(BUY) 시그널 발생 시, `Total Heat + Unit Risk`가 `max_portfolio_heat`를 초과하지 않는지 검증.
    *   검증 통과 시 주문 실행 및 심볼별 상태 업데이트.

## 4. 포트폴리오 리스크 관리 (Total Heat)

*   **개념**: 포트폴리오 차원에서 노출된 총 리스크의 합계를 제한하여, 특정 시장 상황에서의 과도한 손실을 방지합니다.
*   **계산식**: `Total Heat = Σ (해당 심볼의 유닛 수 × 유닛당 리스크 %)`
*   **제어 로직**:
    *   `can_entry = (Current Total Heat + New Unit Risk) <= Max Portfolio Heat`
    *   이 원칙에 따라, 포트폴리오 리스크가 가득 찬 경우 새로운 심볼에서 진입 시그널이 발생하더라도 진입을 차단합니다.
    *   이는 심볼 간 상관관계가 높을 때 전체 자산을 보호하는 'One Thing' 원칙에 충실한 리스크 관리 방식입니다.

---
**설계 원칙**: 가독성과 'One Thing' 원칙을 준수하기 위해 각 심볼의 상태는 엄격히 격리되며, 오직 `Total Heat`만이 포트폴리오 차원의 공유 지표로 활용됩니다.
