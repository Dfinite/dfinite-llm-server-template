# 4. LogQL 쿼리 레퍼런스

Loki에 적재된 컨테이너 로그를 대상으로, Prometheus UI·Grafana Explore에서 사용할 **LogQL** 예시를 정리합니다.

**LogQL**은 로그 스트림을 수집·저장하지 않고, Loki에 이미 들어온 데이터를 **질의**할 때 쓰는 언어입니다 (수집·저장은 02·03번).

| 구분 | 담당 |
|------|------|
| **수집** | Alloy — [02](./02-alloy-log-setup.md) |
| **저장·조회** | Loki — push 수신 후 LogQL로 조회 ([03](./03-alloy-loki-integration.md)) |

> **알림 정책**: ERROR·CRITICAL 레벨만 알림 대상입니다. WARNING은 조회·모니터링 용도로는 포함하되, 알림은 보내지 않습니다. 레벨 기준은 [6번](./06-log-levels-and-alerting.md)을 따릅니다.

---

## 목표

- [x] 주요 라벨 필터링 방법 정리
- [x] 서비스별 로그 조회 쿼리 작성
- [x] 로그 내용 기반 필터링 방법 정리
- [x] 집계 쿼리 (rate, count) 작성
- [x] 알림 정책(ERROR·CRITICAL)에 따른 알림 전용 쿼리 작성

---

## 4.1 라벨

Alloy `discovery.docker`·`loki.process`가 부여하는 라벨입니다.

| 라벨 | 의미 | 예시 |
|------|------|------|
| `job` | 로그 수집 출처 | `docker` |
| `container_name` | 컨테이너 이름 | `prometheus`, `grafana`, `loki` |
| `compose_service` | Compose 서비스명 | `prometheus`, `alloy` |
| `compose_project` | Compose 프로젝트명 | `monitoring` |

**전체 컨테이너 로그**

```logql
{job="docker"}
```

**특정 컨테이너만**

```logql
{container_name="prometheus"}
```

**Compose 서비스명으로**

```logql
{compose_service="grafana"}
```

---

## 4.2 로그 스트림 필터

### 내용 포함 필터 (`|=`)

```logql
{job="docker"} |= "error"
```

### 내용 제외 필터 (`!=`)

```logql
{container_name="alloy"} != "debug"
```

### 정규식 필터 (`|~`)

```logql
{job="docker"} |~ "WARN|ERROR"
```

### 로그 레벨 기반 필터

> 레벨 문자열이 로그 라인에 그대로 출력된다고 가정합니다 (vLLM 등 Python `logging` 기본 포맷).

**조회용 — WARNING 이상 (모니터링·대시보드 패널)**

```logql
{job="docker"} |~ "(?i)warning|error|critical"
```

**알림 대상 — ERROR·CRITICAL만 ([06번 정책](./06-log-levels-and-alerting.md))**

```logql
{job="docker"} |~ "(?i)error|critical"
```

**특정 컨테이너 ERROR·CRITICAL**

```logql
{container_name=~"vllm.*"} |~ "(?i)error|critical"
```

---

## 4.3 서비스별 조회 예시

### Prometheus 로그

```logql
{container_name="prometheus"}
```

### Grafana 로그

```logql
{container_name="grafana"}
```

### Loki 로그

```logql
{container_name="loki"}
```

### Alloy 로그

```logql
{container_name="alloy"}
```

### 에러·경고 로그 전체 (조회용, 모든 컨테이너)

WARNING 이상을 한 화면에서 확인할 때 사용합니다. **알림 대상은 ERROR·CRITICAL만**입니다 ([06번 정책](./06-log-levels-and-alerting.md)).

```logql
{job="docker"} |~ "(?i)warning|error|critical"
```

---

## 4.4 집계 쿼리

### 컨테이너별 로그 발생률 (logs/s)

```logql
rate({job="docker"}[5m])
```

### 특정 서비스 에러 발생률

```logql
rate({container_name="prometheus"} |= "error" [5m])
```

### 최근 1시간 컨테이너별 로그 수

```logql
sum by (container_name) (count_over_time({job="docker"}[1h]))
```

---

## 4.5 알림 전용 쿼리 (ERROR·CRITICAL)

Grafana Alerting 규칙 구성 시 사용합니다. WARNING은 알림 대상이 아닙니다.

**전체 컨테이너 ERROR·CRITICAL 발생률**

```logql
rate({job="docker"} |~ "(?i)error|critical" [5m])
```

**vLLM ERROR·CRITICAL 발생률**

```logql
rate({container_name=~"vllm.*"} |~ "(?i)error|critical" [5m])
```

**컨테이너별 ERROR·CRITICAL 누적 수 (최근 1시간)**

```logql
sum by (container_name) (
  count_over_time({job="docker"} |~ "(?i)error|critical" [1h])
)
```

---

## 4.6 패널별 확정 쿼리

| 패널 | 용도 | LogQL |
|------|------|-------|
| 전체 컨테이너 로그 스트림 | 조회 | `{job="docker"}` |
| 에러·경고 필터 스트림 | 조회 (WARNING 이상) | `{job="docker"} \|~ "(?i)warning\|error\|critical"` |
| 컨테이너별 로그 발생률 | 조회·집계 | `rate({job="docker"}[5m])` |
| 알림 — ERROR·CRITICAL 발생률 | 알림 | `rate({job="docker"} \|~ "(?i)error\|critical" [5m])` |

---

## 참고

| 문서 | 내용 |
|------|------|
| [01 — Alloy 로그 수집](./01-alloy-log-setup.md) | Alloy 로그 파이프라인 설정 |
| [03 — Alloy·Loki 연동](./03-alloy-loki-integration.md) | 연동 확인 |
| [05 — Grafana Loki 데이터소스](./05-grafana-loki-datasource.md) | Loki 데이터소스 설정 |
| [06 — 로그 레벨·알림 정책](./06-log-levels-and-alerting.md) | ERROR 이상 알림 정책 |

- [LogQL 공식 문서](https://grafana.com/docs/loki/latest/query/)
- [LogQL 로그 쿼리](https://grafana.com/docs/loki/latest/query/log_queries/)
- [LogQL 메트릭 쿼리](https://grafana.com/docs/loki/latest/query/metric_queries/)
