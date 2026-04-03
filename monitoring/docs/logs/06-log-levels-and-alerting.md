# 6. 로그 레벨·알림 정책 (Python `logging` 기준)

애플리케이션(vLLM 등)이 출력하는 로그는 **레벨**에 따라 심각도가 구분됩니다. Loki·Grafana로 수집·조회할 때도 동일한 기준을 맞추면, **어떤 줄을 알림으로 올릴지** 일관되게 정할 수 있습니다.

> **알림 정책**: 로그 메시지 중 **ERROR 이상**(ERROR, CRITICAL)에 대해서만 알림을 전달합니다. DEBUG·INFO·WARNING은 알림 대상이 아닙니다. (운영 정책에 따라 WARNING 포함 여부는 조정 가능합니다.)

| LEVEL | Value | 알림 |
|-------|-------|------|
| DEBUG | 10 | — |
| INFO | 20 | — |
| WARNING | 30 | — |
| ERROR | 40 | O |
| CRITICAL | 50 | O |

Python 표준 [`logging`](https://docs.python.org/3/library/logging.html) 모듈의 숫자 값과 동일합니다.

---

## 목표

- [ ] 레벨별 의미와 `logger.*` 호출을 맞춰 사용한다
- [x] ERROR·CRITICAL만 알림으로 보내는 정책을 팀·Grafana 규칙과 일치시킨다
- [x] Grafana 알림 규칙을 프로비저닝 파일로 사전 설정한다 (`grafana/provisioning/alerting/`)
- [x] Loki·LogQL로 해당 레벨만 필터링하는 방법은 [4번](./04-logql-queries.md)과 연계한다

---

## 6.1 Grafana 알림 프로비저닝

알림 규칙과 수신처는 **파일 기반 프로비저닝**으로 미리 설정해 둡니다. Grafana 기동 시 자동 적용됩니다.

| 파일 | 역할 |
|------|------|
| [`grafana/provisioning/alerting/log-error-rules.yaml`](../../../grafana/provisioning/alerting/log-error-rules.yaml) | 로그 알림 규칙 — Loki 기반 |
| [`grafana/provisioning/alerting/metric-alert-rules.yaml`](../../../grafana/provisioning/alerting/metric-alert-rules.yaml) | 메트릭 알림 규칙 — Prometheus 기반 |
| [`grafana/provisioning/alerting/contact-points.yaml`](../../../grafana/provisioning/alerting/contact-points.yaml) | 수신처 예시 (전체 주석 — 사용 채널 주석 해제) |

### 로그 알림 규칙 (Loki)

| 규칙 | LogQL | 조건 | 대기 |
|------|-------|------|------|
| 컨테이너 ERROR·CRITICAL 감지 | `sum(rate({job="docker"} \|~ "(?i)error\|critical" [5m]))` | `> 0` | 2분 |
| vLLM ERROR·CRITICAL 감지 | `sum(rate({container_name=~"vllm.*"} \|~ "(?i)error\|critical" [5m]))` | `> 0` | 2분 |

로그 알림은 **"이미 에러가 났다"** 는 사후 감지입니다.

### 메트릭 알림 규칙 (Prometheus)

| 규칙 | PromQL | 조건 | 대기 |
|------|--------|------|------|
| GPU 온도 임계 초과 | `max(DCGM_FI_DEV_GPU_TEMP)` | `> 80°C` | 5분 |
| vLLM KV 캐시 포화 | `max(vllm:gpu_cache_usage_perc{model_name=~".+"})` | `> 0.9` | 2분 |
| vLLM 요청 abort 발생 | `sum(rate(vllm:request_success_total{finished_reason="abort",...}[5m]))` | `> 0` | 1분 |

메트릭 알림은 **"문제가 생기기 전"** 선제 감지입니다. GPU 사용률은 추론 중 높은 게 정상이므로 알림 대상이 아닙니다.

수신처를 설정하려면 `contact-points.yaml`에서 원하는 채널(Slack·이메일·Webhook)의 주석을 해제하고 값을 입력한 뒤:

```bash
docker compose restart grafana
```

로그 쿼리 상세: [4 — LogQL](./04-logql-queries.md).

---

## 6.2 레벨별 로그 출력 방법 (Python)

### DEBUG

오류 수정 중 디버깅용으로 활용합니다.

```python
logger.debug("...")
```

### INFO

일반적인 상황에서 가장 많이 쓰는 레벨입니다. 서비스 구동 시 확인이 필요한 정보, 사용량 등 누적·관측용 데이터에 적합합니다.

```python
logger.info("...")
```

### WARNING

서비스 동작을 멈추지는 않지만, 코드·설정·자원 측면에서 주의가 필요할 때 사용합니다.

```python
logger.warning("...")
```

### ERROR

서비스 동작에 실제 문제가 생긴 오류입니다.

```python
logger.error("...")
```

### CRITICAL

개별 서비스를 넘어 연관 시스템·기능까지 영향을 줄 수 있는 치명적 오류입니다.

```python
logger.critical("...")
```

---

## 참고

- Python logging HOWTO: [Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- 문서 [4 (LogQL)](./04-logql-queries.md), [5 (Grafana Loki 데이터소스)](./05-grafana-loki-datasource.md)

