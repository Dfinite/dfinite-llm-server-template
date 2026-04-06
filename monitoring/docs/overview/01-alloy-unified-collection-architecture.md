# 1. 아키텍처: Grafana Alloy 통합 수집 (로그 → Loki, 메트릭 → Prometheus)

**Grafana Alloy** 한 에이전트에서 **로그·메트릭**을 수집하고, **로그는 Loki**, **메트릭은 Prometheus** 로 보내는 구조를 정리합니다.  
메트릭 파트는 [GPU-05 — Alloy 설정](../metrics/gpu/05-alloy-setup.md)·[GPU-06 — Alloy·dcgm-exporter 연동](../metrics/gpu/06-alloy-dcgm-exporter.md)·[GPU-07 — Prometheus 구축](../metrics/gpu/07-prometheus-setup.md)·[vLLM-01 — 메트릭 수집](../metrics/vllm/01-vllm-metrics-collection.md)에 나온 현재 파이프라인과 비교합니다.  
분산 트레이스·프로파일링은 [추후-02 — 프로파일링·트레이스](../future/02-future-profiling-and-distributed-tracing.md) 참고.

> 선행으로 현재 scrape 설정을 확인해 두면, "누가 exporter를 긁는가" 변화를 비교하기 쉽습니다.  
> [`prometheus/prometheus.yml`](../../prometheus/prometheus.yml), [`alloy/config.alloy`](../../alloy/config.alloy), [GPU-06](../metrics/gpu/06-alloy-dcgm-exporter.md), [vLLM-01](../metrics/vllm/01-vllm-metrics-collection.md) 참고.

---

## 목표

- [x] 현재 메트릭 경로(DCGM → dcgm-exporter → Alloy scrape → Prometheus 저장 → Grafana)를 **문서화된 기준선**으로 고정
- [x] Alloy 도입 시 **변경되는 프로세스**(수집 주체, Prometheus 역할)를 표로 정리
- [x] **중복 scrape·remote_write·리소스** 유의사항을 도입 전에 공유
- [x] GPU 스택(dcgm / dcgm-exporter)은 **노출 층으로 유지**함을 명시

---

## 1.1 현재 메트릭 파이프라인

저장소 기준 파일: [`docker-compose.yml`](../../docker-compose.yml), [`prometheus/prometheus.yml`](../../prometheus/prometheus.yml).

### 구성 요소와 역할

| 순서 | 구성 요소 | 역할 | 참고 문서 |
|------|-----------|------|-----------|
| ① | **dcgm** | GPU 노드에서 NVIDIA DCGM 엔진 | [GPU-03 — DCGM·dcgm-exporter 구축](../metrics/gpu/03-dcgm-and-dcgm-exporter-setup.md) |
| ② | **dcgm-exporter** | DCGM에 연결해 Prometheus 형식 메트릭을 HTTP 노출 (`:9400/metrics`) | [GPU-04 — dcgm-exporter 메트릭 노출](../metrics/gpu/04-dcgm-exporter-metrics-exposure.md) |
| ③ | **Alloy** | exporter·vLLM `/metrics` scrape, `remote_write` 로 Prometheus에 전달 | [GPU-05 — Alloy 설정](../metrics/gpu/05-alloy-setup.md), [GPU-06 — Alloy·dcgm-exporter 연동](../metrics/gpu/06-alloy-dcgm-exporter.md), [vLLM-01 — 메트릭 수집](../metrics/vllm/01-vllm-metrics-collection.md) |
| ④ | **Prometheus** | 시계열 저장·PromQL 조회 (remote_write 수신) | [GPU-07 — Prometheus 구축](../metrics/gpu/07-prometheus-setup.md) |
| ⑤ | **Grafana** | Prometheus·Loki 데이터소스, 메트릭·로그 대시보드 | [GPU-11 — Grafana Prometheus 데이터소스](../metrics/gpu/11-grafana-prometheus-datasource.md), [대시보드-01 — 통합 모니터링 대시보드](../dashboards/01-integrated-dashboard.md) |

### 데이터 흐름 (요약)

GPU·vLLM 메트릭은 exporter가 **노출**하고, **수집(scrape)** 은 Alloy가 담당합니다.

