# 1. 목표 아키텍처: Grafana Alloy 통합 수집 (로그 → Loki, 메트릭 → Prometheus)

**Grafana Alloy** 한 에이전트에서 **로그·메트릭**을 수집하고, **로그는 Loki**, **메트릭은 Prometheus(호환 TSDB)** 로 보내는 방안을 정리합니다.  
**메트릭 파트**는 [GPU-05 (Alloy)](../metrics/gpu/05-alloy-setup.md)·[GPU-06 (Alloy — dcgm-exporter)](../metrics/gpu/06-alloy-dcgm-exporter.md)·[GPU-07 (Prometheus)](../metrics/gpu/07-prometheus-setup.md)·[vLLM-01](../metrics/vllm/01-vllm-metrics-collection.md)에 나온 **현재 파이프라인**과 비교합니다. 분산 트레이스·프로파일링은 [문서 01](../future/01-future-profiling-and-distributed-tracing.md) 참고.

> 선행으로 **현재** scrape 설정을 확인해 두면, “누가 exporter를 긁는가” 변화를 비교하기 쉽습니다. [`prometheus/prometheus.yml`](../../prometheus/prometheus.yml), [`alloy/config.alloy`](../../alloy/config.alloy), [GPU-06](../metrics/gpu/06-alloy-dcgm-exporter.md), [vLLM-01 §1.2](../metrics/vllm/01-vllm-metrics-collection.md) 참고.

## 목표

- [x] 현재 메트릭 경로(DCGM → dcgm-exporter → Alloy scrape → Prometheus 저장 → Grafana)를 **문서화된 기준선**으로 고정
- [x] Alloy 도입 시 **변경되는 프로세스**(수집 주체, Prometheus 역할)를 표로 정리
- [x] **중복 scrape·remote_write·리소스** 유의사항을 도입 전에 공유
- [x] GPU 스택(dcgm / dcgm-exporter)은 **노출 층으로 유지**함을 명시

---

## 2.1 현재 메트릭 파이프라인 (기준선)

저장소 기준 파일: [`docker-compose.yml`](../../docker-compose.yml), [`prometheus/prometheus.yml`](../../prometheus/prometheus.yml).

### 구성 요소와 역할

| 순서 | 구성 요소 | 역할 | 참고 문서 |
|------|-----------|------|-----------|
| ① | **dcgm** | GPU 노드에서 NVIDIA DCGM 엔진 | [GPU-03](../metrics/gpu/03-dcgm-and-dcgm-exporter-setup.md) |
| ② | **dcgm-exporter** | DCGM에 연결해 Prometheus 형식 메트릭을 **HTTP 노출** (`:9400/metrics`) | [GPU-04](../metrics/gpu/04-dcgm-exporter-metrics-exposure.md) |
| ③ | **Alloy** | exporter·vLLM `/metrics` **scrape**, `remote_write` 로 Prometheus에 전달 | [GPU-05](../metrics/gpu/05-alloy-setup.md), [GPU-06](../metrics/gpu/06-alloy-dcgm-exporter.md), [vLLM-01](../metrics/vllm/01-vllm-metrics-collection.md) |
| ④ | **Prometheus** | 시계열 **저장**·PromQL 조회 (remote_write 수신) | [GPU-07](../metrics/gpu/07-prometheus-setup.md) |
| ⑤ | **Grafana** | Prometheus 데이터 소스·메트릭 대시보드·Explore | [GPU-11](../metrics/gpu/11-grafana-prometheus-datasource.md), [GPU-12](../metrics/gpu/12-gpu-grafana-dashboard.md), [통합 대시보드](../dashboards/01-integrated-dashboard.md) · 로그(Loki)는 [logs/01](../logs/01-loki-setup.md) |

### 데이터 흐름 (요약)

GPU·vLLM 메트릭은 exporter가 **노출**하고, **수집(scrape)** 은 Alloy가 담당합니다.

```
dcgm → dcgm-exporter(:9400 /metrics) ──scrape──► Alloy(:12345) ──remote_write──► Prometheus(:9090) ──► Grafana(:3000)

호스트 vLLM(:30071, service=qwen-demo) ──scrape──► Alloy ──remote_write──► Prometheus ──► Grafana
호스트 vLLM(:30072, service=embedding-women) ──scrape──► Alloy ──remote_write──► Prometheus ──► Grafana
```

- **GPU**: [GPU-06](../metrics/gpu/06-alloy-dcgm-exporter.md) — Alloy 타깃 `dcgm-exporter:9400`.
- **vLLM**: [vLLM-01](../metrics/vllm/01-vllm-metrics-collection.md) — Alloy 타깃 `172.17.0.1:30071` (`service=qwen-demo`), `172.17.0.1:30072` (`service=embedding-women`). `job="vllm"` 공통, `service` 라벨로 인스턴스 구분.

### Prometheus 프로세스 역할 (현재)

