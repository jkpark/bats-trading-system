# Backtest Report Specification

BATS 시스템의 백테스트 리포트는 아키텍처 가독성과 데이터 분석의 용이성을 위해 다음 형식을 엄격히 준수해야 합니다.

## 1. 리포트 구조

### [CONFIGURATION] (테스트 설정값)
- **Symbol**: 거래 종목
- **Interval**: 타임프레임 (예: 4h, 1d)
- **Period**: 백테스트 수행 기간 (시작일 ~ 종료일)
- **Strategy**: 적용된 전략 클래스명
- **Strategy Params**: 전략에 적용된 세부 파라미터 요약 (예: S1/S2/S3 활성화 여부, 필터 임계값)

### [SUMMARY] (수익성 및 통계)
- **Initial Balance**: 시작 자산
- **Final Equity**: 최종 자산
- **Total Return**: 수익률 (%)
- **Max Drawdown**: 최대 낙폭 (%)
- **Win Rate**: 승률 (수익 거래 수 / 전체 종료 거래 수)
- **Total Trades**: 종료된 총 거래 횟수

### [TRADE DETAILS] (매매일지)
- **Timestamp**: 매매 발생 시각 (YYYY-MM-DD HH:mm)
- **Type**: BUY, PYRAMID, EXIT
- **Price**: 체결 가격
- **Units**: 현재 보유 유닛 수
- **Result**: EXIT 시 발생한 손익 (USDT)

## 2. 가독성 원칙
- 모든 리포트는 터미널 가독성을 위해 고정폭(Monospace) 테이블 형식을 권장합니다.
- 결과 파일은 JSON으로 별도 저장되어 사후 분석이 가능해야 합니다.
