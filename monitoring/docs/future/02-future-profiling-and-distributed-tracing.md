# 1. 추후 고려: 프로파일링·벤더 도구 vs 분산 트레이스·스팬

`monitoring/` 스택은 **메트릭**(Prometheus, DCGM / dcgm-exporter, vLLM)과 **Grafana**를 중심으로 합니다. **프로파일링**과 **분산 트레이스·스팬**은 당장 도입하지 않고, 요구가 생길 때 검토할 **추후 고려사항**으로 정리합니다.

> 선행으로 GPU·vLLM 메트릭 파이프라인을 이해해 두면 본 문서의 역할 구분이 명확합니다. [GPU-05 (Alloy·메트릭)](../metrics/gpu/05-alloy-setup.md), [GPU-06 (Alloy — dcgm-exporter)](../metrics/gpu/06-alloy-dcgm-exporter.md), [GPU-07 (Prometheus)](../metrics/gpu/07-prometheus-setup.md), [vLLM-01 (메트릭 수집)](../metrics/vllm/01-vllm-metrics-collection.md) 참고.

---

## 목표

- [x] 프로파일링·벤더 도구와 메트릭·트레이스의 **역할 차이**를 팀 기준으로 정리해 둠
- [x] 분산 트레이스 도입 시점·조건을 **체크리스트**로 보관
- [x] GPU 하드웨어 관측은 **메트릭(DCGM)** 우선임을 문서에 명시

---

## 1.1 현재 스택과의 역할 구분

| 관측 수단 | 현재 스택에서의 위치 | 본 문서 범위 |
|-----------|----------------------|--------------|
| **메트릭** | Prometheus + Grafana, GPU·vLLM 패널 ([통합 대시보드](../dashboards/01-integrated-dashboard.md)) | 기본 스택 — 본 문서는 **추가 검토만** |
| **로그** | 도입됨 (Loki + Alloy, `docker-compose.yml`) | 본 문서 범위 외 — [문서 overview-01](../overview/01-alloy-unified-collection-architecture.md) 참고 |
| **프로파일링** | 미도입 | **추후 검토** |
| **분산 트레이스·스팬** | 미도입 | **추후 검토** |

---

## 1.2 프로파일링·벤더 도구

### 개념

- **CPU/메모리·호출 스택**에서 **어느 함수·커널이 시간을 쓰는지** 시간축으로 보는 관측입니다.
- **GPU**의 경우 NVIDIA **Nsight Systems / Nsight Compute**, **PyTorch Profiler**, **연속 프로파일링**(예: Grafana Pyroscope) 등이 해당합니다.

### 메트릭·트레이스와의 차이

| 구분 | 담당 예시 | 용도 |
|------|-----------|------|
| **메트릭** | `DCGM_FI_DEV_GPU_UTIL`, `DCGM_FI_DEV_GPU_TEMP` ([GPU-08 PromQL](../metrics/gpu/08-gpu-metrics-promql.md)) | 운영·용량·알람, **집계 시계열** |
| **프로파일링** | Nsight, PyTorch Profiler | **한 실행·짧은 구간**의 코드·커널 단위 병목 |

### 추후 검토 시점 (예시)

- 추론 지연이 메트릭만으로 원인 분석이 부족할 때 (커널 대기, 특정 연산 지배).
- 모델·배치 크기 튜닝 시 **GPU 커널·메모리 대역**을 확인해야 할 때.
- 팀에서 **연속 프로파일링**을 Grafana 생태계와 통합할지 결정할 때.

---

## 1.3 분산 트레이스·스팬

### 개념

- **하나의 요청**이 게이트웨이·추론 서버 등 **여러 구성 요소**를 지날 때 **스팬(Span)** 단위로 지연·순서를 기록합니다.
- 백엔드 예: **Grafana Tempo**, **Jaeger**. 수집은 **OpenTelemetry(OTel)** 와 함께 설계하는 경우가 많습니다.

### GPU 메트릭·프로파일링과의 관계

