# 2. GPU 메트릭 수집 소스 조사 및 채택

GPU 메트릭 수집 방식 후보를 비교하고, 조사 결과를 바탕으로 Prometheus·Grafana에 쓸 **GPU exporter**를 결정합니다.

## 목표

- [x] nvidia-smi / NVML / DCGM 개념·활용 정리
- [x] 방식별 차이·장단점 정리
- [x] Prometheus 연동 방식 및 적합성 검토
- [x] 필요 GPU 메트릭 제공 여부·목록표 정리
- [x] dcgm-exporter 역할 및 **채택 사유** 문서화

---

## 2.1 nvidia-smi 기반 수집

### 개념

- NVIDIA 드라이버와 함께 제공되는 CLI.
- GPU 이름, 이용률, 메모리, 온도, 전력, 프로세스 등을 한 화면(또는 쿼리 가능한 출력)으로 확인.

### 활용 방식

- 주기적으로 `nvidia-smi` 실행 후 **표준 출력 파싱**, 또는  
  `nvidia-smi --query-gpu=... --format=csv,noheader` 등으로 **기계 읽기 쉬운 출력** 후 수집.

### Prometheus 연동

- 기본적으로 **Prometheus 텍스트 포맷(`/metrics`)을 제공하지 않음**.  
  별도 **exporter·스크립트**가 파싱 후 HTTP로 노출해야 scrape 가능.

### 장단점

| 장점 | 단점 |
|------|------|
| 서버에 보통 이미 있어 추가 설치가 적음 | 파싱·라벨·메트릭 이름을 팀이 유지보수해야 함 |
| 수동 점검·간단 스크립트에 적합 | DCGM 계열 대비 “표준 메트릭명·대시보드” 재사용이 약함 |

---

## 2.2 NVML (NVIDIA Management Library)

### 개념

- GPU 이용률, 메모리, 온도, 전력 등을 **프로그램에서 조회**하기 위한 API (C).  
- Python 등에서는 `nvidia-ml-py` 등으로 동일 계열 정보에 접근.

### 활용 방식

- 자체 애플리케이션 또는 **경량 exporter**가 NVML로 값을 읽어 **Prometheus exposition 형식**으로 HTTP 서빙.

### Prometheus 연동

- NVML이 Prometheus에 **직접** 붙는 구조는 아님.  
  **NVML → (직접/선택한 exporter) → Prometheus scrape** 흐름.

### 장단점

| 장점 | 단점 |
|------|------|
| 커스텀 라벨·로직·샘플링 주기 제어에 유리 | exporter 선택·개발·운영 부담 |
| 비교적 가벼운 수집 경로 | 메트릭 명명·문서화를 팀 규약으로 맞춰야 함 |

---

## 2.3 DCGM (Data Center GPU Manager) 및 dcgm-exporter

### DCGM 개념

- 데이터센터·다중 GPU 환경에서 GPU **상태·성능·진단** 정보를 다루기 위한 NVIDIA 측 스택.  
- NVML과 겹치는 계측이 많고, 환경·버전에 따라 제공 필드·프로파일이 달라질 수 있음.

### dcgm-exporter 역할

- DCGM(및 하위 NVML 계층)에서 읽은 값을 **Prometheus exposition 형식의 HTTP `/metrics`** 로 노출하는 **전용 exporter**(Alloy 등 Prometheus 호환 scraper가 동일 엔드포인트를 수집).  
- 본 프로젝트 플로우에서 **“GPU 실시간 상태 → Export(Prometheus 형식)”** 에 해당하는 구성 요소.

### 수집기·Prometheus·Grafana 연계

- **Alloy**(또는 동일하게 HTTP `/metrics`를 scrape하는 수집기): `dcgm-exporter`를 scrape 대상으로 둔 뒤 **Prometheus**에 적재(예: `remote_write`).  
- **Prometheus**: 시계열 저장·PromQL API.  
- **Grafana**: Prometheus를 data source로 두고 PromQL로 패널 구성.  
- 공식·커뮤니티 대시보드가 DCGM 메트릭명에 맞춰 있는 경우가 많음.

### 장단점

| 장점 | 단점 |
|------|------|
| Prometheus 연동에 **적합하다** | GPU 노드에 DCGM/exporter 실행·이미지·권한 정리 필요 |
| 메트릭 이름·라벨이 비교적 **표준화**되어 있음 | 버전에 따라 메트릭명 확인(`/metrics`) 필요 |

---

## 2.4 방식 비교 (차이점 요약)

| 구분 | nvidia-smi | NVML | DCGM + dcgm-exporter |
|------|------------|------|----------------------|
| 성격 | CLI 출력 | 프로그래밍 API | DCGM + Prometheus용 exporter |
| 정보 접근 | 명령 실행·파싱 | 라이브러리 호출 | DCGM/NVML 계층을 exporter가 수집 |
| Prometheus에 바로 적합 | △ (래핑 필요) | △ (exporter 필요) | ○ (HTTP `/metrics`) |
| 운영·대시보드 재사용 | 커스텀 의존 | 커스텀 의존 | 문서·예시 풍부 |

