# 2. 로그 모니터링 대시보드

컨테이너 로그를 레벨별로 구분해서 확인합니다. ERROR·CRITICAL(알림 대상)과 WARNING(조회용)을 분리해 표시하고, 컨테이너별 발생률 추이를 시계열로 확인합니다.

> **알림 정책**: ERROR·CRITICAL만 알림 대상입니다. 자세한 기준은 [06 — 로그 레벨·알림 정책](../logs/06-log-levels-and-alerting.md)을 따릅니다.

---

## 목표

- [ ] 로그 대시보드가 Grafana에서 로드·표시됨
- [ ] ERROR·CRITICAL 스트림 패널이 정상 표시됨
- [ ] WARNING 이상 조회용 패널이 정상 표시됨
- [ ] 컨테이너별 발생률 timeseries 패널이 표시됨

---

## 대시보드 정보

| 항목 | 값 |
|------|-----|
| 대시보드 JSON | [`grafana/dashboards/log-overview.json`](../../grafana/dashboards/log-overview.json) |
| 대시보드 이름 | 로그 모니터링 |
| UID | `log-overview` |
| 빌드 스크립트 | [`scripts/build_grafana_log_dashboard.py`](../../scripts/build_grafana_log_dashboard.py) |
| 데이터 소스 | `Loki` |

Grafana UI: **Dashboards → 로그 모니터링** 선택.

---

## 대시보드 구성

### 요약 (상단)

| 패널 | LogQL | 설명 |
|------|-------|------|
| 전체 로그 발생률 | `sum(rate({job="docker"}[5m]))` | 전체 컨테이너 logs/s |
| ERROR·CRITICAL 발생률 | `sum(rate({job="docker"} \|~ "(?i)error\|critical" [5m]))` | 알림 대상 기준 발생률 |
| vLLM 로그 발생률 | `sum(rate({container_name=~"vllm.*"}[5m]))` | vLLM 인스턴스 logs/s |

### 로그 스트림

| 패널 | LogQL | 설명 |
|------|-------|------|
| ERROR·CRITICAL 로그 (알림 대상) | `{job="docker"} \|~ "(?i)error\|critical"` | 알림 정책 기준 스트림 |
| WARNING 이상 로그 (조회용) | `{job="docker"} \|~ "(?i)warning\|error\|critical"` | WARNING 포함 조회용 스트림 |
| vLLM 로그 스트림 | `{container_name=~"vllm.*"}` | vLLM 인스턴스 전체 로그 |

### 발생률 추이

| 패널 | LogQL | 설명 |
|------|-------|------|
| 컨테이너별 전체 발생률 | `rate({job="docker"}[5m])` — `{{container_name}}` 별 | 컨테이너별 logs/s 추이 |
| 컨테이너별 ERROR·CRITICAL 발생률 | `rate({job="docker"} \|~ "(?i)error\|critical" [5m])` — `{{container_name}}` 별 | 알림 임계값과 동일 쿼리 |

---

## JSON 수정 후 재생성

```bash
make grafana-log-dashboard
# 또는
python3 scripts/build_grafana_log_dashboard.py
```

변경 반영 시 `docker compose restart grafana`로 provisioning을 재로드합니다.

---

## 완료 조건

| 완료 조건 | 상태 |
|-----------|------|
| 로그 대시보드 표시 확인 | 검증 후 기입 |
| ERROR·CRITICAL 스트림 정상 표시 | 검증 후 기입 |
| 컨테이너별 발생률 패널 표시 | 검증 후 기입 |

---

## 기타 대시보드

| 대시보드 | 용도 |
|----------|------|
| [통합 모니터링](./01-integrated-dashboard.md) | GPU + vLLM + 로그 요약 |
| [GPU 모니터링](../metrics/gpu/12-gpu-grafana-dashboard.md) | GPU 메트릭 상세 |
| [vLLM 모니터링](../metrics/vllm/02-vllm-grafana-dashboard.md) | vLLM 메트릭 상세 |
| [로그 Explore (Loki)](../logs/05-grafana-loki-datasource.md) | 로그 직접 조회 |