```
dcgm → dcgm-exporter(:9400/metrics) ──scrape──► Alloy(:12345) ──remote_write──► Prometheus(:9090) ──► Grafana(:3000)

vLLM 컨테이너(monitoring.scrape=true 레이블) ──Docker label discovery──► Alloy ──remote_write──► Prometheus ──► Grafana

컨테이너 로그 ──tail──► Alloy ──push──► Loki(:3100) ──► Grafana(:3000)
```

- **GPU**: [GPU-06 — Alloy·dcgm-exporter 연동](../metrics/gpu/06-alloy-dcgm-exporter.md) — Alloy 타깃 `dcgm-exporter:9400`.
- **vLLM**: [vLLM-01 — 메트릭 수집](../metrics/vllm/01-vllm-metrics-collection.md) — `manage_compose.py`가 생성한 컨테이너 레이블(`monitoring.scrape=true`)을 Alloy가 Docker 소켓으로 자동 감지. `job="vllm"` 공통, `service` 라벨로 인스턴스 구분. [개요-02 — 통합 구현](../overview/02-monitoring-integration-plan.md) 참고.

### Prometheus 역할 (현재)

현재 구성에서 Prometheus는 **remote_write 수신 + 로컬 TSDB 저장 + PromQL API** 를 수행합니다. scrape는 Alloy가 담당합니다.

---

## 1.2 아키텍처 비교: 이전 vs 현재

### 메트릭 파트 비교

| 항목 | 이전 (Prometheus 직접 scrape) | 현재 (Alloy 통합) |
|------|-------------------------------|-------------------|
| **누가 `/metrics`를 긁는가** | Prometheus `scrape_configs` | **Alloy** scrape |
| **dcgm / dcgm-exporter** | 변경 없음 — 노출 층 유지 | 동일 (스택 유지) |
| **vLLM 타깃** | `172.17.0.1:30071/30072` | Docker 레이블 기반 자동 발견 (`monitoring.scrape=true`) |
| **Prometheus scrape** | 활성 | **비활성·축소** — 이중 scrape 방지 |
| **Prometheus 역할** | scrape + 저장 + 쿼리 | **저장·쿼리** 중심 (remote_write 수신) |
| **로그 수집** | 미포함 | Alloy tail → Loki push |

### 메트릭 적재 방식

| 방법 | 메모 |
|------|------|
| **remote_write** | Prometheus `--web.enable-remote-write-receiver` 플래그 — 현재 [`docker-compose.yml`](../../docker-compose.yml)에 적용 완료 |
| **대안 TSDB** | Mimir, VictoriaMetrics 등 Prometheus 호환 백엔드 — 필요 시 별도 문서 분리 |

---

## 1.3 장단점

### 이점

| 이점 | 설명 |
|------|------|
| **에이전트 단일화** | 노드마다 Alloy 한 종류로 로그·메트릭 파이프라인 운영·업그레이드 |
| **역할 분리** | Exporter = 노출, Alloy = 수집·전달, TSDB = 저장·질의 |
| **Grafana 단일 UI** | 메트릭·로그 상관 ([대시보드-01 — 통합 모니터링 대시보드](../dashboards/01-integrated-dashboard.md)) |

### 주의점

| 주의 | 설명 |
|------|------|
| **중복 scrape** | Prometheus와 Alloy가 같은 `/metrics` 를 동시에 긁으면 부하·중복 시계열 → 한쪽만 scrape |
| **Alloy 리소스** | 로그·메트릭 한 프로세스 — CPU·메모리·네트워크 한도 모니터링 필요 ([추후-01 — 메모리 제한](../future/01-future-memory-limits.md)) |
| **설정 비대** | 파이프라인이 한 파일에 모이면 변경 영향 범위가 넓어질 수 있음 |
| **Prometheus 역할 변경** | 기본 GPU-07 구성과 달리 remote_write 수신·백엔드 설계 필요 |

### 이전 방식 (Prometheus 직접 scrape) 비교

| 장점 | 단점 |
|------|------|
| remote_write 설계 불필요, 설정 단순 | 로그 수집을 별도 에이전트(Promtail 등)로 두면 에이전트가 둘 이상 |

---

## 1.4 부하와 운영 복잡도

| 관점 | 정리 |
|------|------|
| **부하** | Alloy가 scrape + 로그 tail 동시 수행 시 한 프로세스에 부하 집중 — 로그 볼륨·scrape 대상 수·`scrape_interval` 기준으로 측정 |
| **운영** | 배포·버전은 통합이 단순한 경우가 많음. 장애 시 로그·메트릭 파이프라인 동시 영향 가능 |
| **실무 절충** | 통합으로 시작 → 부하 한계 시 로그만 분리 또는 리소스·노드 분리 검토 |