**요약**: **nvidia-smi**는 사람·스크립트 친화, **NVML**은 프로그램·커스텀 exporter 친화, **DCGM + dcgm-exporter**는 **Prometheus 스택과의 직결**에 가장 가깝다.

---

## 2.5 Prometheus 연동 시 적합한 방식

| 목표 | 권장 |
|------|------|
| 수집기(Alloy 등) scrape → Prometheus 적재 → Grafana 시각화·알림 | **dcgm-exporter** |
| 빠른 수동 검증·숫자 비교 | `nvidia-smi` |
| 매우 특수한 라벨·비즈니스 로직만 필요 | NVML 기반 **자체 exporter** 검토 |

### 시각화 도구: Superset vs Grafana (+ Prometheus)

- **Apache Superset**은 주로 **SQL**로 연결된 소스(데이터베이스·웨어하우스 등)에서 질의한 **결과셋**을 차트·대시보드로 보여주는 **BI** 도구에 가깝다.
- **GPU 메트릭**처럼 **짧은 주기로 수집·누적되는 시계열**은 **Prometheus**에 두고 **PromQL**로 조회한 뒤 **Grafana**로 시각화하는 편이 일반적으로 유리하다. (동일 지표를 ETL·적재하여 Superset으로 보는 구성도 가능하나, 스택과 지연이 늘어난다.)
- 정리하면, **시계열 기반 인프라 모니터링**에서는 **Prometheus + Grafana** 조합이, **SQL 기반 탐색·리포트**에서는 **Superset** 쪽이 더 자연스러운 경우가 많다.

**Prometheus + Grafana**(시계열 메트릭 모니터링·PromQL; SQL 기반 BI인 **Apache Superset** 단독보다 exporter → scrape → 대시보드 흐름에 적합)를 전제로 하므로, GPU 노드에서는 **dcgm-exporter**를 채택하는 것이 적합하다.

---

## 2.6 필요 GPU 메트릭 제공 여부 (목록표)

실제 **메트릭 이름**은 dcgm-exporter·DCGM 프로파일·버전에 따라 달라질 수 있어, 구축 후 `GET /metrics`로 확정하는 것을 권장한다.

| 목적 | 필요한 정보 | 비고 |
|------|-------------|------|
| 사용률 | GPU 연산 이용률(%) | 대시보드 핵심 |
| 메모리 | 사용량·총량 또는 사용률 | OOM·용량 계획 |
| 온도 | GPU 온도(°C) | 쿨링·스로틀 |
| 전력 | 소비 전력(W) 등 | 전력 예산 |
| 식별 | GPU 인덱스, UUID, 모델 | **라벨**로 시계열 구분 |
| (선택) 에러·헬스 | XID 등 | 환경·버전 의존 |

### 구축 후 메모 (메트릭명 확정용)

[4번](./04-dcgm-exporter-metrics-exposure.md) 절차 후 아래처럼 맞추면 된다 (본 레포 기본값).

| 용도 | 확정 메트릭명 (구축 후 기입) |
|------|------------------------------|
| Utilization | `DCGM_FI_DEV_GPU_UTIL` |
| Memory used | `DCGM_FI_DEV_FB_USED` |
| Temperature | `DCGM_FI_DEV_GPU_TEMP` |
| Power | `DCGM_FI_DEV_POWER_USAGE` |
| GPU 구분 라벨 | `gpu`, `UUID`, `device` 등 (상세는 [4번](./04-dcgm-exporter-metrics-exposure.md)) |

---

## 2.7 채택 결정

### 채택: **dcgm-exporter**

| 사유 | 설명 |
|------|------|
| Alloy·Prometheus 파이프라인 | exporter가 **HTTP `/metrics`(Prometheus 텍스트)** 를 노출하므로 **Alloy**(`prometheus.scrape` 등)로 긁은 뒤 **Prometheus**에 적재·**PromQL** 조회하는 구성과 맞다. |
| 목표 메트릭 | 이용률·메모리·온도·전력 등을 **한 경로(dcgm-exporter)** 에서 다루기 쉽다. |
| Grafana | 위 시계열을 **Prometheus 데이터 소스**로 두면 PromQL·공개 대시보드 예시와 **호환**하기 쉽다. |
| 역할 분리 | `nvidia-smi`는 **검증·대조**용으로 병행 가능. |

### 유보

- **nvidia-smi만**으로 운영 메트릭을 만들 경우 파싱·유지보수 비용이 커진다.  
- **NVML 직접**은 커스텀 요구가 없는 한 본 시나리오에서는 우선순위를 낮출 수 있다.

---

## 완료 조건

- [x] nvidia-smi, NVML, DCGM **차이** 및 각 방식 **장단점** 기술  
- [x] Alloy·Prometheus 파이프라인에서 **적합한 방식(dcgm-exporter)** 및 **채택 사유** 기술  
- [x] **필요 메트릭 목록표** 작성 (실제 메트릭명은 구축 후 보강)

---

## 참고

- [NVIDIA DCGM](https://developer.nvidia.com/dcgm)
- [dcgm-exporter (GitHub)](https://github.com/NVIDIA/dcgm-exporter)
