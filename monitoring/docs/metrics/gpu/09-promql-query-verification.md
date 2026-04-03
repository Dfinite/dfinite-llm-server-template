# 9. GPU 메트릭 PromQL 조회 검증

작성된 PromQL이 실제 GPU 상태를 정상적으로 반영하는지 Prometheus UI에서 검증합니다. [08](./08-gpu-metrics-promql.md)에서 작성한 쿼리를 실행하고, `nvidia-smi` 출력과 대조하여 값이 일치하는지 확인합니다.

> 선행: [07 — Prometheus](./07-prometheus-setup.md) 기동·GPU 시계열 적재, [08 — PromQL](./08-gpu-metrics-promql.md).

| 구분 | 담당 |
|------|------|
| **검증 UI** | Prometheus — **Graph** (`http://<호스트>:9090/graph`, [07](./07-prometheus-setup.md)) |
| **쿼리** | [08](./08-gpu-metrics-promql.md)에서 정리한 PromQL |

---

## 목표

- [x] Prometheus UI에서 PromQL 쿼리 실행
- [x] GPU별 값 확인
- [x] nvidia-smi 결과와 비교 검증
- [x] 메트릭 값 단위 확인

---

## 9.1 Prometheus UI에서 쿼리 실행

브라우저에서 `http://<호스트>:9090/graph`에 접속하여, 아래 PromQL을 각각 실행합니다.

| 패널 | PromQL |
|------|--------|
| Utilization | `DCGM_FI_DEV_GPU_UTIL{job="dcgm-exporter"}` |
| Temperature | `DCGM_FI_DEV_GPU_TEMP` |
| Memory (used) | `DCGM_FI_DEV_FB_USED` |
| Power | `DCGM_FI_DEV_POWER_USAGE` |

> Table 탭에서 현재 값, Graph 탭에서 시계열 추이를 확인할 수 있습니다.

### 실행 결과 캡처

| 메트릭 | 캡처 |
|--------|------|
| GPU Utilization | [스크린샷](../../../src/04-promql-gpu-util.png) |
| GPU Temperature | [스크린샷](../../../src/05-promql-gpu-temp.png) |
| GPU Memory Used | [스크린샷](../../../src/06-promql-gpu-memory.png) |
| GPU Power | [스크린샷](../../../src/07-promql-gpu-power.png) |

---

## 9.2 GPU별 값 확인

쿼리 결과에서 `gpu` 라벨로 각 GPU가 개별 행으로 나오는지 확인합니다.

```promql
DCGM_FI_DEV_GPU_UTIL{job="dcgm-exporter"}
```

| 확인 항목 | 기대 | 실측 |
|-----------|------|------|
| 행 수 | 서버에 장착된 GPU 수만큼 | 2 (Result series: 2) |
| `gpu` 라벨 | `"0"`, `"1"`, … 순서대로 | `gpu="0"`, `gpu="1"` |
| `modelName` 라벨 | 실제 GPU 모델명 | `NVIDIA L40S` |

---

## 9.3 nvidia-smi 결과와 비교

동일 시점에 `nvidia-smi`를 실행하여, Prometheus 쿼리 결과와 값이 대략 일치하는지 대조합니다.

```bash
nvidia-smi --query-gpu=index,utilization.gpu,temperature.gpu,memory.used,power.draw \
  --format=csv,noheader,nounits
```

| nvidia-smi 필드 | PromQL 메트릭 | 단위 |
|-----------------|---------------|------|
| `utilization.gpu` | `DCGM_FI_DEV_GPU_UTIL` | % |
| `temperature.gpu` | `DCGM_FI_DEV_GPU_TEMP` | °C |
| `memory.used` | `DCGM_FI_DEV_FB_USED` | MiB |
| `power.draw` | `DCGM_FI_DEV_POWER_USAGE` | W |

> DCGM과 nvidia-smi의 폴링 주기가 다르므로 값이 정확히 같지 않을 수 있습니다. 오차 범위 내에서 방향이 일치하면 정상입니다.

### 비교 결과 (2026-03-24 00:34 기준)

nvidia-smi 캡처: [스크린샷](../../../src/08-nvidia-smi-comparison.png)

| 메트릭 | GPU 0 (nvidia-smi) | GPU 0 (Prometheus) | GPU 1 (nvidia-smi) | GPU 1 (Prometheus) | 일치 |
|--------|--------------------|--------------------|--------------------|--------------------|------|
| Utilization | 0% | 0 | 0% | 0 | ✅ |
| Temperature | 59°C | ~59 | 51°C | ~51 | ✅ |
| Memory Used | 39393 MiB | ~39k | 39393 MiB | ~39k | ✅ |
| Power | 123W | ~123 | 109W | ~109 | ✅ |

---

## 9.4 메트릭 값 단위 확인

| 메트릭 | 기대 단위 | 실측 | 판정 |
|--------|-----------|------|------|
| `DCGM_FI_DEV_GPU_UTIL` | % (0–100) | 0 (idle 상태에서 0) | ✅ |
| `DCGM_FI_DEV_GPU_TEMP` | °C | 51, 59 (nvidia-smi와 일치) | ✅ |
| `DCGM_FI_DEV_FB_USED` | MiB | ~39393 (nvidia-smi와 일치) | ✅ |
| `DCGM_FI_DEV_POWER_USAGE` | W | ~109, ~123 (nvidia-smi와 일치) | ✅ |

---

## 9.5 완료 조건

| 완료 조건 | 작성할 내용 | 상태 |
|-----------|-------------|------|
| 각 PromQL 실행 결과 확인 | PromQL 결과 캡처 | ✅ [9.1 캡처](#91-prometheus-ui에서-쿼리-실행) |
| nvidia-smi 결과와 비교 검증 완료 | nvidia-smi 비교 표 | ✅ [9.3 비교 결과](#93-nvidia-smi-결과와-비교) |

---

## 참고

- 문서 [06 (Alloy — dcgm-exporter 연동)](./06-alloy-dcgm-exporter.md)
- 문서 [07 (Prometheus 구축)](./07-prometheus-setup.md)
- 문서 [08 (PromQL 작성)](./08-gpu-metrics-promql.md)
- [Prometheus querying basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
