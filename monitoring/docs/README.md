# Monitoring 문서 구성

`monitoring/` 스택을 **관측 신호·목적**별로 나눈 문서입니다.  
아래 순서는 “무엇이 무엇인지”가 드러나도록 한 **권장 읽기 순서**입니다.

---

## 스택 구성 요소 (한눈에)

| 구분 | 구성 요소 | 역할 |
|------|-----------|------|
| **GPU** | `dcgm`, `dcgm-exporter` | GPU 상태 → HTTP `/metrics` 노출 |
| **서비스** | vLLM (호스트에서 포트 노출) | 추론 메트릭 `/metrics` |
| **수집** | Alloy | 메트릭 scrape, Docker 로그 수집 |
| **메트릭 저장** | Prometheus | TSDB, PromQL, `remote_write` 수신 |
| **로그 저장** | Loki | 로그 저장·LogQL |
| **시각화** | Grafana | Prometheus + Loki 데이터 소스, 대시보드 |

데이터 흐름 요약:

```
dcgm → dcgm-exporter(:9400) ──────────────────────────────┐
vLLM(:30071, service=qwen-demo) ──────────────────────────┼─ scrape → Alloy ─ remote_write → Prometheus(:9090) ─┐
vLLM(:30072, service=embedding-women) ────────────────────┘              └─ push ──→ Loki(:3100) ───────────────┼→ Grafana(:3000)
Docker 로그 ──────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 문서 디렉터리 (신호·목적별)

| 경로 | 설명 |
|------|------|
| [`overview/`](overview/) | 전체 아키텍처(Alloy 통합 수집 등) |
| [`metrics/gpu/`](metrics/gpu/) | GPU 인프라 메트릭 — 환경·DCGM·Alloy·Prometheus·Grafana·PromQL·GPU 대시보드 (01–12) |
| [`metrics/vllm/`](metrics/vllm/) | vLLM 서비스 메트릭 — 수집·대시보드·PromQL (01–03) |
| [`logs/`](logs/) | Loki·Alloy 구축, LogQL, 로그 레벨·알림 정책 |
| [`dashboards/`](dashboards/) | 통합 Grafana 대시보드 (GPU + vLLM) |
| [`future/`](future/) | 추후 검토 — 프로파일링·분산 트레이스 등 |

---

## 권장 읽기 순서

### 1) 개요·로그 파이프라인

1. [overview/01 — Alloy 통합 수집 아키텍처](overview/01-alloy-unified-collection-architecture.md)
2. [logs/01 — Alloy 로그 수집 기능 활성화](logs/01-alloy-log-setup.md)
3. [logs/02 — Loki 구축](logs/02-loki-setup.md)
4. [logs/03 — Alloy·Loki 연동 확인](logs/03-alloy-loki-integration.md)
5. [logs/04 — LogQL 쿼리 레퍼런스](logs/04-logql-queries.md)
6. [logs/05 — Grafana Loki 데이터소스](logs/05-grafana-loki-datasource.md)
7. [logs/06 — 로그 레벨·알림 정책](logs/06-log-levels-and-alerting.md) (애플리케이션 로깅 기준·ERROR 이상 알림)

### 2) GPU 메트릭 (인프라) — **5 Alloy → 6 Alloy·dcgm-exporter 연동 → 7 Prometheus(저장)**

1. [metrics/gpu/01 — 서버 환경](metrics/gpu/01-gpu-server-environment.md)
2. [metrics/gpu/02 — 수집 소스 조사](metrics/gpu/02-gpu-metrics-sources.md)
3. [metrics/gpu/03 — dcgm-exporter 구축](metrics/gpu/03-dcgm-and-dcgm-exporter-setup.md)
4. [metrics/gpu/04 — 메트릭 노출 확인](metrics/gpu/04-dcgm-exporter-metrics-exposure.md)
5. [metrics/gpu/05 — Alloy (메트릭: scrape·remote_write)](metrics/gpu/05-alloy-setup.md)
6. [metrics/gpu/06 — Alloy — dcgm-exporter 연동](metrics/gpu/06-alloy-dcgm-exporter.md)
7. [metrics/gpu/07 — Prometheus (저장·PromQL)](metrics/gpu/07-prometheus-setup.md)
8. [metrics/gpu/08 — PromQL](metrics/gpu/08-gpu-metrics-promql.md) → [metrics/gpu/09 — 검증](metrics/gpu/09-promql-query-verification.md)
9. [metrics/gpu/10 — Grafana 구축](metrics/gpu/10-grafana-setup.md)
10. [metrics/gpu/11 — Grafana — Prometheus 데이터 소스](metrics/gpu/11-grafana-prometheus-datasource.md)
11. [metrics/gpu/12 — GPU 대시보드](metrics/gpu/12-gpu-grafana-dashboard.md)

### 3) vLLM 메트릭 (서비스)

1. [metrics/vllm/01 — 메트릭 수집](metrics/vllm/01-vllm-metrics-collection.md)
2. [metrics/vllm/02 — 대시보드](metrics/vllm/02-vllm-grafana-dashboard.md)
3. [metrics/vllm/03 — PromQL 레퍼런스](metrics/vllm/03-vllm-metrics-promql.md)

### 4) 통합 화면·추후 검토

- [dashboards/01 — 통합 대시보드](dashboards/01-integrated-dashboard.md)
- [dashboards/02 — 로그 모니터링 대시보드](dashboards/02-log-dashboard.md)
- [future/01 — 프로파일링·분산 트레이스](future/01-future-profiling-and-distributed-tracing.md)

---

## 파일별 빠른 목차

### 개요 (`overview/`)

| # | 문서 |
|---|------|
| 01 | [Alloy 통합 수집 아키텍처](overview/01-alloy-unified-collection-architecture.md) |

### 메트릭 — GPU (`metrics/gpu/`)

| # | 문서 |
|---|------|
| 01 | [GPU 서버 환경 확인](metrics/gpu/01-gpu-server-environment.md) |
| 02 | [GPU 메트릭 수집 소스 조사](metrics/gpu/02-gpu-metrics-sources.md) |
| 03 | [dcgm-exporter 구축](metrics/gpu/03-dcgm-and-dcgm-exporter-setup.md) |
| 04 | [메트릭 노출 확인](metrics/gpu/04-dcgm-exporter-metrics-exposure.md) |
| 05 | [Alloy 구축 (메트릭 파트)](metrics/gpu/05-alloy-setup.md) |
| 06 | [Alloy — dcgm-exporter 연동](metrics/gpu/06-alloy-dcgm-exporter.md) |
| 07 | [Prometheus 구축](metrics/gpu/07-prometheus-setup.md) |
| 08 | [PromQL 작성](metrics/gpu/08-gpu-metrics-promql.md) |
| 09 | [PromQL 조회 검증](metrics/gpu/09-promql-query-verification.md) |
| 10 | [Grafana 구축](metrics/gpu/10-grafana-setup.md) |
| 11 | [Grafana — Prometheus 데이터 소스](metrics/gpu/11-grafana-prometheus-datasource.md) |
| 12 | [GPU 대시보드 패널 구성](metrics/gpu/12-gpu-grafana-dashboard.md) |

### 메트릭 — vLLM (`metrics/vllm/`)

| # | 문서 |
|---|------|
| 01 | [vLLM 메트릭 수집 환경 확인](metrics/vllm/01-vllm-metrics-collection.md) |
| 02 | [vLLM 대시보드 패널 구성](metrics/vllm/02-vllm-grafana-dashboard.md) |
| 03 | [vLLM PromQL 레퍼런스](metrics/vllm/03-vllm-metrics-promql.md) |

### 로그 (`logs/`)

| # | 문서 |
|---|------|
| 01 | [Alloy 로그 수집 기능 활성화](logs/01-alloy-log-setup.md) |
| 02 | [Loki 구축](logs/02-loki-setup.md) |
| 03 | [Alloy·Loki 연동 확인](logs/03-alloy-loki-integration.md) |
| 04 | [LogQL 쿼리 레퍼런스](logs/04-logql-queries.md) |
| 05 | [Grafana Loki 데이터소스](logs/05-grafana-loki-datasource.md) |
| 06 | [로그 레벨·알림 정책](logs/06-log-levels-and-alerting.md) |

### 대시보드 (`dashboards/`)

| # | 문서 |
|---|------|
| 01 | [통합 모니터링 대시보드](dashboards/01-integrated-dashboard.md) |
| 02 | [로그 모니터링 대시보드](dashboards/02-log-dashboard.md) |

### 추후 (`future/`)

| # | 문서 |
|---|------|
| 01 | [추후 고려: 프로파일링·트레이스](future/01-future-profiling-and-distributed-tracing.md) |
