# Feature Requirement: Notification Manager

| 항목 | 내용 |
|------|------|
| **문서 버전** | v1.0 |
| **작성일** | 2026-02-27 |
| **작성자** | Auto-generated |
| **상태** | Draft |
| **우선순위** | High |

---

## 1. 개요 (Overview)

### 1.1 목적 (Purpose)

BATS Trading System의 운영 상태와 매매 활동을 실시간으로 운영자에게 전달하기 위한 **SNS 기반 알림 시스템**을 제공한다. 자동화된 트레이딩 시스템의 특성상, 운영자가 시스템을 상시 모니터링할 수 없으므로 주요 이벤트(매매 체결, 에러 발생, 시스템 상태 변경)를 Notification Channel을 통해 즉시 통보한다.

### 1.2 범위 (Scope)

**포함:**
- Notification Channel을 통한 알림 전송
- 매매 체결 알림 (BUY / SELL / EXIT)
- 시스템 에러 알림
- 일반 상태 알림
- Embed 형식의 시각적 메시지 포맷팅

**미포함 (Out of Scope):**
- 알림 수신/읽음 확인
- 알림 이력 저장 및 조회
- 사용자별 알림 설정 커스터마이징

### 1.3 용어 정의 (Glossary)

| 용어 | 정의 |
|------|------|
| **Notification Channel** | 외부 서비스에 HTTP POST 요청으로 메시지를 전송하는 방식 |
| **Embed** | 메시지에서 제목, 색상, 필드 등 구조화된 형식으로 표시되는 Rich 메시지 |
| **DI (Dependency Injection)** | 객체가 의존하는 컴포넌트를 외부에서 주입받는 설계 패턴 |
| **Side** | 매매 방향 (BUY / SELL / EXIT) |
| **Symbol** | 거래 대상 종목 코드 (e.g., BTCUSDT) |

---

## 2. 기능 요구사항 (Functional Requirements)

### FR-001: Notification Channel 설정
| 항목 | 내용 |
|------|------|
| **ID** | FR-001 |
| **우선순위** | Must |
| **설명** | 시스템 초기화 시 Notification Channel을 설정한다. 생성자 파라미터로 직접 전달하거나, `config.yaml`의 `notification.channel`에서 자동으로 로드한다. |
| **입력** | `channel` (NotificationChannel) — 직접 전달 시 사용 |
| **출력** | `NotificationManager` 인스턴스 (channel 속성 설정됨) |
| **선행 조건** | 없음 |
| **후행 조건** | channel이 설정되지 않은 경우 경고 로그 출력 및 모든 알림 전송이 비활성화됨 |

### FR-002: 매매 체결 알림
| 항목 | 내용 |
|------|------|
| **ID** | FR-002 |
| **우선순위** | Must |
| **설명** | 매매가 체결되었을 때 알림을 전송한다. 매매 방향에 따라 색상을 구분한다. |
| **입력** | `side` (str), `symbol` (str), `price` (float), `quantity` (float), `status` (str, 기본값: "SUCCESS") |
| **출력** | `bool` — 전송 성공 여부 |
| **선행 조건** | Notification Channel이 유효하게 설정되어 있어야 함 |
| **후행 조건** | Notification Channel에 메세지 전송 성공됨 |

**색상 규칙:**
| 조건 | 색상 | HEX 코드 |
|------|------|----------|
| `side == "BUY"` | 🟢 녹색 (Green) | `0x00ff00` |
| `side != "BUY"` (SELL/EXIT 등) | 🔴 적색 (Red) | `0xff0000` |
| `status != "SUCCESS"` | ⚫ 회색 (Gray) | `0x808080` |

**Embed 필드 구성:**
| 필드 | 값 | Inline |
|------|------|--------|
| Title | `Trade Notification: {status}` | - |
| Symbol | `` `{symbol}` `` | ✅ |
| Side | `**{side.upper()}**` | ✅ |
| Price | `{price}` | ✅ |
| Quantity | `{quantity}` | ✅ |
| Footer | `BATS Trading System \| Notification Manager` | - |

### FR-003: 시스템 에러 알림
| 항목 | 내용 |
|------|------|
| **ID** | FR-003 |
| **우선순위** | Must |
| **설명** | 시스템 에러 발생 시 긴급 알림을 Notification Channel로 전송한다. 에러 메시지는 코드 블록 형식으로 표시된다. |
| **입력** | `error_msg` (str) |
| **출력** | `bool` — 전송 성공 여부 |
| **선행 조건** | Notification Channel이 유효하게 설정되어 있어야 함 |
| **후행 조건** | Notification Channel에 에러 메세지 전송 성공됨 |