| 질문 | 정리 |
|------|------|
| GPU SM 점유·온도·VRAM | **메트릭**(dcgm-exporter) 층 ([GPU-04](../metrics/gpu/04-dcgm-exporter-metrics-exposure.md)) |
| 요청 한 건의 **서비스 경로·지연 분해** | 트레이스 층 (도입 시) |
| **커널·함수 단위** 미세 병목 | 프로파일링·벤더 도구 |

추론 서버가 HTTP 요청 단위로 큐·전처리·생성을 **스팬**으로 노출하면 **엔드투엔드 지연** 분석에 유리합니다. 이는 **GPU 전용**이라기보다 **서비스·API 관측**에 가깝습니다.

### 추후 검토 시점 (예시)

- 마이크로서비스·게이트웨이가 늘어 **요청 경로 추적**이 필요해질 때.
- vLLM 또는 상위 계층에서 **OTel 스팬**을 내보내는 구성을 검토할 때.
- Grafana에서 **메트릭·로그·트레이스 상관**(trace id)을 쓰고 싶을 때.

---

## 1.4 의사결정 체크리스트

검토를 시작할 때 아래를 질문해 볼 수 있습니다.

| # | 질문 | 방향 |
|---|------|------|
| 1 | 문제가 **장비·용량·과열**인가, **요청 한 건의 경로·지연**인가? | 전자 → 메트릭(및 필요 시 로그). 후자 → 트레이스 검토. |
| 2 | 병목이 **어느 함수·커널**까지 필요한가? | 필요하면 프로파일링·벤더 도구 검토. |
| 3 | 에이전트·백엔드(**Alloy**, Tempo, Pyroscope 등)를 **한 번에** 도입할지 **단계적으로** 할지? | 운영 범위·리스크에 따라 결정. |

---

## 완료 조건

본 문서는 **설계 메모**이므로 구축 완료가 아닌 **문서 작성 완료**를 기준으로 합니다.

- [x] 프로파일링·트레이스·메트릭의 역할 차이 정리
- [x] 각 기술의 추후 검토 시점 기술
- [x] 의사결정 체크리스트 작성
- [x] 현재 스택(메트릭·로그) 위치 명시

프로파일링·트레이스 중 하나를 **실제로 도입**하면 해당 항목별로 별도 문서 또는 절을 추가하는 것을 권장합니다.

---

## 메모 / 이슈

| 항목 | 내용 |
|------|------|
| GPU 인프라 | 트레이스로 GPU 하드웨어 상태를 **대체**할 필요는 없음 — DCGM·dcgm-exporter 메트릭이 해당 층에 적합 ([GPU-02](../metrics/gpu/02-gpu-metrics-sources.md)). |
| 로그·통합 수집 | 로그·Alloy 목표 아키텍처는 [문서 overview-01](../overview/01-alloy-unified-collection-architecture.md) 참고. |

---

## 참고

| 문서 | 내용 |
|------|------|
| [GPU-02 — GPU 메트릭 소스](../metrics/gpu/02-gpu-metrics-sources.md) | GPU 메트릭 소스 조사, dcgm-exporter 채택 |
| [GPU-05 — Alloy 설정](../metrics/gpu/05-alloy-setup.md) | Alloy 메트릭 scrape·remote_write |
| [GPU-06 — Alloy·dcgm-exporter 연동](../metrics/gpu/06-alloy-dcgm-exporter.md) | Alloy dcgm-exporter scrape 연동 |
| [GPU-07 — Prometheus 구축](../metrics/gpu/07-prometheus-setup.md) | Prometheus Docker 구축 |
| [vLLM-01 — 메트릭 수집](../metrics/vllm/01-vllm-metrics-collection.md) | vLLM `/metrics`, Alloy `vllm` 타깃 |
| [대시보드-01 — 통합 모니터링 대시보드](../dashboards/01-integrated-dashboard.md) | GPU + vLLM 패널 |
| [개요-01 — Alloy 통합 수집](../overview/01-alloy-unified-collection-architecture.md) | 로그·메트릭 에이전트 통합 시 메트릭 파이프라인 변화 |
| [logs-01 — Alloy 로그 수집](../logs/01-alloy-log-setup.md) | Alloy 로그 파이프라인 설정 |
| [logs-02 — Loki 구축](../logs/02-loki-setup.md) | Loki Docker·설정 |