---

## 1.5 GPU 메트릭과의 관계

| 질문 | 정리 |
|------|------|
| **GPU 하드웨어 상태** | 트레이스로 대체 불필요 — DCGM·dcgm-exporter 메트릭 층 유지 ([추후-02 — 프로파일링·트레이스](../future/02-future-profiling-and-distributed-tracing.md)) |
| **목표 아키텍처에서의 변경** | DCGM → dcgm-exporter 는 유지, 수집 주체만 Prometheus → Alloy 로 이전 |

---

## 완료 조건

- [x] **중복 scrape 없음** — Alloy만 dcgm-exporter·vLLM 타깃 scrape (`prometheus/prometheus.yml` 은 self-scrape만)
- [x] **Loki** 데이터소스 프로비저닝 완료 (`grafana/provisioning/datasources/loki.yaml`, UID=`loki`)
- [x] **Grafana 알림 프로비저닝** 완료 (`grafana/provisioning/alerting/` — 로그·메트릭 규칙 5개)
- [x] 4개 대시보드 자동 로드 — GPU·vLLM·통합·로그 (`grafana/dashboards/`)
- [x] Alloy CPU·메모리 한도 — 현재 scrape 타깃 4개·소규모 로그 볼륨 수준에서는 한도 없이 운영 가능. 타깃·로그가 대폭 증가하면 [추후-01 — 메모리 제한](../future/01-future-memory-limits.md) 검토

---

## 메모 / 이슈

| 항목 | 내용 |
|------|------|
| **vLLM 타깃 IP** | `172.17.0.1:30071/30072` — Docker 기본 게이트웨이 IP. 환경(macOS, rootless Docker 등)에 따라 다를 수 있음. [vLLM-01 — 메트릭 수집](../metrics/vllm/01-vllm-metrics-collection.md) 참고. |
| **GPU 프로필** | dcgm / dcgm-exporter 는 `docker compose --profile gpu` 로 기동 ([GPU-03 — DCGM·dcgm-exporter 구축](../metrics/gpu/03-dcgm-and-dcgm-exporter-setup.md)). Alloy와 같은 호스트/네트워크에서 exporter URL 도달 가능해야 함. |
| **remote_write 수신** | Prometheus `--web.enable-remote-write-receiver` 플래그 — [`docker-compose.yml`](../../docker-compose.yml) 에 적용 완료. |

---

## 참고

| 문서 | 내용 |
|------|------|
| [logs-01 — Alloy 로그 수집](../logs/01-alloy-log-setup.md) | Alloy 로그 파이프라인 설정 |
| [logs-02 — Loki 구축](../logs/02-loki-setup.md) | Loki Docker·설정·확인 |
| [GPU-03 — DCGM·dcgm-exporter 구축](../metrics/gpu/03-dcgm-and-dcgm-exporter-setup.md) | DCGM·dcgm-exporter Compose |
| [GPU-04 — dcgm-exporter 메트릭 노출](../metrics/gpu/04-dcgm-exporter-metrics-exposure.md) | `/metrics` 노출 |
| [GPU-05 — Alloy 설정](../metrics/gpu/05-alloy-setup.md) | Alloy 메트릭 scrape·remote_write |
| [GPU-06 — Alloy·dcgm-exporter 연동](../metrics/gpu/06-alloy-dcgm-exporter.md) | Alloy dcgm-exporter 타깃 |
| [GPU-07 — Prometheus 구축](../metrics/gpu/07-prometheus-setup.md) | Prometheus 저장·조회 |
| [vLLM-01 — 메트릭 수집](../metrics/vllm/01-vllm-metrics-collection.md) | vLLM scrape job |
| [대시보드-01 — 통합 모니터링 대시보드](../dashboards/01-integrated-dashboard.md) | GPU + vLLM + 로그 패널 |
| [추후-01 — 메모리 제한](../future/01-future-memory-limits.md) | 컨테이너 메모리 제한 검토 |
| [추후-02 — 프로파일링·트레이스](../future/02-future-profiling-and-distributed-tracing.md) | 트레이스·프로파일 검토 |