**Embed 구성:**
| 필드 | 값 |
|------|------|
| Title | `🚨 System Error Alert` |
| Description | ` ```{error_msg}``` ` (코드 블록) |
| Color | `0xff0000` (Red) |
| Footer | `BATS Trading System \| Notification Manager` |

### FR-004: 일반 상태 알림
| 항목 | 내용 |
|------|------|
| **ID** | FR-004 |
| **우선순위** | Must |
| **설명** | 시스템 시작, 종료 등 일반적인 상태 변경을 Notification Channel로 전송한다. |
| **입력** | `title` (str), `message` (str) |
| **출력** | `bool` — 전송 성공 여부 |
| **선행 조건** | Notification Channel이 유효하게 설정되어 있어야 함 |
| **후행 조건** | Notification Channel에 상태 메시지 전송 성공됨 |

**Embed 구성:**
| 필드 | 값 |
|------|------|
| Title | `{title}` (사용자 정의) |
| Description | `{message}` (사용자 정의) |
| Color | `0x3498db` (Blue) |
| Footer | `BATS Trading System \| Notification Manager` |

### FR-005: Graceful Degradation (알림 비활성화)
| 항목 | 내용 |
|------|------|
| **ID** | FR-005 |
| **우선순위** | Must |
| **설명** | Notification Channel이 설정되지 않은 경우, 모든 알림 전송 메서드는 에러 없이 `False`를 반환하며 시스템 운영에 영향을 주지 않는다. |
| **입력** | 모든 알림 메서드 호출 |
| **출력** | `False` |
| **선행 조건** | `channel`이 `None` |
| **후행 조건** | 시스템은 정상적으로 계속 동작함 |

### FR-006: NotificationChannel 인터페이스
| 항목 | 내용 |
|------|------|
| **ID** | FR-006 |
| **우선순위** | Must |
| **설명** | 다양한 알림 채널(Discord, Slack, Telegram 등)을 지원하기 위한 추상 인터페이스를 정의한다. DI 패턴을 통해 `NotificationManager`에 주입한다. |
| **입력** | `payload` (dict) — 전송할 메시지 페이로드 |
| **출력** | `bool` — 전송 성공 여부 |
| **선행 조건** | 없음 |
| **후행 조건** | 구현체가 채널별 전송 로직을 수행함 |

**인터페이스 정의:**
```python
from abc import ABC, abstractmethod

class NotificationChannel(ABC):
    @abstractmethod
    def send(self, payload: dict) -> bool:
        """메시지 페이로드를 전송한다."""
        pass
```

### FR-007: DiscordNotificationChannel 구현
| 항목 | 내용 |
|------|------|
| **ID** | FR-007 |
| **우선순위** | Must |
| **설명** | `NotificationChannel` 인터페이스를 상속하여 Discord Webhook 기반 알림 전송을 구현한다. |
| **입력** | `webhook_url` (str) — `config.yaml`의 `notification.channel.webhook_url`에서 로드 |
| **출력** | `bool` — Discord API 응답 코드 `204` 시 `True` |
| **선행 조건** | 유효한 Discord Webhook URL이 설정되어야 함 |
| **후행 조건** | Discord 채널에 메시지가 전송됨 |

---

## 3. 비기능 요구사항 (Non-Functional Requirements)

### 3.1 성능 (Performance)
- 알림 전송은 HTTP 요청 기반이므로, 메인 트레이딩 루프의 성능에 최소한의 영향을 주어야 한다.
- Notification Channel의 응답 시간에 의존하며, 타임아웃은 Python 기본 `urllib` 설정을 따른다.

### 3.2 보안 (Security)
- Notification Channel은 `config.yaml`의 `notification.channel`에 설정된 값을 통해 관리하며, 소스 코드에 하드코딩하지 않는다.
- HTTP 요청 시 `User-Agent` 헤더를 `BATS-Notifier/1.0`으로 설정하여 요청 출처를 식별한다.

### 3.3 안정성 (Reliability)
- 알림 전송 실패 시 예외를 상위로 전파하지 않고 내부적으로 처리한다 (`try-except`).
- `HTTPError`와 일반 `Exception`을 별도로 처리하여 상세한 에러 로그를 남긴다.
- 알림 실패가 트레이딩 시스템의 핵심 기능(매매 체결, 상태 관리)에 영향을 주지 않는다.

### 3.4 확장성 (Scalability)
- SNS Channel은 사용자의 선택에 따라 다양한 채널로 변경할 수 있도록 인터페이스 추상화하고 확장 가능하도록 설계한다.

---

## 4. 인터페이스 요구사항 (Interface Requirements)

### 4.1 외부 인터페이스 (External Interfaces)

