<!-- 이 파일은 scripts/build_promql_doc.py가 promql/queries.json에서 생성합니다. -->
<!-- 수정: promql/queries.json 편집 후 `make promql-doc` -->

# 8. GPU 메트릭 PromQL 작성

dcgm-exporter가 노출하는 메트릭을 대상으로, Prometheus에서 사용할 **PromQL** 예시를 정리합니다.

**PromQL**은 시계열을 수집·저장하지 않고, Prometheus에 이미 들어온 데이터를 **질의**할 때 쓰는 언어입니다 (수집·저장은 06·07번).

| 구분 | 담당 |
|------|------|
| **노출** | dcgm-exporter — 메트릭 이름·본문은 [04](./04-dcgm-exporter-metrics-exposure.md) |
| **수집** | **Alloy** — [06](./06-alloy-dcgm-exporter.md) |
| **저장·조회** | **Prometheus** — TSDB 저장 후 Graph/Explore에서 **PromQL**로 조회 ([07](./07-prometheus-setup.md)) |

## 목표

- [x] 주요 GPU 메트릭명 확정
- [x] 패널별 PromQL 작성
- [x] GPU별 라벨 필터링 방법 정리
- [x] Prometheus Graph에서 동작 확인

> 메트릭명은 [04](./04-dcgm-exporter-metrics-exposure.md)에서 실측 확인한 이름 기준. 커스텀 counter CSV를 쓰면 이름이 달라질 수 있으므로 `/metrics`에서 재확인.

---

## 8.1 메트릭명 (기본 프로파일)

dcgm-exporter 기본 설정(`default-counters.csv`)에서 사용하는 필드입니다.

| 목적 | DCGM 필드 / Prometheus 메트릭 (일반적) | 단위·비고 |
|------|------------------------------------------|-----------|
| GPU 사용률 | `DCGM_FI_DEV_GPU_UTIL` | % |
| GPU 온도 | `DCGM_FI_DEV_GPU_TEMP` | °C |
| VRAM 사용량 | `DCGM_FI_DEV_FB_USED` | MiB |
| 전력 | `DCGM_FI_DEV_POWER_USAGE` | W |

> exporter 버전·`default-counters.csv` 변경에 따라 일부가 비활성일 수 있음. `/metrics`에서 `DCGM_FI_DEV` 로 검색하여 확인.

---

## 8.2 GPU별 라벨

dcgm-exporter는 아래 라벨로 GPU를 구분합니다 (버전에 따라 추가·이름 차이 가능).

| 라벨 | 의미 |
|------|------|
| `gpu` | GPU 인덱스 (문자열 `"0"`, `"1"` …) |
| `UUID` | GPU UUID |
| `device` | 노출되는 경우 디바이스 식별자 |
| `modelName, Hostname 등` | 환경·템플릿에 따라 존재 |

**한 GPU만 보기**

```promql
DCGM_FI_DEV_GPU_UTIL{gpu="0"}
```

**UUID로 고정**

```promql
DCGM_FI_DEV_GPU_UTIL{UUID="GPU-xxxx"}
```

**호스트·모델로 좁히기 (라벨이 있을 때)**

```promql
DCGM_FI_DEV_GPU_UTIL{modelName=~".*L40S.*"}
```

---

## 8.3 PromQL 예시

### GPU utilization (%)

```promql
DCGM_FI_DEV_GPU_UTIL
```

특정 인스턴스만 (Prometheus가 붙인 `job`, `instance` 등)

```promql
DCGM_FI_DEV_GPU_UTIL{job="dcgm-exporter"}
```

### GPU temperature (°C)

```promql
DCGM_FI_DEV_GPU_TEMP
```

### GPU memory used (MiB)

```promql
DCGM_FI_DEV_FB_USED
```

**사용률(%)** — 직접 필드가 없으면 사용량·여유로 계산 (둘 다 MiB일 때). 분모 0 등은 환경에 따라 `clamp_min` 등으로 보정 가능.

```promql
100 * DCGM_FI_DEV_FB_USED / (DCGM_FI_DEV_FB_USED + DCGM_FI_DEV_FB_FREE)
```

### GPU power (W)

```promql
DCGM_FI_DEV_POWER_USAGE
```

---

## 8.4 패널별 확정 PromQL

| 패널 | PromQL |
|------|--------|
| Utilization | `DCGM_FI_DEV_GPU_UTIL` |
| Temperature | `DCGM_FI_DEV_GPU_TEMP` |
| Memory (used) | `DCGM_FI_DEV_FB_USED` |
| Power | `DCGM_FI_DEV_POWER_USAGE` |

> Grafana 대시보드 JSON: [`grafana/dashboards/gpu-overview.json`](../../../grafana/dashboards/gpu-overview.json)

---

## 참고

- [dcgm-exporter default-counters.csv](https://github.com/NVIDIA/dcgm-exporter/blob/main/etc/default-counters.csv)
- [문서 06 (Alloy — dcgm-exporter)](./06-alloy-dcgm-exporter.md)
- [문서 07 (Prometheus)](./07-prometheus-setup.md)