현재 구성에서 Prometheus는 **remote_write 수신 + 로컬 TSDB 저장 + PromQL API**를 수행합니다. scrape는 Alloy가 담당합니다 ([GPU-05](../metrics/gpu/05-alloy-setup.md), [GPU-07](../metrics/gpu/07-prometheus-setup.md), [vLLM-01](../metrics/vllm/01-vllm-metrics-collection.md)).

---

## 2.2 적용 아키텍처 (Alloy 통합)

### 개념

| 구성 요소 | 역할 |
|-----------|------|
| **Grafana Alloy** | 로그 tail 등 → **Loki**; exporter·vLLM **HTTP scrape** → 메트릭 백엔드로 전달 |
| **Loki** | 로그 저장·LogQL |
| **Prometheus(또는 PromQL 호환 TSDB)** | 메트릭 시계열 **저장·PromQL** — Grafana 메트릭 데이터 소스 |
| **Grafana** | 메트릭(Prometheus)·로그(Loki) 데이터 소스, [통합 대시보드](../dashboards/01-integrated-dashboard.md) (GPU 메트릭 문서는 [GPU-11](../metrics/gpu/11-grafana-prometheus-datasource.md)만 해당) |

### 데이터 흐름 (목표)

```
dcgm → dcgm-exporter(:9400) ──scrape──► Alloy ──remote_write 등──► Prometheus(계열) ──► Grafana

vLLM(:30071, service=qwen-demo) ──scrape──► Alloy ────────────────► (동일)
vLLM(:30072, service=embedding-women) ──scrape──► Alloy ──────────► (동일)

앱/컨테이너 로그 ──tail──► Alloy ──push──► Loki ──► Grafana
```

### 메트릭 파트만: 현재 vs 목표

| 항목 | 현재 ([prometheus.yml](../../prometheus/prometheus.yml)) | 목표 (Alloy 도입 후, 메트릭) |
|------|---------------------------|------------------------------|
| **누가 `/metrics`를 긁는가** | Prometheus `scrape_configs` | **Alloy**가 동일 엔드포인트 scrape |
| **dcgm / dcgm-exporter** | 변경 없음 — **노출** | 동일 ([GPU-03](../metrics/gpu/03-dcgm-and-dcgm-exporter-setup.md) 스택 유지) |
| **vLLM 타깃** | `172.17.0.1:30071` (`service=qwen-demo`), `172.17.0.1:30072` (`service=embedding-women`) | `job="vllm"` 공통, `service` 라벨로 인스턴스 구분 |
| **Prometheus의 scrape** | 활성 | **비활성·축소** — Alloy와 **동일 타깃 이중 scrape 방지** |
| **Prometheus의 역할** | scrape + 저장 + 쿼리 | **저장·쿼리** 중심으로 두려면 Alloy 수집분 **수신 경로(remote_write 등)** 필요 |

### 구현 시 맞출 것 (메트릭 적재)

Alloy가 scrape한 시계열을 TSDB에 넣는 방식은 배포·버전에 따라 다릅니다.

| 방법 | 메모 |
|------|------|
| **remote_write** | Prometheus 호환 백엔드(Mimir, VictoriaMetrics 등) 또는 **수신 기능이 있는** Prometheus 구성 |
| **단일 Prometheus만 유지** | remote write **수신** 지원 여부·플래그를 버전별로 확인 |

본 저장소는 현재 아래 경로로 구현합니다.

- Alloy 설정: [`alloy/config.alloy`](../../alloy/config.alloy)
- Loki 설정: [`loki/config.yml`](../../loki/config.yml)
- Prometheus remote_write 수신 플래그: [`docker-compose.yml`](../../docker-compose.yml)
- Grafana Loki 데이터 소스: [`grafana/provisioning/datasources/loki.yaml`](../../grafana/provisioning/datasources/loki.yaml)

---

## 2.3 장단점

### 목표 아키텍처의 이점

| 이점 | 설명 |
|------|------|
| 에이전트 단일화 | 노드마다 **Alloy 한 종류**로 로그·메트릭 파이프라인 운영·업그레이드 |
| 역할 분리 | **Exporter** = 노출, **Alloy** = 수집·전달, **TSDB** = 저장·질의 |
| Grafana 단일 UI | 메트릭·로그 상관 ([통합 대시보드](../dashboards/01-integrated-dashboard.md)와 동일 UI) |

### 주의점·단점

| 주의 | 설명 |
|------|------|
| **중복 scrape** | Prometheus와 Alloy가 **같은 `/metrics`** 를 동시에 긁으면 부하·중복 시계열 → **한쪽만** scrape |
| **Alloy 리소스** | 로그·메트릭 **한 프로세스** — CPU·메모리·네트워크 한도 모니터링 |
| **설정 비대** | 파이프라인이 한 파일에 모이면 변경 영향 범위가 넓어질 수 있음 |
| **Prometheus 역할 변경** | 기본 [GPU-07](../metrics/gpu/07-prometheus-setup.md) 구성과 달리 **remote_write 수신·백엔드** 설계 필요할 수 있음 |

