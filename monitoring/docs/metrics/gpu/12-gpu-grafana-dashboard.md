# 12. GPU 대시보드 패널 구성

GPU 주요 메트릭을 Grafana 패널로 구성합니다. [11](./11-grafana-prometheus-datasource.md)에서 **Prometheus** 데이터 소스 연결이 확인된 상태에서 진행합니다.

---

## 목표

- [x] GPU Utilization 패널 생성
- [x] GPU Temperature 패널 생성
- [x] GPU Memory Used 패널 생성
- [x] GPU Power Usage 패널 생성
- [x] GPU별 시계열 패널 구성
- [x] 패널 제목·단위·범례 정리

---

## 12.1 대시보드 로드

본 레포는 provisioning으로 대시보드가 자동 로드됩니다.

| 항목 | 값 |
|------|-----|
| Provider | [`grafana/provisioning/dashboards/default.yaml`](../../../grafana/provisioning/dashboards/default.yaml) |
| 대시보드 JSON | [`grafana/dashboards/gpu-overview.json`](../../../grafana/dashboards/gpu-overview.json) |
| 대시보드 이름 | GPU Overview (dcgm-exporter) |
| UID | `gpu-overview` |

Grafana UI: **Dashboards** → **GPU Overview (dcgm-exporter)** 선택.

---

## 12.2 패널 구성

### GPU Utilization

| 항목 | 값 |
|------|-----|
| PromQL | `DCGM_FI_DEV_GPU_UTIL` |
| 단위 | percent (0–100) |
| 범례 | `{{gpu}}` |
| 타입 | timeseries |

### GPU Temperature

| 항목 | 값 |
|------|-----|
| PromQL | `DCGM_FI_DEV_GPU_TEMP` |
| 단위 | celsius |
| 범례 | `{{gpu}}` |
| 타입 | timeseries |

### GPU Memory Used

| 항목 | 값 |
|------|-----|
| PromQL | `DCGM_FI_DEV_FB_USED` |
| 단위 | mbytes (Grafana 표시: GiB) |
| 범례 | `{{gpu}}` |
| 타입 | timeseries |

### GPU Power Usage

| 항목 | 값 |
|------|-----|
| PromQL | `DCGM_FI_DEV_POWER_USAGE` |
| 단위 | watt |
| 범례 | `{{gpu}}` |
| 타입 | timeseries |

---

## 12.3 GPU별 시계열 확인

각 패널에서 `gpu` 라벨(`"0"`, `"1"`, …)별로 개별 시계열이 표시되는지 확인합니다.

| 확인 항목 | 기대 | 실측 |
|-----------|------|------|
| 시계열 수 | GPU 수만큼 (2개) | ✅ 2개 |
| 범례 구분 | `gpu` 인덱스별 색상 구분 | ✅ `0`, `1` 표시 |
| 시계열 그래프 | 시간에 따른 추이 표시 | ✅ |
| 현재값 | 마우스 오버 시 tooltip에 현재값 표시 | ✅ |
| auto-refresh | 10s 간격 자동 새로고침 | ✅ |

---

## 12.4 JSON 수정 후 재생성

```bash
make grafana-dashboard
# 또는
python3 scripts/build_grafana_gpu_dashboard.py
```

변경 반영 시 `docker compose restart grafana`로 provisioning을 재로드합니다.

---

## 12.5 완료 조건

| 완료 조건 | 작성할 내용 | 상태 |
|-----------|-------------|------|
| GPU별 그래프 표시, 패널 표시 확인 | Grafana 대시보드 확인 | ✅ [12.2 참조](#122-패널-구성) |
| 시계열 그래프와 현재값 확인 가능 | 패널별 PromQL 정리 | ✅ [12.2 참조](#122-패널-구성) |

---

## 참고

| 문서 | 내용 |
|------|------|
| [GPU-08 — GPU PromQL](./08-gpu-metrics-promql.md) | PromQL 쿼리 작성 |
| [GPU-11 — Grafana Prometheus 데이터소스](./11-grafana-prometheus-datasource.md) | Prometheus 데이터소스 설정 |