외부 인터페이스는 `NotificationChannel` 구현체에 의해 결정된다. 아래는 `DiscordNotificationChannel`의 예시이다.

| 항목 | 내용 |
|------|------|
| **대상** | Discord Webhook API |
| **프로토콜** | HTTPS POST |
| **Content-Type** | `application/json` |
| **User-Agent** | `BATS-Notifier/1.0` |
| **성공 응답 코드** | `204 No Content` |
| **페이로드 형식** | Discord Embed Object (`{"embeds": [...]}`) |

> [!NOTE]
> 향후 새로운 채널 구현체(e.g., `SlackNotificationChannel`)에서는 해당 채널의 API 명세를 따른다.

### 4.2 내부 인터페이스 (Internal Interfaces)

| 호출자 | 메서드 | 호출 시점 |
|--------|--------|-----------|
| any | `send_trade()` | BUY/PYRAMID 매매 체결 시 |
| any | `send_trade()` | EXIT 시 (status에 결과 포함) |
| any | `send_error()` | 메인 루프 예외 발생 시 |
| any | `send_status()` | 시스템 안전 종료 시 |

---

## 5. 설정 (Configuration)

| 설정 항목 | 설명 | 기본값 | 필수 여부 |
|-----------|------|--------|----------|
| `notification.channel.type` | 사용할 Notification Channel 타입 | `discord` | Yes |
| `notification.channel.webhook_url` | Webhook 엔드포인트 URL | 없음 | Channel이 `discord`인 경우 Yes |

**설정 방법:**
1. `config.yaml`의 `notification.channel` 섹션에 채널 타입 및 접속 정보를 설정
2. 소스 코드에 하드코딩 금지

---

## 6. 에러 처리 (Error Handling)

| 에러 상황 | 처리 방식 | 사용자 영향 |
|-----------|-----------|-------------|
| Channel 미설정 (`None`) | 초기화 시 경고 로그 출력, 모든 `send_*` 메서드는 `False` 반환 | 알림을 받지 못하지만 시스템은 정상 운영 |
| Channel 전송 실패 (HTTP 에러) | Channel 구현체 내부에서 에러 로그 기록 후 `False` 반환 | 해당 알림만 전송 실패, 시스템 계속 동작 |
| 네트워크 오류 등 기타 예외 | Channel 구현체 내부에서 에러 로그 기록 후 `False` 반환 | 해당 알림만 전송 실패, 시스템 계속 동작 |

---

## 7. 제약 사항 및 의존성 (Constraints & Dependencies)

### 7.1 제약 사항 (Constraints)
- Python 표준 라이브러리(`urllib`, `json`, `os`, `logging`)만 사용하여 외부 의존성 없이 동작한다.
- 알림 전송은 비동기식(asynchronous)으로 처리되므로, 네트워크 지연 시에도 호출자의 실행이 블로킹되지 않는다.

### 7.2 의존성 (Dependencies)

| 의존성 | 유형 | 설명 |
|--------|------|------|
| Python `urllib.request` | 표준 라이브러리 | HTTP 요청 전송 |
| Python `json` | 표준 라이브러리 | JSON 페이로드 직렬화 |
| Python `logging` | 표준 라이브러리 | 에러 및 경고 로그 |

---

## 8. 검증 기준 (Acceptance Criteria)

- [ ] `NotificationChannel` 인터페이스가 ABC로 정의되어 `send(payload)` 메서드를 강제한다.
- [ ] `DiscordNotificationChannel`이 `NotificationChannel`을 상속하고 Discord Webhook으로 메시지를 전송한다.
- [ ] `NotificationManager`가 DI 패턴으로 `NotificationChannel`을 주입받아 동작한다.
- [ ] Channel 미설정 시 모든 전송 메서드가 `False`를 반환하고 예외를 발생시키지 않는다.
- [ ] `send_trade()`가 매매 방향에 따른 색상 규칙을 적용하여 알림을 전송한다.
- [ ] `send_error()`가 에러 메시지를 코드 블록 형식으로 전송한다.
- [ ] `send_status()`가 사용자 지정 제목/메시지로 상태 알림을 전송한다.
- [ ] 알림 전송 실패가 트레이딩 시스템의 핵심 동작을 중단시키지 않는다.
- [ ] 기존 테스트가 새로운 DI 구조에서 통과한다.

---

## 변경 이력 (Change Log)

| 버전 | 날짜 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| v1.0 | 2026-02-27 | 초기 작성 — 현재 구현 기준 | Auto-generated |
| v1.1 | 2026-02-27 | DI 패턴 적용, NotificationChannel 인터페이스 및 DiscordNotificationChannel 추가 | Auto-generated |
