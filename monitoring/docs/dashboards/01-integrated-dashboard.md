# 1. 통합 모니터링 대시보드

GPU 인프라 메트릭, vLLM 서비스 메트릭, 컨테이너 로그를 하나의 대시보드에서 확인합니다. GPU(인프라 관점)·vLLM(서비스 관점)·로그(운영 관점)를 동시에 보면서 문제 원인을 파악할 수 있습니다.

---

## 목표

대시보드 JSON·패널 정의는 레포에 포함되어 있습니다. **실제 Grafana에서 표시·값을 확인한 뒤** 체크합니다.

- [ ] 통합 대시보드가 Grafana에서 로드·표시됨
- [ ] 요약 패널(gauge / stat)이 기대대로 동작함
- [ ] GPU·vLLM 메트릭 패널이 동시에 표시됨
- [ ] API 환산 비용 패널(선택) 표시 확인
- [ ] 로그 패널에서 컨테이너 로그 조회 확인 (Loki 연동 전제)

---

## 대시보드 정보

| 항목 | 값 |
|------|-----|
| 대시보드 JSON | [`grafana/dashboards/integrated-overview.json`](../../grafana/dashboards/integrated-overview.json) |
| 대시보드 이름 | 통합 모니터링 |
| UID | `integrated-overview` |
| 빌드 스크립트 | [`scripts/build_grafana_integrated_dashboard.py`](../../scripts/build_grafana_integrated_dashboard.py) |
| 데이터 소스 | `Prometheus` (메트릭), `Loki` (로그) |

Grafana UI: **Dashboards → 통합 모니터링** 선택.

---

## 대시보드 구성

### 요약 (상단)

한눈에 현황을 파악할 수 있는 gauge / stat 패널 6개입니다. vLLM 패널은 인스턴스(`service` 라벨)별로 구분됩니다.

| 패널 | 타입 | 쿼리 | 임계값 |
|------|------|------|--------|
| GPU 평균 사용률 | gauge | `avg(DCGM_FI_DEV_GPU_UTIL)` | 🟢 ~70% 🟡 ~90% 🔴 |
| GPU 최고 온도 | gauge | `max(DCGM_FI_DEV_GPU_TEMP)` | 🟢 ~70°C 🟡 ~80°C 🔴 |
| 입력 토큰 (누적) | stat | `vllm:prompt_tokens_total` — `{{service}}` 별 | — |
| 생성 토큰 (누적) | stat | `vllm:generation_tokens_total` — `{{service}}` 별 | — |
| 완료 요청 수 | stat | `vllm:request_success_total` — `{{service}}` 별 | — |
| KV 캐시 사용률 | gauge | `vllm:gpu_cache_usage_perc` — `{{service}}` 별 | 🟢 ~70% 🟡 ~90% 🔴 |

### GPU 메트릭 (dcgm-exporter)

| 패널 | PromQL | 단위 |
|------|--------|------|
| GPU 사용률 | `DCGM_FI_DEV_GPU_UTIL` | % |
| GPU 온도 | `DCGM_FI_DEV_GPU_TEMP` | °C |
| GPU 메모리 사용량 | `DCGM_FI_DEV_FB_USED` | MiB |
| GPU 전력 | `DCGM_FI_DEV_POWER_USAGE` | W |

### vLLM 메트릭 (보조 지표)

`{{service}}` 라벨로 `qwen-demo` / `embedding-women` 인스턴스를 구분합니다.

| 패널 | PromQL | 단위 |
|------|--------|------|
| 토큰 사용량 (누적) | `vllm:prompt_tokens_total`, `vllm:generation_tokens_total` | — |
| 토큰 처리 속도 | `rate(vllm:prompt_tokens_total[5m])`, `rate(vllm:generation_tokens_total[5m])` | tok/s |
| 요청 수 | `vllm:request_success_total` (stop / length / abort) | — |
| 평균 응답 시간 | `rate(vllm:e2e_request_latency_seconds_sum[5m]) / rate(...count[5m])` | s |

### API 환산 비용 (참고)

| 패널 | 시리즈 | PromQL |
|------|--------|--------|
| 플래그십 | GPT-4o | `(prompt * 2.5 / 1e6) + (generation * 10 / 1e6)` |
| | Gemini 2.5 Pro | `(prompt * 1.25 / 1e6) + (generation * 10 / 1e6)` |
| 경량 | GPT-4o-mini | `(prompt * 0.15 / 1e6) + (generation * 0.6 / 1e6)` |
| | Gemini 2.5 Flash | `(prompt * 0.3 / 1e6) + (generation * 2.5 / 1e6)` |

> 2026-03-25 기준 단가. 토크나이저 차이 등으로 실제 API 비용과 차이가 있을 수 있습니다.

### 로그 (Loki)

컨테이너 로그를 메트릭과 같은 화면에서 확인합니다. **Loki가 기동 중이어야** 표시됩니다.

| 패널 | 타입 | LogQL | 설명 |
|------|------|-------|------|
| ERROR·CRITICAL 로그 (알림 대상) | logs | `{job="docker"} \|~ "(?i)error\|critical"` | 알림 정책 기준 스트림 ([06번](../logs/06-log-levels-and-alerting.md)) |
| vLLM 로그 | logs | `{container_name=~"vllm.*"}` | vLLM 인스턴스 로그 스트림 |
| 컨테이너별 ERROR·CRITICAL 발생률 | timeseries | `rate({job="docker"} \|~ "(?i)error\|critical" [5m])` — `{{container_name}}` 별 | 알림 임계값과 동일 쿼리 — 발생률 > 0 이면 알림 발화 |

---

## JSON 수정 후 재생성

```bash
make grafana-integrated-dashboard
# 또는
python3 scripts/build_grafana_integrated_dashboard.py
```

변경 반영 시 `docker compose restart grafana`로 provisioning을 재로드합니다.

---

## 완료 조건

| 완료 조건 | 작성할 내용 | 상태 |
|-----------|-------------|------|
| 통합 대시보드 표시 확인 | Grafana 대시보드 캡처 | 검증 후 기입 |
| 요약 gauge/stat 정상 표시 | 임계값 색상 동작 확인 | 검증 후 기입 |
| GPU·vLLM 패널 동시 표시 | 시간 동기화 확인 | 검증 후 기입 |
| 로그 패널 Loki 연동 확인 | 에러·경고·vLLM 로그 표시 확인 | 검증 후 기입 |

![통합 대시보드 — GPU 메트릭](../../src/integrated-dashboard-gpu.png)

![통합 대시보드 — vLLM 메트릭](../../src/integrated-dashboard-vllm.png)

---

## 기타 대시보드

| 대시보드 | 용도 |
|----------|------|
| [GPU 모니터링](../metrics/gpu/12-gpu-grafana-dashboard.md) | GPU 메트릭 상세 |
| [vLLM 모니터링](../metrics/vllm/02-vllm-grafana-dashboard.md) | vLLM 메트릭 상세 |
| [로그 (Loki Explore)](../logs/05-grafana-loki-datasource.md) | 로그 상세 조회 |
| [로그 레벨·알림 정책](../logs/06-log-levels-and-alerting.md) | ERROR 이상 알림·Python `logging` 기준 |