### 대안: Prometheus 직접 scrape 유지

| 장점 | 단점 |
|------|------|
| [GPU-06](../metrics/gpu/06-alloy-dcgm-exporter.md)·[vLLM-01](../metrics/vllm/01-vllm-metrics-collection.md)과 동일 패턴, remote_write 설계 불필요 | 로그 수집을 **Promtail/Alloy** 로만 두면 **에이전트가 둘 이상**일 수 있음 |

---

## 2.4 부하와 운영 복잡도

| 관점 | 정리 |
|------|------|
| **부하** | Alloy가 scrape + 로그 tail 동시 수행 시 **한 프로세스**에 부하 집중 — 로그 볼륨·scrape 대상 수·`scrape_interval` 기준으로 측정 |
| **운영** | 배포·버전은 **통합이 단순**한 경우가 많음. 장애 시 **로그·메트릭 파이프라인 동시 영향** 가능 |
| **실무 절충** | 통합으로 시작 → 부하 한계 시 로그만 분리 또는 리소스·노드 분리 검토 |

---

## 2.5 GPU 메트릭과의 관계

| 질문 | 정리 |
|------|------|
| GPU 하드웨어 상태 | **트레이스로 대체 불필요** — DCGM·dcgm-exporter **메트릭** ([문서 01](../future/01-future-profiling-and-distributed-tracing.md)) |
| 목표 아키텍처에서의 변경 | **DCGM → dcgm-exporter** 는 유지, **수집 주체**만 Prometheus → Alloy 로 이전하는 것이 자연스러움 |

---

## 완료 조건

- [x] **중복 scrape 없음** — Alloy만 dcgm-exporter·vLLM 타깃 scrape (`prometheus/prometheus.yml` 은 self-scrape만)
- [x] **Loki** 데이터 소스 프로비저닝 완료 (`grafana/provisioning/datasources/loki.yaml`, UID=`loki`)
- [x] **Grafana 알림 프로비저닝** 완료 (`grafana/provisioning/alerting/` — 로그·메트릭 규칙 5개)
- [x] 4개 대시보드 자동 로드 — GPU·vLLM·통합·로그 (`grafana/dashboards/`)
- [x] Alloy CPU·메모리 한도 — 현재 scrape 타깃 4개·소규모 로그 볼륨 수준에서는 한도 없이 운영 가능. 타깃·로그가 대폭 증가하면 `deploy.resources.limits` 검토

---

## 메모 / 이슈

| 항목 | 내용 |
|------|------|
| vLLM 타깃 | [vLLM-01](../metrics/vllm/01-vllm-metrics-collection.md) — `172.17.0.1:30071` (`service=qwen-demo`), `172.17.0.1:30072` (`service=embedding-women`). `job="vllm"` 공통, `service` 라벨로 인스턴스 구분. |
| GPU 프로필 | `dcgm` / `dcgm-exporter` 는 `docker compose --profile gpu` ([GPU-03](../metrics/gpu/03-dcgm-and-dcgm-exporter-setup.md)). Alloy 추가 시 **같은 호스트/네트워크**에서 exporter URL에 도달 가능해야 함. |
| remote_write | 단일 Prometheus만 쓸 경우 **수신 방식**을 반드시 확인. 필요 시 Mimir 등 별도 문서로 분리 검토. |

---

## 참고

| 문서 | 내용 |
|------|------|
| [01 — Alloy 로그 수집 기능 활성화](../logs/01-alloy-log-setup.md) | Alloy 로그 파이프라인 설정 |
| [02 — Loki 구축](../logs/02-loki-setup.md) | Loki Docker·설정·확인 |
| [GPU-03](../metrics/gpu/03-dcgm-and-dcgm-exporter-setup.md) | DCGM·dcgm-exporter Compose |
| [GPU-04](../metrics/gpu/04-dcgm-exporter-metrics-exposure.md) | `/metrics` 노출 |
| [GPU-05](../metrics/gpu/05-alloy-setup.md) | Alloy — 메트릭 scrape·remote_write |
| [GPU-06](../metrics/gpu/06-alloy-dcgm-exporter.md) | Alloy — dcgm-exporter 타깃 |
| [GPU-07](../metrics/gpu/07-prometheus-setup.md) | Prometheus — 저장·PromQL |
| [vLLM-01](../metrics/vllm/01-vllm-metrics-collection.md) | vLLM scrape job |
| [통합 대시보드](../dashboards/01-integrated-dashboard.md) | GPU + vLLM 패널 |
| [01 — 프로파일링·트레이스 (추후)](../future/01-future-profiling-and-distributed-tracing.md) | 트레이스·프로파일 검토 |
